FROM bitnami/spark:3.5.5-debian-12-r7

USER root

# Installa pip e dipendenze Python
RUN install_packages python3-pip

# Copia il file requirements e installa librerie
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copia lo script Python e il file .env
COPY app.py /app/app.py
COPY CONFIG_FIREGUARD360.env /app/CONFIG_FIREGUARD360.env

# Imposta directory di lavoro
WORKDIR /app

# Avvia lo script con Spark e i connettori necessari
CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.apache.kafka:kafka-clients:3.5.1,mysql:mysql-connector-java:8.0.33", "app.py"]

