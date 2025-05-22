FROM python:3.11-slim

WORKDIR /app

# Copia i file di configurazione
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia lo script principale
COPY serial-to-kafka-linux.py .

# Comando di avvio
CMD ["python", "serial-to-kafka-linux.py"]
