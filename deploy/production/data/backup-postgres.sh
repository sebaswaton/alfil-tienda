#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ENV_FILE=${ENV_FILE:-"$SCRIPT_DIR/.env.production"}
BACKUP_DIR=${BACKUP_DIR:-/srv/alfil/backups/postgres}
RETENTION_DAYS=${RETENTION_DAYS:-14}
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
DESTINATION="$BACKUP_DIR/alfil_tienda_$TIMESTAMP.dump"
TEMP_FILE="$DESTINATION.tmp"

umask 077
mkdir -p "$BACKUP_DIR"

docker compose \
  --env-file "$ENV_FILE" \
  --file "$SCRIPT_DIR/compose.yml" \
  exec -T postgres \
  sh -c 'pg_dump --username="$POSTGRES_USER" --dbname="$POSTGRES_DB" --format=custom' \
  > "$TEMP_FILE"

mv "$TEMP_FILE" "$DESTINATION"
find "$BACKUP_DIR" -type f -name 'alfil_tienda_*.dump' -mtime "+$RETENTION_DAYS" -delete

printf 'PostgreSQL backup created: %s\n' "$DESTINATION"
