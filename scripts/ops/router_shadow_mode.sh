#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="val0-bot.service"
DROPIN_DIR="/etc/systemd/system/${SERVICE_NAME}.d"
DROPIN_FILE="${DROPIN_DIR}/intent-router-shadow.conf"
ENV_NAME="VAL0_INTENT_ROUTER_V2_SHADOW"

usage() {
  cat <<'EOF'
Usage: scripts/ops/router_shadow_mode.sh <enable|disable|status|logs>

Subcommands:
  enable   Enable Intent Router v2 shadow logging through a systemd drop-in.
  disable  Remove the shadow logging drop-in and restart the bot.
  status   Show service status and effective shadow environment.
  logs     Show recent router shadow/actual/compare log lines.

This helper does not touch .env or client files.
EOF
}

require_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "This command must be run as root because it writes systemd drop-ins and restarts ${SERVICE_NAME}." >&2
    echo "Try: sudo $0 $1" >&2
    exit 1
  fi
}

enable_shadow() {
  require_root "enable"
  install -d -m 0755 "${DROPIN_DIR}"
  cat > "${DROPIN_FILE}" <<EOF
[Service]
Environment="VAL0_INTENT_ROUTER_V2_SHADOW=true"
EOF
  systemctl daemon-reload
  systemctl restart "${SERVICE_NAME}"
  echo "Enabled ${ENV_NAME}=true for ${SERVICE_NAME}."
  echo "Use '$0 logs' to inspect [INTENT_ROUTER_V2_SHADOW], [INTENT_ROUTER_V2_ACTUAL], and [INTENT_ROUTER_V2_COMPARE] lines."
}

disable_shadow() {
  require_root "disable"
  rm -f "${DROPIN_FILE}"
  systemctl daemon-reload
  systemctl restart "${SERVICE_NAME}"
  echo "Disabled Intent Router v2 shadow mode for ${SERVICE_NAME}."
  echo "Verify no new [INTENT_ROUTER_V2_SHADOW] logs appear after this restart."
}

show_status() {
  echo "Drop-in file: ${DROPIN_FILE}"
  if [[ -f "${DROPIN_FILE}" ]]; then
    echo "Drop-in contents:"
    sed -n '1,20p' "${DROPIN_FILE}"
  else
    echo "Drop-in is not present. Shadow mode should be OFF unless configured elsewhere."
  fi
  echo
  systemctl show "${SERVICE_NAME}" --property=Environment --no-pager || true
  echo
  systemctl status "${SERVICE_NAME}" --no-pager || true
}

show_logs() {
  journalctl -u "${SERVICE_NAME}" -n 500 --no-pager \
    | grep -E '\[INTENT_ROUTER_V2_(SHADOW|ACTUAL|COMPARE)\]' \
    | tail -100 || true
}

main() {
  local command="${1:-}"
  case "${command}" in
    enable)
      enable_shadow
      ;;
    disable)
      disable_shadow
      ;;
    status)
      show_status
      ;;
    logs)
      show_logs
      ;;
    -h|--help|help|"")
      usage
      ;;
    *)
      echo "Unknown subcommand: ${command}" >&2
      usage >&2
      exit 2
      ;;
  esac
}

main "$@"
