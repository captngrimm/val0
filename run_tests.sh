#!/usr/bin/env bash
set -euo pipefail

cd /opt/val0

VENV_PY="/opt/val0/.venv/bin/python"
if [[ ! -x "$VENV_PY" ]]; then
  echo "ERROR: venv python not found at $VENV_PY" >&2
  exit 1
fi

export PYTHONUNBUFFERED=1

echo "== Val0 test run =="
"$VENV_PY" -m unittest -q
echo "== OK =="
