import serial
import time
import json
import os
from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

SERIAL_PORT = os.getenv("SERIAL_PORT", "COM5")
BAUD_RATE = int(os.getenv("BAUD_RATE", "9600"))
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9093")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sensordata")


def connetti_kafka():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode("utf-8")
            )
            print("[INFO] Connesso a Kafka.")
            return producer
        except NoBrokersAvailable:
            print("[WARN] Kafka non disponibile, nuovo tentativo in 5s...")
            time.sleep(5)


def connetti_seriale():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
            print(f"[INFO] Connesso alla porta seriale {SERIAL_PORT}.")
            return ser
        except serial.SerialException:
            print(f"[WARN] Porta seriale {SERIAL_PORT} non disponibile, nuovo tentativo in 5s...")
            time.sleep(5)


# Connessioni iniziali
producer = connetti_kafka()
ser = connetti_seriale()

# Lettura continua con gestione disconnessioni
while True:
    try:
        line = ser.readline().decode("utf-8").strip()
        if line:
            try:
                data = json.loads(line)
                try:
                    producer.send(KAFKA_TOPIC, value=data)
                    print(f"[Kafka] Inviato: {data}")
                except KafkaError as ke:
                    print(f"[ERRORE Kafka] {ke}, riconnessione...")
                    producer = connetti_kafka()
            except json.JSONDecodeError:
                print(f"[ERRORE JSON] Linea non valida: {line}")
    except serial.SerialException as se:
        print(f"[ERRORE Serial] {se}, riconnessione...")
        ser = connetti_seriale()
    except Exception as e:
        print(f"[ERRORE Generico] {e}")
        time.sleep(2)
