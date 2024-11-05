from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import os
import subprocess
import gdown
from fastapi.middleware.cors import CORSMiddleware
from tqdm import tqdm  
import uvicorn
from roop.roop.model_download import setup_environment
from PIL import Image
from pathlib import Path
from typing import Optional

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_environment()

class FaceSwapRequest(BaseModel):
    target_url: Optional[str] = None
    source_url: Optional[str] = None
    
async def form_or_json(target_url: Optional[str] = Form(None), source_url: Optional[str] = Form(None), request: FaceSwapRequest = Depends()):
    # Check if form data is provided, otherwise fall back to JSON
    if not target_url or not source_url:
        target_url = request.target_url
        source_url = request.source_url

    if not target_url or not source_url:
        raise HTTPException(status_code=422, detail="Both target_url and source_url are required")

    return target_url, source_url

# Helper function to download a file from Google Drive
"""def download_from_google_drive(url: str, output_path: str):
    try:
        # Extract the file ID from the Google Drive URL
        file_id = url.split("/d/")[1].split("/view")[0]
        download_url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(download_url, output_path, quiet=False)
        print(f"File downloaded successfully to {output_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download file from {url}. Error: {str(e)}")"""

def convert_to_jpg(image_path):
    # Open the image to check its format and convert if necessary
    img = Image.open(image_path)
    original_format = img.format
    original_extension = Path(image_path).suffix
    print(f"Original image format: {original_format}")
    
    if img.format != 'JPEG':
        # Define the new path with a .jpg extension
        output_jpg_path = Path(image_path).with_suffix('.jpg')
        rgb_img = img.convert("RGB")  # Convert to RGB for JPG format
        rgb_img.save(output_jpg_path, format="JPEG")
        print(f"Image converted to JPG and saved as: {output_jpg_path}")
        print(f"New file extension: {output_jpg_path.suffix}")
    else:
        print(f"Image is already in JPG format: {image_path}")
        print(f"File extension remains: {original_extension}")

def download_from_google_drive(url: str, output_path: str):
    """
    Downloads a file from Google Drive using its URL and saves it to the specified output path.

    Args:
        url (str): Google Drive URL of the file to be downloaded.
        output_path (str): Local path where the downloaded file will be saved.
    """
    try:
        # Extract the file ID from the Google Drive URL
        file_id = url.split("/d/")[1].split("/view")[0]
        download_url = f"https://drive.google.com/uc?id={file_id}"
        
        # Download the file to the specified path
        gdown.download(download_url, output_path, quiet=False)
        print(f"File downloaded successfully to {output_path}")
        
        # Convert the image to JPG if it's not already in that format
        convert_to_jpg(output_path)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to download file from {url}. Error: {str(e)}")
    

@app.post('/face_swap')
async def face_swap(data: tuple = Depends(form_or_json)):
    """
    Endpoint for performing face swapping using provided Google Drive links for the target video and source image.

    Expects form data with the following fields:
        - target_url (str): Google Drive link to the target video.
        - source_url (str): Google Drive link to the source image.

    Returns:
        JSON response with the status of the face swapping operation and the path to the output file.
    """
    try:
        # Directory for the Roop model and the face swapper
        # os.chdir("roop")  # Set to the directory where your Roop files are located

        # Retrieve URLs from the request
        target_url, source_url = data
        output_path = Path('/face_swap_data/outputs/output_face_swap.mp4')  # Default output path


        # Define paths to save the downloaded files
        target_path = Path("/face_swap_data/data_from_user/videos/target_video.mp4")
        source_path = Path("/face_swap_data/data_from_user/images/source_image.jpg")

        # Ensure directories exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Download the files from Google Drive with progress reporting
        print("Downloading target video...")
        download_from_google_drive(target_url, target_path)
        print("Downloading source image...")
        download_from_google_drive(source_url, source_path)

        # Prepare and run the face swapping command
        print("Performing face swapping...")
        os.chdir("roop")
        # os.chdir("H:\\avatar_veem\\Edit_Coding\\bf_docker\\FaceSwap\\roop")
        command = f"python run.py --target {target_path} --source {source_path} -o {output_path} --execution-provider cuda --frame-processor face_swapper"

        # Mock progress bar since subprocess is blocking
        with tqdm(total=100, desc="Face swapping") as pbar:
            process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pbar.update(100)

        # Check if subprocess ran successfully
        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Face swapping failed: {process.stderr.decode('utf-8')}")

        return JSONResponse(content={
            'status': 'success',
            'message': 'Face swapping completed',
            'video_input': str(target_path),
            'image_input': str(source_path),
            'output_path': str(output_path)
        })

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/get_path_face_swap')
async def get_path_face_swap():
    """
    Endpoint to retrieve the paths of the target video, source image, and the output file from the face swap operation.

    Returns:
        JSON response with the status and the paths to the video input, image input, and output file, if they exist.
    """
    try:
        # Define the paths for the target video, source image, and output file
        target_path = Path("/face_swap_data/data_from_user/videos/target_video.mp4")
        source_path = Path("/face_swap_data/data_from_user/images/source_image.jpg")
        output_path = Path('/face_swap_data/outputs/output_face_swap.mp4')

        # Check if the output file exists
        if output_path.exists():
            return JSONResponse(content={
                'status': 'success',
                'message': 'Output file path retrieved successfully',
                'video_input': str(target_path),
                'image_input': str(source_path),
                'output_path': str(output_path)
            })
        else:
            raise HTTPException(status_code=404, detail='Output file not found')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/')
async def index():
    """
    Test route to check if the API is running.

    Returns:
        A simple message indicating the API is operational.
    """
    return "Roop Face Swapping API is running!"

def main():
    # Run the FastAPI application with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
     main()
