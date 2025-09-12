#!/bin/sh
set -euo pipefail

MC="/usr/bin/mc"
S3_ENDPOINT="http://minio:9000"
ACCESS="${MINIO_ROOT_USER:-minio}"
SECRET="${MINIO_ROOT_PASSWORD:-minio12345}"
BUCKET="lake"

echo "⏳ Waiting for MinIO..."
sleep 3

# Alias + bucket idempotenti
$MC alias set local "$S3_ENDPOINT" "$ACCESS" "$SECRET" >/dev/null 2>&1 || true
$MC mb --ignore-existing "local/$BUCKET" >/dev/null 2>&1 || true
$MC anonymous set download "local/$BUCKET" >/dev/null 2>&1 || true

# Reset opzionale (solo se vuoi ripartire da zero)
if [ "${RESET_LAKE:-0}" = "1" ]; then
  echo "[minio-setup] RESET_LAKE=1 -> cleaning prefixes"
  $MC rm -r --force local/$BUCKET/checkpoints || true
  $MC rm -r --force local/$BUCKET/gold/sensor_stats_1m || true
  $MC rm -r --force local/$BUCKET/gold/risk_index_10m || true
  $MC rm -r --force local/$BUCKET/gold/daily || true
fi

# Pre-crea i prefix usati dai job (metto un .keep vuoto)
tmpfile="$(mktemp)"; : > "$tmpfile"
for p in \
  $BUCKET/checkpoints \
  $BUCKET/gold/sensor_stats_1m \
  $BUCKET/gold/risk_index_10m \
  $BUCKET/gold/daily \
; do
  $MC cp "$tmpfile" "local/$p/.keep" >/dev/null 2>&1 || true
done
rm -f "$tmpfile"

echo "✅ MinIO bucket '$BUCKET' pronto."
