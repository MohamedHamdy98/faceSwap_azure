# Use Python 3.8 as the base image
FROM python:3.8-slim

# Set environment variable to avoid interactive prompts during package installations
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt ./requirements.txt

# Install system dependencies (ffmpeg, build tools, etc.) and clean up to reduce image size
RUN apt update && \
    apt install --no-install-recommends -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libomp-dev \
    git && \
    apt clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install Python dependencies (including insightface and other packages)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the application port (5000 as per your example)
EXPOSE 5000

# Set environment variables (Optional)
ENV PORT=5000

# Run the FastAPI app using Gunicorn with a timeout (adjust for your application)
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5000", "--timeout", "600", "app:app"]
