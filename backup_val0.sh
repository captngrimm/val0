#!/usr/bin/env bash
set -e

BASE_DIR="/opt/val0"
BACKUP_ROOT="$BASE_DIR/backups"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
TARGET_DIR="$BACKUP_ROOT/$TIMESTAMP"

mkdir -p "$TARGET_DIR"

echo "Creating Val-0 backup in: $TARGET_DIR"

cp "$BASE_DIR/bot.py" "$TARGET_DIR/bot.py"
cp "$BASE_DIR/memory_store.py" "$TARGET_DIR/memory_store.py"

if [ -f "$BASE_DIR/val0_memory.db" ]; then
    cp "$BASE_DIR/val0_memory.db" "$TARGET_DIR/val0_memory.db"
fi

echo "Backup complete."
