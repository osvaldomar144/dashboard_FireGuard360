import os, json, time
from datetime import timezone
import pandas as pd
from kafka import KafkaProducer

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")
TOPIC = os.getenv("TOPIC", "sensors.raw")
CSV_PATH = os.getenv("CSV_PATH", "/data/firms_sample.csv")
TIME_COL = os.getenv("TIME_COL", "time")
LAT_COL = os.getenv("LAT_COL", "lat")
LON_COL = os.getenv("LON_COL", "lon")
SPEED_MULTIPLIER = float(os.getenv("SPEED_MULTIPLIER", "10.0"))
MAX_MSGS_PER_SEC = float(os.getenv("MAX_MSGS_PER_SEC", "1000"))

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    key_serializer=lambda k: k.encode("utf-8")
)

df = pd.read_csv(CSV_PATH)
if TIME_COL not in df.columns:
    raise ValueError(f"TIME_COL '{TIME_COL}' non presente nel CSV {CSV_PATH}")

df[TIME_COL] = pd.to_datetime(df[TIME_COL], utc=True, errors="coerce")
df = df.dropna(subset=[TIME_COL]).sort_values(TIME_COL).reset_index(drop=True)

def build_event(row):
    ts = row[TIME_COL].to_pydatetime().astimezone(timezone.utc).isoformat()
    lat = float(row[LAT_COL]) if LAT_COL in df.columns else 41.9
    lon = float(row[LON_COL]) if LON_COL in df.columns else 12.5
    sid = f"S-FRM-{int(lat*100)}-{int(lon*100)}"
    return sid, {
        "ts": ts,
        "sensor_id": sid,
        "loc": {"lat": lat, "lon": lon, "cell_id": f"CELL_{int(lat*10)}_{int(lon*10)}"},
        "metrics": {"temp": 30.0, "hum": 40.0, "gas": 350, "pm25": 10.0, "wind": 2.0},
        "battery": 100
    }

sent_in_window = 0
window_start = time.time()

for _, row in df.iterrows():
    sid, msg = build_event(row)

    # pacing temporale basato sugli intervalli tra record, scalati
    # (qui semplifichiamo: inviamo alla massima velocità consentita dal rate limiter)
    now = time.time()
    if now - window_start >= 1.0:
        sent_in_window = 0
        window_start = now
    if sent_in_window >= MAX_MSGS_PER_SEC:
        time.sleep(max(0, 1.0 - (now - window_start)))
        sent_in_window = 0
        window_start = time.time()

    producer.send(TOPIC, key=sid, value=msg)
    sent_in_window += 1

producer.flush()
