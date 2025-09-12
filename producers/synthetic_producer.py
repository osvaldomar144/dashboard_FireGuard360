import os, json, time, random
from datetime import datetime, timezone
from kafka import KafkaProducer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("TOPIC", "sensors.raw")
SENSORS = int(os.getenv("SENSORS", "100"))
MSGS_PER_SEC = float(os.getenv("MSGS_PER_SEC", "100"))
SPIKE_PROB = float(os.getenv("SPIKE_PROB", "0.01"))

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8")
)

sensor_ids = [f"S-{i:03d}" for i in range(1, SENSORS+1)]
interval = 1.0 / max(MSGS_PER_SEC, 0.1)

def make_evt(sid: str):
    now = datetime.now(timezone.utc).isoformat()
    spike = 20*random.random() if random.random() < SPIKE_PROB else 0
    return {
        "ts": now,
        "sensor_id": sid,
        "loc": {
            "lat": 41.9 + random.random()*0.05,
            "lon": 12.5 + random.random()*0.05,
            "cell_id": f"CELL_{int(random.random()*100)}"
        },
        "metrics": {
            "temp": round(28 + random.random()*8 + spike, 2),
            "hum": round(15 + random.random()*60, 2),
            "gas": int(300 + random.random()*400 + spike*10),
            "pm25": round(5 + random.random()*40, 1),
            "wind": round(random.random()*8, 1)
        },
        "battery": int(50 + random.random()*50)
    }

i = 0
while True:
    sid = sensor_ids[i % SENSORS]
    producer.send(TOPIC, key=sid, value=make_evt(sid))
    i += 1
    time.sleep(interval)