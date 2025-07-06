from flask import Flask, request, jsonify
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import serial
import json
import time

app = Flask(__name__)

# === CONFIG ===
SERIAL_PORT = 'COM9'
BAUD_RATE = 9600

# === SERIAL SETUP ===
ser = None
while ser is None:
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1, write_timeout=1)
        print(f"[OK] Porta seriale {SERIAL_PORT} aperta.")
    except serial.SerialException as e:
        print(f"[ERROR] Porta seriale non disponibile: {e}")
        time.sleep(5)

# === KAFKA SETUP ===
producer = None
while producer is None:
    try:
        producer = KafkaProducer(
            bootstrap_servers='localhost:9093',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except NoBrokersAvailable:
        print("Kafka non disponibile, riprovo in 5 secondi...")
        time.sleep(5)

# === ENDPOINT: riceve dati e li manda a Kafka ===
@app.route('/send-data', methods=['POST'])
def receive_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON received'}), 400

    producer.send('sensordata', value=data)
    producer.flush()
    return jsonify({'status': 'Data sent to Kafka'}), 200

# === NUOVO ENDPOINT: invia comando sulla seriale ===
@app.route('/send-command', methods=['POST'])
def send_command():
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'Missing "command" field'}), 400

    command = data['command'].strip().upper()
    try:
        ser.write((command + '\n').encode('utf-8'))
        time.sleep(0.05)
        print(f"[SERIAL] Comando inviato: {command}")
        return jsonify({'status': f'Command \"{command}\" sent to serial'}), 200
    except serial.SerialException as e:
        print(f"[ERROR] Errore invio seriale: {e}")
        return jsonify({'error': 'Failed to write to serial port'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)