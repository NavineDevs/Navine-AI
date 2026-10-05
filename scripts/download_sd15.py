from huggingface_hub import snapshot_download

path = snapshot_download(
    "runwayml/stable-diffusion-v1-5",
    ignore_patterns=[
        "*.ckpt",
        "*.safetensors.md",
        "*.msgpack",
        "flax*",
        "onnx*",
        "*.onnx",
        "openvino*",
    ],
)
print(path)
