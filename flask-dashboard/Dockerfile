FROM python:3.11-slim

WORKDIR /app

# Copia requirements e installa dipendenze
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copia tutto il codice sorgente
COPY . .

CMD ["python", "run.py"]
