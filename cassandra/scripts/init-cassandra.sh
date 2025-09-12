#!/bin/sh
set -eu

HOST="${CASSANDRA_HOST:-cassandra}"
PORT="${CASSANDRA_PORT:-9042}"
SCHEMA_SRC="/scripts/schema.cql"
SCHEMA_TMP="/tmp/schema.cql"

echo "⏳ Waiting for Cassandra at $HOST:$PORT ..."
i=0
# fino a ~5 minuti (60 * 5s)
while [ $i -lt 60 ]; do
  if cqlsh "$HOST" "$PORT" -e "DESCRIBE KEYSPACES" >/dev/null 2>&1; then
    break
  fi
  i=$((i+1))
  sleep 5
done

if [ $i -ge 60 ]; then
  echo "❌ Cassandra non è pronta dopo il timeout"
  exit 1
fi

# Normalizza CRLF -> LF per evitare errori
tr -d '\r' < "$SCHEMA_SRC" > "$SCHEMA_TMP"

echo "🧩 Applying schema (idempotente)..."
# Suggerito mettere IF NOT EXISTS in schema.cql su keyspace/tabelle
cqlsh "$HOST" "$PORT" -f "$SCHEMA_TMP"

echo "✅ Schema applied."
