from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import cv2  # OpenCV for video processing
import subprocess
from fastapi.middleware.cors import CORSMiddleware
from tqdm import tqdm  
import uvicorn
from PIL import Image
from pathlib import Path

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FaceSwapRequest(BaseModel):
    output_filename: Optional[str] = "output_face_swap.mp4"

def convert_to_jpg(image_path: str) -> str:
    img = Image.open(image_path)
    if img.format != 'JPEG':
        output_jpg_path = Path(image_path).with_suffix('.jpg')
        rgb_img = img.convert("RGB")
        rgb_img.save(output_jpg_path, format="JPEG")
        return str(output_jpg_path)
    return image_path

def trim_video(input_path: str, output_path: str, max_duration: int = 10) -> str:
    """Trims the video to a maximum of max_duration seconds using OpenCV."""
    cap = cv2.VideoCapture(input_path)
    
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Error opening video file.")
    
    fps = cap.get(cv2.CAP_PROP_FPS)  # Get the frames per second
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))  # Get total number of frames
    duration = total_frames / fps  # Calculate duration in seconds

    if duration > max_duration:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Define the codec
        out = cv2.VideoWriter(output_path, fourcc, fps, (int(cap.get(3)), int(cap.get(4))))  # Output video writer
        
        for _ in range(int(fps * max_duration)):  # Loop for max_duration seconds
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)  # Write frame to output video
        
        out.release()  # Release the output writer
        cap.release()  # Release the video capture
        return output_path
    
    cap.release()  # Release the video capture if not trimmed
    return input_path

@app.post('/face_swap')
async def face_swap(
    target_video: UploadFile = File(...), 
    source_image: UploadFile = File(...),
    request: FaceSwapRequest = Depends()
):
    try:
        # Set up paths
        current_directory = Path(__file__).parent
        output_filename = request.output_filename
        output_path = current_directory / "faceSwap/outputs" / output_filename

        # Define paths to save the uploaded files
        target_path = current_directory / "faceSwap/videos" / target_video.filename
        source_path = current_directory / "faceSwap/images" / source_image.filename

        # Ensure directories exist
        for path in [target_path.parent, source_path.parent, output_path.parent]:
            os.makedirs(path, exist_ok=True)

        # Save uploaded video and image files
        with open(target_path, "wb") as f:
            f.write(await target_video.read())
        
        with open(source_path, "wb") as f:
            f.write(await source_image.read())

        # Trim the video if necessary
        trimmed_video_path = target_path
        if cv2.VideoCapture(str(target_path)).get(cv2.CAP_PROP_FRAME_COUNT) / cv2.VideoCapture(str(target_path)).get(cv2.CAP_PROP_FPS) > 10:
            trimmed_video_path = current_directory / "faceSwap/videos" / f"trimmed_{target_video.filename}"
            trim_video(str(target_path), str(trimmed_video_path))

        # Convert source image to JPG if needed
        source_path = convert_to_jpg(str(source_path))
        print('before run: ', os.getcwd())
        os.chdir('roop')
        # Prepare and run the face swapping command
        print('after run:', os.getcwd())
        command = f"python run.py --target {trimmed_video_path} --source {source_path} -o {output_path} --execution-provider cpu --frame-processor face_swapper"

        # Execute the face swapping command
        with tqdm(total=100, desc="Face swapping") as pbar:
            process = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            pbar.update(100)

        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Face swapping failed: {process.stderr.decode('utf-8')}")

        return JSONResponse(content={
            'status': 'success',
            'message': 'Face swapping completed',
            'video_input': str(trimmed_video_path),
            'image_input': source_path,
            'output_path': str(output_path)
        })

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/output/{filename}')
async def get_output_video(filename: str):
    file_path = Path(__file__).parent / "faceSwap/outputs" / filename
    if file_path.exists():
        return FileResponse(file_path, media_type='video/mp4', filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found")

@app.get('/')
async def index():
    return "Roop Face Swapping API is running!"

def main():
    uvicorn.run(app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    main()
