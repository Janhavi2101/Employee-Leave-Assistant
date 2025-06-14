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
    pip install --no-cache-dir fastapi uvicorn transformers accelerate bitsandbytes pandas PyMuPDF openpyxl huggingface_hub

# Set HF token and model cache path
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}
ENV TRANSFORMERS_CACHE=/app/.cache

# Download model using huggingface_hub with token
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='google/gemma-1.1-7b-it', token='${HF_TOKEN}')"

# Expose API port
EXPOSE 10000

# Run the FastAPI app using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
