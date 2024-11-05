# model_setup.py

import os
import subprocess
from tqdm import tqdm 
from pathlib import Path
import requests

# Helper function to check if a package is installed
def is_package_installed(package_name):
    try:
        subprocess.run(["pip", "show", package_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError:
        return False

def download_model(model_url, model_path):
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    if not os.path.exists(model_path):
        print("Model not found. Downloading inswapper_128.onnx...")
        response = requests.get(model_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        with open(model_path, "wb") as file, tqdm(
            desc="Downloading model",
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
                    bar.update(len(chunk))
        print("Model downloaded successfully.")
    else:
        print("Model is already downloaded.")

def check_repository_exists(repo_url):
    """Check if a Git repository exists by running a `git ls-remote` command."""
    try:
        subprocess.run(["git", "ls-remote", repo_url], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Repository {repo_url} exists.")
        return True
    except subprocess.CalledProcessError:
        print(f"Repository {repo_url} does not exist or is inaccessible.")
        return False  
    
def setup_environment():
    repo_url = "https://github.com/s0md3v/roop.git"
    repo_dir = Path("./roop")

    # Check if the repository directory already exists
    if repo_dir.exists() and repo_dir.is_dir():
        print(f"The repository 'roop' already exists. Skipping download.")
        os.chdir("roop")  # Change into the repo directory
    else:
        # Check if the repository exists online before attempting to clone
        if not check_repository_exists(repo_url):
            print(f"Cannot proceed, the repository {repo_url} is not accessible.")
            return
        
    MODEL_PATH = "models/inswapper_128.onnx"
    print(os.getcwd())
    # Install requirements
    subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True)
    # Check if the model has already been downloaded
    download_model("https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx", MODEL_PATH)
    os.makedirs("models", exist_ok=True)

    # Check if onnxruntime-gpu is installed
    if is_package_installed("onnxruntime-gpu"):
        print("onnxruntime-gpu is already installed.")
    else:
        print("Installing onnxruntime-gpu...")
        with tqdm(total=100, desc="Installing onnxruntime-gpu") as pbar:
            subprocess.run(["pip", "install", "onnxruntime-gpu"])
            pbar.update(100)

    # Check if torch, torchvision, and torchaudio are installed
    if is_package_installed("torch") and is_package_installed("torchvision") and is_package_installed("torchaudio"):
        print("Torch packages are already installed.")
    else:
        print("Installing torch, torchvision, and torchaudio...")
        with tqdm(total=100, desc="Installing PyTorch") as pbar:
            subprocess.run(["pip", "uninstall", "onnxruntime", "onnxruntime-gpu", "-y"])
            subprocess.run(["pip", "install", "torch", "torchvision", "torchaudio", "--force-reinstall", "--index-url", "https://download.pytorch.org/whl/cu118"])
            pbar.update(100)       

def main():
    """Main function to run the setup process."""
    print("Starting the environment setup for Roop...")
    try:
        setup_environment()
        print("Setup completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred during setup: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()