from navine.text.model import build_text_model
from navine.utils.param_verify import unique_trainable_params as u
from pathlib import Path
out = Path(r"C:\Users\hitbo\Downloads\Navine AI\logs\arch800.txt")
rows = []
for d,L,ff in [(1632,24,6528),(1648,24,6592),(1664,24,6656),(1600,25,6400)]:
    m = build_text_model(dict(vocab_size=12000,d_model=d,n_heads=16,n_layers=L,d_ff=ff,max_seq_len=2048,dropout=0.08,use_rope=True,use_kv_cache=True,use_swiglu=True,use_rms_norm=True,tie_embeddings=True),12000)
    n = u(m)
    line = f"{d} {L} {ff} {n}"
    rows.append(line)
    out.write_text("\n".join(rows)+"\n", encoding="utf-8")
    print(line, flush=True)
    del m
best = min(((abs(int(r.split()[-1])-800000000), r) for r in rows))[1]
out.write_text("\n".join(rows)+f"\nBEST {best}\n", encoding="utf-8")
print("BEST", best, flush=True)
