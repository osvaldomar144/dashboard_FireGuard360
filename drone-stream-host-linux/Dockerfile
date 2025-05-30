FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Crea directory di configurazione per Ultralytics per evitare warning
RUN mkdir -p /root/.config/Ultralytics && chmod -R 777 /root/.config

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application, model and video
COPY drone_stream_server.py .
COPY best.pt .
COPY fire.mp4 .

# Default to simulation mode unless overridden
ENV USE_SIMULATION=false

CMD ["python", "drone_stream_server.py"]
