#!/bin/sh
set -eu

BROKER="${BROKER:-kafka:9092}"

echo "⏳ Waiting for Kafka..."
i=0
while [ $i -lt 60 ]; do
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
  shift 2
  # Costruisco la riga di comando senza array (POSIX)
  cmd="kafka-topics.sh --bootstrap-server \"$BROKER\" --create --if-not-exists --topic \"$topic\" --partitions \"$parts\" --replication-factor 1"
  for kv in "$@"; do
    cmd="$cmd --config \"$kv\""
  done
  # esegui la riga di comando; se esiste già, non fallire
  sh -c "$cmd" || true
}

# Live e Replay separati
create_topic "sensors.raw"    6 "retention.ms=172800000"  "compression.type=producer"
create_topic "sensors.replay" 6 "retention.ms=1209600000" "compression.type=producer"
create_topic "risk.index"     3 "retention.ms=172800000"  "compression.type=producer"

echo "✅ Topics ready."
