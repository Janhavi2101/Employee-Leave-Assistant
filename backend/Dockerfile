# Use official PyTorch base image with CUDA support
FROM pytorch/pytorch:2.2.2-cuda11.8-cudnn8-runtime

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git libgl1-mesa-glx libglib2.0-0

# Install Python packages
RUN pip install --upgrade pip
RUN pip install fastapi uvicorn transformers accelerate bitsandbytes pandas PyMuPDF openpyxl huggingface_hub

# Copy project files
COPY . /app

# Accept Hugging Face token as build argument and login (do not hardcode the token)
ARG HF_TOKEN1
RUN echo "$HF_TOKEN1" | huggingface-cli login --token

# Expose the port
EXPOSE 10000

# Start the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
