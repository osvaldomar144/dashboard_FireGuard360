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
    
# === NUOVO ENDPOINT: invia abilitazione danger level 2 ===
@app.route('/fire_detection', methods=['POST'])
def fire_detection():
    data = request.get_json()

    if not data or not data.get("detection") is True:
        return jsonify({"status": "Nessuna azione eseguita"}), 200

    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # Trova l'ultimo record
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

# === NUOVO ENDPOINT: esegui script esterno ===
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
            check=False  # non solleva eccezioni se exit code ≠ 0
        )

        return jsonify({
            "exit_code": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip()
        }), 200

    except Exception as e:
        print(f"[SCRIPT ERROR] {e}")
        return jsonify({"error": f"Errore durante l'esecuzione: {str(e)}"}), 500



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)