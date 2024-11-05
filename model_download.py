import os
import subprocess
from tqdm import tqdm 
from pathlib import Path
import requests

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

def setup_environment():
    os.chdir("roop/roop") 
    print(os.getcwd())
    MODEL_PATH = "models/inswapper_128.onnx"
    # Check if the model has already been downloaded
    download_model("https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx", MODEL_PATH)
    os.makedirs("models", exist_ok=True)

    # Original path
    current_path = Path(os.getcwd())

    # Get the parent directory of the current path and navigate up one level
    new_path = current_path.parent.parent / current_path.name

    # Convert Path object to string for os.chdir()
    new_path_str = str(new_path)

    # Change the working directory
    os.chdir(new_path.parent)  # This sets the working directory to the folder containing 'run.py'

    # Verify the change
    print("Current working directory:", os.getcwd()) 

setup_environment()