#!/usr/bin/env bash
set -euo pipefail

ROOT="/opt/val0"
UNIT="val0-bot.service"
BRANCH_EXPECTED="miguel-mvp-v2"
PY="$ROOT/.venv/bin/python"

DO_RESTART="0"
for arg in "$@"; do
  case "$arg" in
    --restart) DO_RESTART="1" ;;
    -h|--help)
      echo "Usage: sudo $ROOT/tools/ops_health.sh [--restart]"
      echo "Default: 100% read-only. --restart prompts for confirmation."
      exit 0
      ;;
  esac
done

need_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "ERROR: Run as root (systemd/journal/paths)."
    exit 1
  fi
}

ok()   { echo "OK   - $*"; }
warn() { echo "WARN - $*"; }
fail() { echo "FAIL - $*"; FAILS=$((FAILS+1)); }

FAILS=0
need_root
cd "$ROOT"

echo "VAL0 OPS HEALTH  $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "================================================="

# 1) Git status + branch (read-only)
echo
echo "== GIT =="
git status -sb || true
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
if [[ "$BRANCH" == "$BRANCH_EXPECTED" ]]; then
  ok "branch=$BRANCH"
else
  fail "branch=$BRANCH (expected $BRANCH_EXPECTED)"
fi

if git diff --quiet && git diff --cached --quiet; then
  ok "working tree clean"
else
  fail "working tree NOT clean (uncommitted changes present)"
fi

# 2) Service status (read-only unless --restart)
echo
echo "== SERVICE =="
if systemctl is-active --quiet "$UNIT"; then
  ok "$UNIT active"
else
  fail "$UNIT NOT active"
fi

if systemctl is-enabled --quiet "$UNIT"; then
  ok "$UNIT enabled"
else
  warn "$UNIT not enabled"
fi

# 3) Systemd env flags (source of truth)
echo
echo "== ENV (systemd: show) =="
ENV_LINES="$(systemctl show "$UNIT" -p Environment --no-pager | tr ' ' '\n' | grep -E '^(VAL0_|PYTHONWARNINGS=)' || true)"
if [[ -z "$ENV_LINES" ]]; then
  warn "no VAL0_ env found in systemctl show -p Environment (may be normal if env is only in drop-in)"
else
  echo "$ENV_LINES" | sort
fi

get_env_show() { echo "$ENV_LINES" | awk -F= -v k="$1" '$1==k{print $2}' | tail -n 1; }

# Fallback: parse Environment= lines from systemctl cat (unit + drop-ins)
get_env_from_unit() {
  local key="$1"
  systemctl cat "$UNIT" 2>/dev/null \
    | awk -v want="$key=" '
        $0 ~ /^[[:space:]]*Environment=/ {
          sub(/^[[:space:]]*Environment=/, "", $0)
          # systemd allows multiple assignments per Environment= line; we only need exact match key=
          n=split($0, a, /[[:space:]]+/)
          for (i=1; i<=n; i++) {
            if (index(a[i], want) == 1) {
              sub(want, "", a[i])
              print a[i]
            }
          }
        }
      ' \
    | tail -n 1
}

get_env() {
  local k="$1"
  local v
  v="$(get_env_show "$k")"
  if [[ -n "$v" ]]; then
    echo "$v"
    return 0
  fi
  get_env_from_unit "$k"
}

VAL0_TZ="$(get_env VAL0_TZ)"
VAL0_GCAL_ENABLED="$(get_env VAL0_GCAL_ENABLED)"
VAL0_GCAL_INCLUDE_UNBOUND="$(get_env VAL0_GCAL_INCLUDE_UNBOUND)"
VAL0_DB_PATH="$(get_env VAL0_DB_PATH)"
VAL0_DB_KEY_FILE="$(get_env VAL0_DB_KEY_FILE)"

echo
echo "== ENV (systemd: resolved) =="
printf "VAL0_TZ=%s\n" "${VAL0_TZ:-}"
printf "VAL0_GCAL_ENABLED=%s\n" "${VAL0_GCAL_ENABLED:-}"
printf "VAL0_GCAL_INCLUDE_UNBOUND=%s\n" "${VAL0_GCAL_INCLUDE_UNBOUND:-}"
printf "VAL0_DB_PATH=%s\n" "${VAL0_DB_PATH:-}"
printf "VAL0_DB_KEY_FILE=%s\n" "${VAL0_DB_KEY_FILE:-}"

[[ -n "$VAL0_TZ" ]] && ok "VAL0_TZ=$VAL0_TZ" || fail "VAL0_TZ missing"
[[ -n "$VAL0_GCAL_ENABLED" ]] && ok "VAL0_GCAL_ENABLED=$VAL0_GCAL_ENABLED" || fail "VAL0_GCAL_ENABLED missing"
[[ -n "$VAL0_GCAL_INCLUDE_UNBOUND" ]] && ok "VAL0_GCAL_INCLUDE_UNBOUND=$VAL0_GCAL_INCLUDE_UNBOUND" || warn "VAL0_GCAL_INCLUDE_UNBOUND missing (defaults may apply)"
[[ -n "$VAL0_DB_PATH" ]] && ok "VAL0_DB_PATH set" || fail "VAL0_DB_PATH missing"
[[ -n "$VAL0_DB_KEY_FILE" ]] && ok "VAL0_DB_KEY_FILE set" || fail "VAL0_DB_KEY_FILE missing"

# 4) DB path + SQLCipher indicator (read-only, no DB open)
echo
echo "== DB (SQLCipher sanity; read-only) =="
if [[ -n "$VAL0_DB_PATH" && -f "$VAL0_DB_PATH" ]]; then
  SZ="$(stat -c '%s' "$VAL0_DB_PATH" 2>/dev/null || echo '?')"
  MODE="$(stat -c '%a' "$VAL0_DB_PATH" 2>/dev/null || echo '?')"
  ok "db exists size=$SZ mode=$MODE path=$VAL0_DB_PATH"

  # Plain sqlite header starts with "SQLite format 3\000"
  if head -c 16 "$VAL0_DB_PATH" 2>/dev/null | tr -d '\000' | grep -q "SQLite format 3"; then
    fail "db header looks like PLAINTEXT sqlite (expected SQLCipher)"
  else
    ok "db header does NOT look like plaintext sqlite (expected for SQLCipher)"
  fi
else
  fail "db missing at VAL0_DB_PATH"
fi

if [[ -n "$VAL0_DB_KEY_FILE" && -f "$VAL0_DB_KEY_FILE" ]]; then
  KMODE="$(stat -c '%a' "$VAL0_DB_KEY_FILE" 2>/dev/null || echo '?')"
  KSZ="$(stat -c '%s' "$VAL0_DB_KEY_FILE" 2>/dev/null || echo '?')"
  if [[ "$KMODE" == "600" ]]; then
    ok "db_key exists mode=600 size=$KSZ path=$VAL0_DB_KEY_FILE"
  else
    warn "db_key exists mode=$KMODE (expected 600) size=$KSZ path=$VAL0_DB_KEY_FILE"
  fi
else
  fail "db_key missing at VAL0_DB_KEY_FILE"
fi

# 5) GCAL enabled + token file existence (no contents)
echo
echo "== GCAL (state + files; no contents) =="
case "${VAL0_GCAL_ENABLED,,}" in
  1|true|yes|on) ok "GCAL enabled (VAL0_GCAL_ENABLED=$VAL0_GCAL_ENABLED)" ;;
  *) warn "GCAL not enabled (VAL0_GCAL_ENABLED=$VAL0_GCAL_ENABLED)" ;;
esac

GCAL_DIR="/etc/val0/gcal"
if [[ -d "$GCAL_DIR" ]]; then
  ok "gcal_dir exists: $GCAL_DIR"
  ls -1 "$GCAL_DIR" 2>/dev/null | sed 's/^/file=/' || true
  for f in calendar_id client_secret.json refresh_token; do
    [[ -f "$GCAL_DIR/$f" ]] && ok "gcal_file exists: $f" || warn "gcal_file missing: $f"
  done
else
  warn "gcal_dir missing: $GCAL_DIR"
fi

# 6) Quick Python import sanity (PURE, non-executing): py_compile core modules
echo
echo "== PYTHON (py_compile sanity; non-executing) =="
if [[ -x "$PY" ]]; then
  ok "venv python: $PY"
else
  fail "venv python missing: $PY"
fi

PY_FILES=( "core/case_mvp.py" "core/due_merge.py" "core/gcal_client.py" "core/doctor.py" )
MISSING=0
for f in "${PY_FILES[@]}"; do
  [[ -f "$ROOT/$f" ]] || { warn "missing file: $f"; MISSING=1; }
done

if [[ "$MISSING" == "0" ]]; then
  if "$PY" -m py_compile "${PY_FILES[@]}" >/dev/null 2>&1; then
    ok "py_compile OK (${PY_FILES[*]})"
  else
    fail "py_compile FAILED (run: $PY -m py_compile ${PY_FILES[*]})"
  fi
else
  warn "py_compile skipped (missing files)"
fi

# 7) Smoke gate check (regex-only, pure; no project imports, no DB, no Telegram)
echo
echo "== SMOKE GATE MATCH (regex-only, pure) =="
"$PY" - <<'PY'
import re
def clean(s: str) -> str:
    return " ".join(s.strip().lower().split())
tests = [
  ("Qué vence hoy?", r"\b(que|qué)\s+vence\s+hoy\b"),
  ("Que vence hoy?", r"\b(que|qué)\s+vence\s+hoy\b"),
  ("Qué vence esta semana?", r"\b(que|qué)\s+vence\s+esta\s+semana\b"),
  ("Qué vence en 2 semanas?", r"\b(que|qué)\s+vence(?:\s+en(?:\s+las)?)?(?:\s+las)?(?:\s+(?:proximas|próximas))?\s+(\d+)\s+semanas?\b"),
  ("Resumen del expediente 524242024", r"\bresumen\s+del\s+expediente\s+\d+\b"),
]
passed = 0
for text, pat in tests:
    m = re.search(pat, clean(text))
    print(f"{'OK' if m else 'FAIL'} - {text}")
    passed += 1 if m else 0
print(f"gate_regex_passed={passed}/{len(tests)}")
PY

# 8) Explicit restart path (mutation only when requested) + confirmation prompt
if [[ "$DO_RESTART" == "1" ]]; then
  echo
  echo "== RESTART (explicit) =="
  echo "This will restart: $UNIT"
  read -r -p "Type RESTART to confirm: " CONFIRM
  if [[ "$CONFIRM" != "RESTART" ]]; then
    warn "restart aborted (confirmation not received)"
  else
    systemctl daemon-reload
    systemctl restart "$UNIT"
    ok "restart completed"
    systemctl --no-pager --full status "$UNIT" | sed -n '1,25p' || true
  fi
fi

echo
echo "== SUMMARY =="
if [[ "$FAILS" -eq 0 ]]; then
  ok "health=GREEN"
  exit 0
else
  fail "health=RED fails=$FAILS"
  exit 2
fi
