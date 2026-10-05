from navine.text.model import build_text_model
from navine.utils.param_verify import unique_trainable_params as u
rows=[]
for d,L,ff in [(1632,24,6528),(1632,24,6656),(1632,24,6784),(1632,25,6528),(1664,24,6400),(1664,24,6528),(1600,25,6528),(1600,26,6400)]:
    assert d%16==0 and (d//16)%2==0, (d,d//16)
    m=build_text_model(dict(vocab_size=12000,d_model=d,n_heads=16,n_layers=L,d_ff=ff,max_seq_len=2048,dropout=0.08,use_rope=True,use_kv_cache=True,use_swiglu=True,use_rms_norm=True,tie_embeddings=True),12000)
    n=u(m); print(d,L,ff,n,'head',d//16); rows.append((abs(n-800000000),n,d,L,ff)); del m
print('BEST', sorted(rows)[0])
