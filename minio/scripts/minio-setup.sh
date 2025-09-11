#!/bin/sh
set -eu

MC="/usr/bin/mc"
S3_ENDPOINT="http://minio:9000"
ACCESS="minio"
SECRET="minio12345"
BUCKET="lake"

echo "⏳ Waiting for MinIO..."
# con healthcheck e depends_on:service_healthy è spesso superfluo
sleep 3

# Alias idempotente
$MC alias set local "$S3_ENDPOINT" "$ACCESS" "$SECRET" >/dev/null 2>&1 || true

# Crea bucket se non esiste (idempotente)
$MC mb --ignore-existing "local/$BUCKET" || true

# (Opzionale) rendi scaricabile anonimamente
$MC anonymous set download "local/$BUCKET" >/dev/null 2>&1 || true

echo "✅ MinIO bucket '$BUCKET' pronto."
