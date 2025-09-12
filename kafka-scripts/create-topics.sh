#!/bin/bash
set -euo pipefail

BROKER="${BROKER:-kafka:9092}"

echo "⏳ Waiting for Kafka..."
for i in $(seq 1 60); do
  if kafka-topics.sh --bootstrap-server "$BROKER" --list >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "🧩 Creating topics (idempotent)..."

create_topic() {
  local topic="$1"
  local parts="$2"
  shift 2
  local cfg_args=()
  for kv in "$@"; do
    cfg_args+=(--config "$kv")
  done
  kafka-topics.sh --bootstrap-server "$BROKER" \
    --create --if-not-exists \
    --topic "$topic" \
    --partitions "$parts" \
    --replication-factor 1 \
    "${cfg_args[@]}" || true
}

# Live e Replay separati, retention e compressione consigliate
create_topic "sensors.raw"    6 "retention.ms=172800000"  "compression.type=producer"  # 48h
create_topic "sensors.replay" 6 "retention.ms=1209600000" "compression.type=producer"  # 14 giorni
create_topic "risk.index"     3 "retention.ms=172800000"  "compression.type=producer"  # 48h

echo "✅ Topics ready."
# lascia il container vivo per i log
#tail -f /dev/null
