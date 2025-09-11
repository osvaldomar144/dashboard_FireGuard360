#!/bin/sh
set -eu

BROKER="kafka:9092"

echo "⏳ Waiting for Kafka..."
i=0
while [ $i -lt 30 ]; do
  if kafka-topics.sh --bootstrap-server "$BROKER" --list >/dev/null 2>&1; then
    break
  fi
  i=$((i+1))
  sleep 2
done

echo "🧩 Creating topics (idempotent)..."
create_topic() {
  topic="$1"
  parts="$2"
  # --if-not-exists evita errori in caso esistano già
  kafka-topics.sh --bootstrap-server "$BROKER" \
    --create --if-not-exists --topic "$topic" \
    --partitions "$parts" --replication-factor 1 || true
}

create_topic "sensors.raw"    6
create_topic "sensors.agg-1m" 6
create_topic "risk.index"     3

echo "✅ Topics ready."
# Evita che il container termini subito (utile per debug)
tail -f /dev/null
