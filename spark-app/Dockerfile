FROM bitnami/spark:3.5.5-debian-12-r7

USER root

RUN install_packages python3-pip

COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

COPY app.py /app/app.py
WORKDIR /app

CMD ["spark-submit", "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1,org.apache.kafka:kafka-clients:3.5.1,mysql:mysql-connector-java:8.0.33", "app.py"]

