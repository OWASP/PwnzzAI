FROM python:3.11-slim

WORKDIR /app

# libzbar0: runtime for pyzbar (QR labs). Wheels cover numpy/sklearn/Pillow/faiss; no compiler.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# CPU torch first so sentence-transformers does not pull the CUDA wheel (~GB of nvidia-*).
# Do not pin torch in requirements.txt: host/macOS venvs stay unchanged.
RUN python -m pip install --upgrade --no-cache-dir pip && \
    pip install --no-cache-dir --retries 10 --timeout 600 \
      torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --retries 10 --timeout 600 \
      -r requirements.txt

COPY . .

RUN mkdir -p uploads downloads instance

# Expose Flask port
EXPOSE 8080

ENV FLASK_APP=main.py
ENV PYTHONUNBUFFERED=1
# Compose DNS to the separate ollama service (not installed in this image).
ENV OLLAMA_HOST=http://ollama:11434

# Flask only. Ollama runs as compose service ollama/ollama:latest.
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080", "--no-reload"]
