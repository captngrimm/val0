#!/usr/bin/env bash
set -u

OUT="/root/LAUNCHPAD/VAL0_output.txt"
REPO="/opt/val0"
CMD="${1:-help}"

mkdir -p /root/LAUNCHPAD

run_header() {
  echo "=== VAL0 OPS RUNNER ==="
  date -Is
  echo "COMMAND=$CMD"
  echo
  echo "=== REPO ==="
  cd "$REPO" || exit 1
  pwd
  echo
  echo "=== BRANCH / STATUS ==="
  git branch --show-current || true
  git status --short || true
  echo
  echo "=== SERVICE ==="
  systemctl is-active val0-bot.service || true
  echo
}

{
  run_header

  case "$CMD" in
    help)
      echo "Available commands:"
      echo "- inspect_karen_routes"
      echo "- inspect_karen_modules"
      echo "- inspect_service"
      echo "- inspect_git"
      ;;

    inspect_karen_routes)
      echo "=== LIVE BOT KAREN / DOCUMENT ROUTES ==="
      grep -nE "hazme un documento|redacta un documento|redáctame un documento|inventario de documentos|start_document_inventory|maybe_handle_document_inventory|maybe_capture_karen_case_event|maybe_handle_karen_recent_events_summary|handle_attachment|filters.Document.ALL|filters.PHOTO" bot.py || true
      ;;

    inspect_karen_modules)
      echo "=== KAREN NEXT ACTION ==="
      sed -n '1,360p' core/karen_next_action.py 2>/dev/null || true
      echo
      echo "=== KAREN RECENT ACTIVITY ==="
      sed -n '1,320p' core/karen_recent_activity.py 2>/dev/null || true
      ;;

    inspect_service)
      echo "=== VAL0 SERVICE STATUS ==="
      systemctl status val0-bot.service --no-pager -l || true
      echo
      echo "=== RECENT LOGS ==="
      journalctl -u val0-bot.service -n 120 --no-pager || true
      ;;

    inspect_git)
      echo "=== GIT GRAPH ==="
      git log --oneline -n 12 || true
      echo
      echo "=== STATUS ==="
      git status --short || true
      ;;

    *)
      echo "UNKNOWN COMMAND: $CMD"
      echo "Run: /root/val0_ops_runner.sh help"
      ;;
  esac
} > "$OUT" 2>&1
