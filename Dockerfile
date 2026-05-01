FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Build deps for prophet/lightgbm
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential libgomp1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 7860

RUN chmod +x start.sh

# Default command: run the startup script.
CMD ["./start.sh"]
