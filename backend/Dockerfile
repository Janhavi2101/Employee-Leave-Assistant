# Use official PyTorch base with CUDA
FROM pytorch/pytorch:2.2.2-cuda11.8-cudnn8-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y git libgl1-mesa-glx libglib2.0-0

COPY . /app

# 👇 Pass HF_TOKEN from Render env into Hugging Face auth
ENV HUGGINGFACE_HUB_TOKEN=$HF_TOKEN1

RUN pip install --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn transformers accelerate bitsandbytes pandas PyMuPDF openpyxl

RUN python -c "from transformers import pipeline; pipeline('text-generation', model='google/gemma-1.1-7b-it')"

EXPOSE 10000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
