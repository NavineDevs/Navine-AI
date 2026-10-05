# Kubernetes skeleton (Phase 2). Placeholder only — not a full multi-region deploy.
# Apply after building images from deploy/docker.
apiVersion: v1
kind: Namespace
metadata:
  name: navine
---
# See ARCHITECTURE.md for Phase 1 docker compose. Helm charts TBD.
