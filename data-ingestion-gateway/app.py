from flask import Flask, request, jsonify
from flask_cors import CORS
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import pymysql
import serial
import json
import time
import subprocess
import os
import threading
from datetime import datetime

app = Flask(__name__)
CORS(app)

# === CONFIG ===
SERIAL_PORT = 'COM10'
BAUD_RATE = 9600
SCRIPT_PATH = r"C:\Users\marce\Desktop\dashboard_FireGuard360\drone-handle\drone_with_REST.py"

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "fireguard_user",
    "password": "fireguard_pass",
    "database": "fireGuard360_db"
}

# === FUNZIONI DI CONNESSIONE ===
def connetti_seriale():
    while True:
        try:
            s = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1, write_timeout=1)
            print(f"[OK] Porta seriale {SERIAL_PORT} aperta.")
            return s
        except serial.SerialException as e:
            print(f"[ERROR] Porta seriale non disponibile: {e}")
            time.sleep(5)

def connetti_kafka():
    while True:
        try:
            p = KafkaProducer(
                bootstrap_servers='localhost:9093',
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            print("[OK] Connesso a Kafka.")
            return p
        except NoBrokersAvailable:
            print("Kafka non disponibile, riprovo in 5 secondi...")
            time.sleep(5)

# === INIZIALIZZAZIONE SERIAL E KAFKA ===
ser = connetti_seriale()
producer = connetti_kafka()

# === THREAD DI LETTURA CONTINUA DA SERIAL E PUBBLICAZIONE SU KAFKA ===
def serial_read_loop():
    global ser, producer
    while True:
        try:
            line = ser.readline().decode("utf-8").strip()
            if line:
                try:
                    data = json.loads(line)
                    if isinstance(data, dict):
                        data["timestamp"] = datetime.utcnow().isoformat() + "Z"
                        if "sensor_id" not in data:
                            data["sensor_id"] = "unknown"
                        producer.send('sensordata', value=data)
                        print(f"[Kafka] Inviato: {data}")
                except json.JSONDecodeError:
                    print(f"[ERRORE JSON] Linea non valida: {line}")
        except serial.SerialException as se:
            print(f"[ERRORE Serial] {se}, riconnessione...")
            ser = connetti_seriale()
        except Exception as e:
            print(f"[ERRORE Generico] {e}")
            time.sleep(2)

# === ENDPOINT: riceve dati manuali e li manda a Kafka ===
@app.route('/send-data', methods=['POST'])
def receive_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON received'}), 400

    data["timestamp"] = datetime.utcnow().isoformat() + "Z"
    if "sensor_id" not in data:
        data["sensor_id"] = "manual"
    producer.send('sensordata', value=data)
    producer.flush()
    return jsonify({'status': 'Data sent to Kafka'}), 200

# === ENDPOINT: invia comando seriale ===
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

# === ENDPOINT: aggiorna danger_level = 2 nell'ultimo record ===
@app.route('/fire_detection', methods=['POST'])
def fire_detection():
    data = request.get_json()
    if not data or not data.get("detection") is True:
        return jsonify({"status": "Nessuna azione eseguita"}), 200

    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            select_sql = "SELECT id FROM system_danger_level ORDER BY calculated_at DESC LIMIT 1"
            cursor.execute(select_sql)
            row = cursor.fetchone()
            if row:
                last_id = row[0]
                update_sql = "UPDATE system_danger_level SET danger_level = 2 WHERE id = %s"
                cursor.execute(update_sql, (last_id,))
                conn.commit()
                return jsonify({"status": f"Record {last_id} aggiornato a danger_level = 2"}), 200
            else:
                return jsonify({"error": "Nessun record trovato in system_danger_level"}), 404
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return jsonify({"error": "Errore durante l'accesso al database"}), 500
    finally:
        if conn:
            conn.close()

# === ENDPOINT: esegue script esterno Python ===
@app.route('/run-script', methods=['POST'])
def run_script():
    if not os.path.isfile(SCRIPT_PATH):
        return jsonify({"error": f"Script non trovato: {SCRIPT_PATH}"}), 404

    try:
        result = subprocess.run(
            ["python", SCRIPT_PATH, "1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        return jsonify({
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }), 200

    except Exception as e:
        print(f"[SCRIPT ERROR] {e}")
        return jsonify({"error": f"Errore durante l'esecuzione: {str(e)}"}), 500

# === AVVIO SERVER E THREAD DI LETTURA ===
if __name__ == '__main__':
    serial_thread = threading.Thread(target=serial_read_loop, daemon=True)
    serial_thread.start()
    app.run(host='0.0.0.0', port=5001)