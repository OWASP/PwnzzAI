FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    libzbar0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade --no-cache-dir pip && \
    pip install --no-cache-dir \
    --retries 10 \
    --timeout 600 \
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
