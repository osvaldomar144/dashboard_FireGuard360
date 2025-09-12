#!/bin/sh
set -eu

echo "⏳ Waiting for Cassandra..."
i=0
while [ $i -lt 40 ]; do
  if cqlsh cassandra 9042 -e "DESCRIBE KEYSPACES" >/dev/null 2>&1; then
    break
  fi
  i=$((i+1))
  sleep 3
done

echo "🧩 Applying schema..."
cqlsh cassandra 9042 -f /scripts/schema.cql
echo "✅ Schema applied."
#tail -f /dev/null