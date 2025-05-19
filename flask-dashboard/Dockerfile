FROM python:3.11-slim

WORKDIR /app

# Copia requirements e installa dipendenze
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copia codice dell'app e il file di configurazione .env
COPY app/ .
COPY run.py .
COPY CONFIG_FIREGUARD360.env .

CMD ["python", "run.py"]
