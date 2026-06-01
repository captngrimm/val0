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

is_secret_env_key() {
  local key_upper
  key_upper="$(printf '%s' "$1" | tr '[:lower:]' '[:upper:]')"
  [[ "${key_upper}" == *KEY* \
    || "${key_upper}" == *TOKEN* \
    || "${key_upper}" == *SECRET* \
    || "${key_upper}" == *PASSWORD* \
    || "${key_upper}" == *PASS* \
    || "${key_upper}" == *CREDENTIAL* \
    || "${key_upper}" == "RESEND_API_KEY" ]]
}

print_redacted_environment() {
  local raw_env token key value
  raw_env="$(systemctl show "${SERVICE_NAME}" --property=Environment --value --no-pager 2>/dev/null || true)"
  echo "Environment (secret values redacted):"
  if [[ -z "${raw_env}" ]]; then
    echo "  <empty or unavailable>"
    return
  fi

  # systemctl prints Environment as a space-separated assignment list. This keeps
  # status useful while avoiding raw KEY/TOKEN/SECRET/PASSWORD values in output.
  for token in ${raw_env}; do
    key="${token%%=*}"
    value="${token#*=}"
    if [[ "${token}" != *"="* ]]; then
      continue
    fi
    if is_secret_env_key "${key}"; then
      printf '  %s=***REDACTED***\n' "${key}"
    else
      printf '  %s=%s\n' "${key}" "${value}"
    fi
  done
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
  print_redacted_environment
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
