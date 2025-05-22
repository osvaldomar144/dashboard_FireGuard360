from flask import Flask, request, jsonify
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable
import json
import time

app = Flask(__name__)

producer = None
while producer is None:
    try:
        producer = KafkaProducer(
            bootstrap_servers='kafka:9092',
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except NoBrokersAvailable:
        print("Kafka non disponibile, riprovo in 5 secondi...")
        time.sleep(5)

@app.route('/send-data', methods=['POST'])
def receive_data():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON received'}), 400

    producer.send('sensordata', value=data)
    producer.flush()
    return jsonify({'status': 'Data sent to Kafka'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
