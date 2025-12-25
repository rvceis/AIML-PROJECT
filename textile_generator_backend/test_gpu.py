import torch

print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"CUDA Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")
print(f"PyTorch Version: {torch.__version__}")
print(f"Device Count: {torch.cuda.device_count() if torch.cuda.is_available() else 0}")

if torch.cuda.is_available():
    print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")