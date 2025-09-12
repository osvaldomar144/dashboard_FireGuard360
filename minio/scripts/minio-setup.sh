#!/bin/sh
set -eu

MC="/usr/bin/mc"
S3_ENDPOINT="http://minio:9000"
ACCESS="${MINIO_ROOT_USER:-minio}"
SECRET="${MINIO_ROOT_PASSWORD:-minio12345}"
BUCKET="${BUCKET:-lake}"
RESET="${RESET_LAKE:-0}"

echo "⏳ Waiting for MinIO..."
$MC alias set local "$S3_ENDPOINT" "$ACCESS" "$SECRET" >/dev/null 2>&1 || true

i=0
until $MC ls local >/dev/null 2>&1; do
  i=$((i+1))
  [ "$i" -gt 120 ] && echo "❌ MinIO non pronto dopo 120s" && exit 1
  sleep 1
done

[ "$RESET" = "1" ] && {
  echo "🧹 RESET_LAKE=1 -> cleaning prefixes"
  $MC rm -r --force "local/$BUCKET/checkpoints" >/dev/null 2>&1 || true
  $MC rm -r --force "local/$BUCKET/gold/sensor_stats_1m" >/dev/null 2>&1 || true
  $MC rm -r --force "local/$BUCKET/gold/risk_index_10m" >/dev/null 2>&1 || true
  $MC rm -r --force "local/$BUCKET/gold/daily" >/dev/null 2>&1 || true
}

$MC mb --ignore-existing "local/$BUCKET" >/dev/null 2>&1 || true
$MC anonymous set download "local/$BUCKET" >/dev/null 2>&1 || true
echo "✅ MinIO bucket '$BUCKET' pronto (reset=$RESET)."
