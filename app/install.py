import os
import platform
import re
import subprocess
import sys


def get_nvidia_cuda_version():
    try:
        output = subprocess.check_output(["nvidia-smi"], stderr=subprocess.STDOUT)
        output_str = output.decode("utf-8", errors="ignore")

        match = re.search(r"CUDA Version:\s*(\d+\.\d+)", output_str)
        if match:
            return float(match.group(1))
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def get_pytorch_install_args(system):
    if system == "Darwin":
        print("Detected macOS: Configuring for Metal Performance Shaders (MPS)...")
        return ["torch", "torchvision"], None

    if system in ["Windows", "Linux"]:
        cuda_version = get_nvidia_cuda_version()

        if cuda_version:
            print(f"Detected NVIDIA GPU with CUDA support: v{cuda_version}")

            if cuda_version >= 12.6:
                index_url = "https://download.pytorch.org/whl/cu126"
            elif cuda_version >= 12.1:
                index_url = "https://download.pytorch.org/whl/cu121"
            elif cuda_version >= 11.8:
                index_url = "https://download.pytorch.org/whl/cu118"
            else:
                print("CUDA version is older than 11.8. Defaulting to CPU wheel.")
                index_url = "https://download.pytorch.org/whl/cpu"

            return ["torch", "torchvision"], index_url

        print("No active NVIDIA GPU detected. Defaulting to CPU-only PyTorch...")
        return ["torch", "torchvision"], "https://download.pytorch.org/whl/cpu"

    return ["torch", "torchvision"], None


def install_requirements():
    print("--- Step 1: Installing base dependencies ---")
    base_packages = [
        "customtkinter>=5.2.0",
        "Pillow>=10.0.0",
        "pillow-heif",
        "PyMuPDF",
        "cairosvg",
        "numpy>=1.24.0",
    ]
    subprocess.check_call([sys.executable, "-m", "pip", "install"] + base_packages)

    print("\n--- Step 2: Inspecting System Hardware & OS ---")
    system = platform.system()
    print(f"Platform: {system} ({platform.machine()})")

    packages, index_url = get_pytorch_install_args(system)

    print("\n--- Step 3: Installing PyTorch Stack ---")
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    if index_url:
        cmd.extend(["--index-url", index_url])

    print(f"Running command: {' '.join(cmd)}")
    subprocess.check_call(cmd)

    print("\n--- Step 4: Installing AI enhancement packages ---")
    try:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "basicsr",
                "realesrgan",
                "--no-build-isolation",
            ]
        )
    except Exception as e:
        print(f"Warning: Could not install optional AI upscaling packages: {e}")

    print("\nSetup process complete!")


if __name__ == "__main__":
    install_requirements()