package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"sync"
	"time"
)

type rateLimiter struct {
	mu       sync.Mutex
	tokens   map[string]float64
	last     map[string]time.Time
	rate     float64
	burst    float64
}

func newRateLimiter(rate, burst float64) *rateLimiter {
	return &rateLimiter{
		tokens: make(map[string]float64),
		last:   make(map[string]time.Time),
		rate:   rate,
		burst:  burst,
	}
}

func (r *rateLimiter) allow(key string) bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	now := time.Now()
	tok := r.tokens[key]
	last, ok := r.last[key]
	if !ok {
		tok = r.burst
		last = now
	}
	elapsed := now.Sub(last).Seconds()
	tok += elapsed * r.rate
	if tok > r.burst {
		tok = r.burst
	}
	if tok < 1.0 {
		r.tokens[key] = tok
		r.last[key] = now
		return false
	}
	tok -= 1.0
	r.tokens[key] = tok
	r.last[key] = now
	return true
}

func main() {
	listen := flag.String("listen", ":8080", "gateway listen address")
	upstream := flag.String("upstream", "http://127.0.0.1:8765", "Python FastAPI upstream")
	rate := flag.Float64("rate", 30, "requests per second per client")
	burst := flag.Float64("burst", 60, "burst capacity per client")
	flag.Parse()

	target, err := url.Parse(*upstream)
	if err != nil {
		log.Fatalf("invalid upstream: %v", err)
	}
	proxy := httputil.NewSingleHostReverseProxy(target)
	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalDirector(req)
		req.Host = target.Host
		req.Header.Set("X-Gateway", "nav-gateway")
	}
	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, e error) {
		log.Printf("proxy error path=%s err=%v", r.URL.Path, e)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadGateway)
		_ = json.NewEncoder(w).Encode(map[string]any{
			"error":    "upstream_unavailable",
			"detail":   e.Error(),
			"upstream": *upstream,
		})
	}

	limiter := newRateLimiter(*rate, *burst)
	mux := http.NewServeMux()
	mux.HandleFunc("/gateway/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
		defer cancel()
		req, _ := http.NewRequestWithContext(ctx, http.MethodGet, *upstream+"/health", nil)
		resp, err := http.DefaultClient.Do(req)
		upstreamOK := false
		upstreamBody := ""
		if err == nil {
			defer resp.Body.Close()
			b, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
			upstreamBody = string(b)
			upstreamOK = resp.StatusCode >= 200 && resp.StatusCode < 500
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"gateway":     "ok",
			"upstream":    *upstream,
			"upstream_ok": upstreamOK,
			"upstream_body": upstreamBody,
			"time":        time.Now().UTC().Format(time.RFC3339),
		})
	})

	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		client := r.RemoteAddr
		if xf := r.Header.Get("X-Forwarded-For"); xf != "" {
			client = xf
		}
		if !limiter.allow(client) {
			w.Header().Set("Content-Type", "application/json")
			w.WriteHeader(http.StatusTooManyRequests)
			_ = json.NewEncoder(w).Encode(map[string]string{"error": "rate_limited"})
			return
		}
		id := fmt.Sprintf("%d", time.Now().UnixNano())
		w.Header().Set("X-Request-Id", id)
		r.Header.Set("X-Request-Id", id)
		proxy.ServeHTTP(w, r)
	})

	srv := &http.Server{
		Addr:              *listen,
		Handler:           mux,
		ReadHeaderTimeout: 10 * time.Second,
	}
	log.Printf("nav-gateway listen=%s upstream=%s rate=%.1f/s burst=%.0f", *listen, *upstream, *rate, *burst)
	if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Println(err)
		os.Exit(1)
	}
}
