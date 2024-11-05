# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the environment variable to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Install system packages (like ffmpeg) and clean up to reduce image size
RUN apt update && \
    apt install --no-install-recommends -y ffmpeg && \
    apt clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container
COPY . .

# Expose port 8000 for the application
EXPOSE 5000

# Set environment variables (Optional, no spaces around `=`)
ENV PORT=5000

# Run the FastAPI app using Gunicorn with a timeout
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5000", "--timeout", "600", "app:app"]