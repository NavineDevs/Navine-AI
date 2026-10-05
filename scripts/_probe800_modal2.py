from navine.video.model import NavineVideoModel
from navine.voice.neural import NavineVoiceModel
from navine.deepfake.model import build_deepfake_model
from navine.utils.param_verify import unique_trainable_params as u
from pathlib import Path
out=["image bc=384 798663181"]
for hd in (2352, 2368, 2400, 2432):
    m=NavineVideoModel(frame_size=160,num_frames=24,in_channels=3,hidden_dim=hd,num_layers=14)
    n=u(m); out.append(f"video hd={hd} {n}"); print(out[-1], flush=True); del m
for hd in (1392, 1408, 1424, 1440):
    m=NavineVoiceModel(vocab_size=256,hidden_dim=hd,num_layers=16,mel_bins=80,max_seq_len=512)
    n=u(m); out.append(f"voice hd={hd} {n}"); print(out[-1], flush=True); del m
for bc in (264, 272, 280):
    m=build_deepfake_model({"image_size":128,"in_channels":3,"base_channels":bc,"channel_mults":[1,2,4,4],"num_res_blocks":2,"latent_dim":1024,"arch_version":3})
    n=u(m); out.append(f"deepfake bc={bc} {n}"); print(out[-1], flush=True); del m
Path(r"C:\Users\hitbo\Downloads\Navine AI\logs\arch800_modal.txt").write_text("\n".join(out)+"\n", encoding="utf-8")
