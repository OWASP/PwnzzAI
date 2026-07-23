FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential \
    libzbar0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install \
    --retries 10 \
    --timeout 600 \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.7.1 && \
    pip install \
    --retries 10 \
    --timeout 600 \
    -r requirements.txt

COPY . .

RUN mkdir -p uploads downloads instance

# Expose Flask port
EXPOSE 8080

ENV FLASK_APP=main.py
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_HOST=http://ollama:11434

# Ollama runs in its own Compose service or at OLLAMA_HOST.
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080", "--no-reload"]
