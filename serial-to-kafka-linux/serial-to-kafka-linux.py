import serial
import json
import time
import os
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable, KafkaTimeoutError

# Configurazione da variabili d'ambiente (con default)
SERIAL_PORT = os.getenv("SERIAL_PORT", "/dev/ttyACM0")
BAUD_RATE = int(os.getenv("BAUD_RATE", "9600"))
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "sensordata")

def connect_serial():
    while True:
        try:
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            print(f"[INFO] Porta seriale {SERIAL_PORT} aperta a {BAUD_RATE} baud.")
            return ser
        except serial.SerialException as e:
            print(f"[ATTESA] Porta seriale non disponibile: {e}")
            print("Riprovo tra 5 secondi...")
            time.sleep(5)

def connect_kafka():
    while True:
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BROKER,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print(f"[INFO] Connesso a Kafka su {KAFKA_BROKER}.")
            return producer
        except NoBrokersAvailable:
            print("[ATTESA] Kafka non disponibile, riprovo tra 5 secondi...")
            time.sleep(5)

def is_valid_payload(data):
    required_fields = {"temperature", "humidity", "gas", "sensor_id", "timestamp"}
    return isinstance(data, dict) and required_fields.issubset(data.keys())

# Avvio
ser = connect_serial()
producer = connect_kafka()

print("[INFO] Inizio lettura da seriale e invio a Kafka...")

while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if not line:
            continue

        try:
            payload = json.loads(line)
            if is_valid_payload(payload):
                producer.send(KAFKA_TOPIC, value=payload)
                print(f"[OK] Inviato su {KAFKA_TOPIC}: {payload}")
            else:
                print(f"[SCARTATO] Struttura JSON non valida: {payload}")
        except json.JSONDecodeError:
            print(f"[ERRORE] Decodifica fallita: {line}")

    except KeyboardInterrupt:
        print("[STOP] Interruzione manuale.")
        break
    except (serial.SerialException, KafkaTimeoutError) as e:
        print(f"[ERRORE] {e}")
        time.sleep(1)
