# Use official PyTorch base with CUDA
FROM pytorch/pytorch:2.2.2-cuda11.8-cudnn8-runtime

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git libgl1-mesa-glx libglib2.0-0

# Copy app code
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn transformers accelerate bitsandbytes pandas PyMuPDF openpyxl

# Preload model to cache (avoid cold start delay)
RUN python -c "from transformers import pipeline; pipeline('text2text-generation', model='google/gemma-1.1-7b-it')"

# Expose API port
EXPOSE 10000

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
