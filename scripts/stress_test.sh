#!/usr/bin/env bash
# ==============================================================================
# PointQR API & Celery Queue Stress Testing Wrapper
# ==============================================================================
#
# Usage:
#   ./scripts/stress_test.sh -k <API_KEY> -n 25 -c 5
#   ./scripts/stress_test.sh --pure-bash -k <API_KEY> -n 10
#   POINTQR_API_KEY=pqr_... ./scripts/stress_test.sh -n 50
#
# Flags:
#   -k, --api-key <KEY>     Personal PointQR API key (or $POINTQR_API_KEY)
#   -n, --count <NUM>       Number of QR codes to generate (default: 10)
#   -c, --concurrency <NUM> Concurrency workers (default: 5)
#   -u, --url <URL>         Base API URL (default: http://localhost/api)
#   -t, --type <TYPE>       QR code type: mixed, static, dynamic (default: mixed)
#   --scans                 Simulate scans on dynamic QRs to test scan_analytics queue
#   --no-export             Skip Celery export jobs
#   --no-poll               Fire-and-forget Celery jobs without polling
#   --pure-bash             Execute stress test using native Bash + curl loop
#   -h, --help              Show this help message
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/stress_test_qrcodes.py"

API_KEY="${POINTQR_API_KEY:-}"
COUNT=10
CONCURRENCY=5
BASE_URL="http://localhost/api"
QR_TYPE="mixed"
SIMULATE_SCANS=0
EXPORT_JOBS=1
POLL_JOBS=1
PURE_BASH=0

# ANSI colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

show_help() {
  cat <<EOF
PointQR API & Celery Queue Stress Tester

Usage:
  $(basename "$0") [options]

Options:
  -k, --api-key <KEY>     API Key for X-API-Key header (env: POINTQR_API_KEY)
  -n, --count <NUM>       Total QR codes to generate (default: 10)
  -c, --concurrency <NUM> Parallel worker threads (default: 5)
  -u, --url <URL>         API base URL (default: http://localhost/api)
  -t, --type <TYPE>       mixed | static | dynamic (default: mixed)
  --scans                 Hit dynamic QR redirect URL to test scan_analytics queue
  --no-export             Disable Celery async export jobs
  --no-poll               Do not wait for Celery jobs to complete
  --pure-bash             Run standalone Bash/curl loop (no python required)
  -h, --help              Show this help text

Examples:
  ./scripts/stress_test.sh -k "pqr_..." -n 20
  ./scripts/stress_test.sh -k "pqr_..." -n 50 -c 10 --scans
  ./scripts/stress_test.sh --pure-bash -k "pqr_..." -n 15
EOF
}

# Parse options
EXTRA_PY_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -k|--api-key)
      API_KEY="$2"
      shift 2
      ;;
    -n|--count)
      COUNT="$2"
      shift 2
      ;;
    -c|--concurrency)
      CONCURRENCY="$2"
      shift 2
      ;;
    -u|--url)
      BASE_URL="$2"
      shift 2
      ;;
    -t|--type)
      QR_TYPE="$2"
      shift 2
      ;;
    --scans)
      SIMULATE_SCANS=1
      shift
      ;;
    --no-export)
      EXPORT_JOBS=0
      shift
      ;;
    --no-poll)
      POLL_JOBS=0
      shift
      ;;
    --email)
      EXTRA_PY_ARGS+=(--email "$2")
      shift 2
      ;;
    --password)
      EXTRA_PY_ARGS+=(--password "$2")
      shift 2
      ;;
    --auto-login)
      EXTRA_PY_ARGS+=(--auto-login "$2")
      shift 2
      ;;
    --pure-bash)
      PURE_BASH=1
      shift
      ;;
    -h|--help)
      show_help
      exit 0
      ;;
    *)
      EXTRA_PY_ARGS+=("$1")
      shift
      ;;
  esac
done

# If running through python runner, let Python handle auth (API key, auto-login, or email prompt)
if [[ "$PURE_BASH" -eq 0 ]] && command -v python3 &>/dev/null && [[ -f "$PYTHON_SCRIPT" ]]; then
  PY_CMD=(
    python3 "$PYTHON_SCRIPT"
    --count "$COUNT"
    --concurrency "$CONCURRENCY"
    --url "$BASE_URL"
    --type "$QR_TYPE"
  )
  [[ -n "$API_KEY" ]] && PY_CMD+=(--api-key "$API_KEY")
  [[ "$EXPORT_JOBS" -eq 0 ]] && PY_CMD+=(--no-export)
  [[ "$POLL_JOBS" -eq 0 ]] && PY_CMD+=(--no-poll)
  [[ "$SIMULATE_SCANS" -eq 1 ]] && PY_CMD+=(--simulate-scans)
  if [[ ${#EXTRA_PY_ARGS[@]} -gt 0 ]]; then
    PY_CMD+=("${EXTRA_PY_ARGS[@]}")
  fi

  exec "${PY_CMD[@]}"
fi

if [[ -z "$API_KEY" ]]; then
  echo -e "${RED}Error: API key required for pure-bash mode. Use -k <KEY> or export POINTQR_API_KEY=...${NC}" >&2
  exit 1
fi

# -----------------------------------------------------------------------------
# Standalone Pure-Bash Curl Stress Test
# -----------------------------------------------------------------------------
echo -e "${CYAN}========================================================================${NC}"
echo -e "${BOLD}${CYAN}  POINTQR PURE-BASH API & CELERY STRESS TESTER${NC}"
echo -e "${CYAN}========================================================================${NC}"
echo -e " Target URL       : ${BASE_URL}"
echo -e " QR Codes Count   : ${BOLD}${COUNT}${NC}"
echo -e " Type             : ${QR_TYPE}"
echo -e " Celery Export    : $([[ $EXPORT_JOBS -eq 1 ]] && echo 'Enabled' || echo 'Disabled')"
echo -e "${CYAN}------------------------------------------------------------------------${NC}"

CREATED_OK=0
CREATED_FAIL=0
CELERY_OK=0
START_TIME=$(date +%s)

# Style variations array
STYLES=(
  '{"dots":"#0f172a","dot_type":"square","sq_type":"square","corner":"#1e3a8a","bg":"#ffffff","name":"Midnight Tech"}'
  '{"dots":"#065f46","dot_type":"dots","sq_type":"dot","corner":"#047857","bg":"#f0fdf4","name":"Emerald Eco"}'
  '{"dots":"#991b1b","dot_type":"rounded","sq_type":"extra-rounded","corner":"#b91c1c","bg":"#fffbeb","name":"Crimson Ruby"}'
  '{"dots":"#6d28d9","dot_type":"classy","sq_type":"extra-rounded","corner":"#4c1d95","bg":"#faf5ff","name":"Cyber Purple"}'
  '{"dots":"#c2410c","dot_type":"classy-rounded","sq_type":"square","corner":"#ea580c","bg":"#fff7ed","name":"Sunset Amber"}'
  '{"dots":"#0f766e","dot_type":"extra-rounded","sq_type":"dot","corner":"#0e7490","bg":"#f0fdfa","name":"Ocean Teal"}'
)
FORMATS=("png" "svg" "pdf" "eps")

for ((i=1; i<=COUNT; i++)); do
  STYLE_IDX=$(( (i - 1) % ${#STYLES[@]} ))
  STYLE_JSON="${STYLES[$STYLE_IDX]}"
  FMT_IDX=$(( (i - 1) % ${#FORMATS[@]} ))
  EXPORT_FMT="${FORMATS[$FMT_IDX]}"

  # Extract style fields (simple parameter extraction without external tools)
  DOTS=$(echo "$STYLE_JSON" | grep -o '"dots":"[^"]*"' | cut -d'"' -f4)
  DOT_TYPE=$(echo "$STYLE_JSON" | grep -o '"dot_type":"[^"]*"' | cut -d'"' -f4)
  SQ_TYPE=$(echo "$STYLE_JSON" | grep -o '"sq_type":"[^"]*"' | cut -d'"' -f4)
  CORNER=$(echo "$STYLE_JSON" | grep -o '"corner":"[^"]*"' | cut -d'"' -f4)
  BG=$(echo "$STYLE_JSON" | grep -o '"bg":"[^"]*"' | cut -d'"' -f4)
  NAME=$(echo "$STYLE_JSON" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)

  CURRENT_TYPE="STATIC"
  if [[ "$QR_TYPE" == "dynamic" ]] || { [[ "$QR_TYPE" == "mixed" ]] && (( i % 2 == 0 )); }; then
    CURRENT_TYPE="DYNAMIC"
  fi

  PAYLOAD=$(cat <<JSON
{
  "title": "BashStress #$(printf "%04d" "$i") - ${NAME} (${DOT_TYPE})",
  "type": "${CURRENT_TYPE}",
  "target_url": "https://example.com/bash-test/${i}",
  "design_config": {
    "content": "https://example.com/bash-test/${i}",
    "width": 350,
    "height": 350,
    "margin": 10,
    "dotsOptions": { "type": "${DOT_TYPE}", "color": "${DOTS}" },
    "cornersSquareOptions": { "type": "${SQ_TYPE}", "color": "${CORNER}" },
    "cornersDotOptions": { "type": "dot", "color": "${CORNER}" },
    "backgroundOptions": { "color": "${BG}" },
    "labelTop": { "enabled": true, "text": "SCAN ME #${i}", "fontSize": 14, "fontWeight": "bold", "color": "${DOTS}", "align": "center" },
    "labelBottom": { "enabled": true, "text": "POINTQR STRESS", "fontSize": 12, "fontWeight": "normal", "color": "${DOTS}", "align": "center" }
  }
}
JSON
)

  FAKE_IP="198.51.100.$(( (i % 250) + 1 ))"

  # Send QR create request
  HTTP_RES=$(curl -s -w "\n%{http_code}\n%{time_total}" -X POST "${BASE_URL}/v1/qrcodes" \
    -H "X-API-Key: ${API_KEY}" \
    -H "CF-Connecting-IP: ${FAKE_IP}" \
    -H "X-Forwarded-For: ${FAKE_IP}" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD")

  HTTP_CODE=$(echo "$HTTP_RES" | tail -n 2 | head -n 1)
  TOTAL_TIME=$(echo "$HTTP_RES" | tail -n 1)
  RESPONSE_BODY=$(echo "$HTTP_RES" | sed '$d' | sed '$d')

  if [[ "$HTTP_CODE" -eq 201 ]]; then
    CREATED_OK=$((CREATED_OK + 1))
    QR_ID=$(echo "$RESPONSE_BODY" | grep -o '"id":"[^"]*"' | head -n 1 | cut -d'"' -f4)
    SHORT_CODE=$(echo "$RESPONSE_BODY" | grep -o '"short_code":"[^"]*"' | head -n 1 | cut -d'"' -f4 || echo "")

    CELERY_MSG=""
    if [[ "$EXPORT_JOBS" -eq 1 ]] && [[ -n "$QR_ID" ]]; then
      EXP_RES=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/v1/qrcodes/${QR_ID}/export/async?format=${EXPORT_FMT}" \
        -H "X-API-Key: ${API_KEY}" \
        -H "CF-Connecting-IP: ${FAKE_IP}")
      EXP_CODE=$(echo "$EXP_RES" | tail -n 1)
      if [[ "$EXP_CODE" -eq 202 ]]; then
        CELERY_OK=$((CELERY_OK + 1))
        CELERY_MSG=" | ${MAGENTA}CELERY ${EXPORT_FMT^^} QUEUED${NC}"
      else
        CELERY_MSG=" | ${RED}CELERY ERR (${EXP_CODE})${NC}"
      fi
    fi

    echo -e "[$(printf "%03d" "$i")/$(printf "%03d" "$COUNT")] ${GREEN}CREATE OK${NC} (${TOTAL_TIME}s) | ${NAME} (${DOT_TYPE})${CELERY_MSG}"
  else
    CREATED_FAIL=$((CREATED_FAIL + 1))
    echo -e "[$(printf "%03d" "$i")/$(printf "%03d" "$COUNT")] ${RED}FAILED (${HTTP_CODE})${NC} | Response: ${RESPONSE_BODY}"
  fi
done

END_TIME=$(date +%s)
DURATION=$(( END_TIME - START_TIME ))

echo -e "\n${CYAN}========================================================================${NC}"
echo -e "${BOLD}${CYAN}  STRESS TEST COMPLETED IN ${DURATION}s${NC}"
echo -e "${CYAN}========================================================================${NC}"
echo -e " QR Codes Created : ${GREEN}${CREATED_OK}/${COUNT}${NC}"
echo -e " Failures         : $([[ $CREATED_FAIL -gt 0 ]] && echo -e "${RED}${CREATED_FAIL}${NC}" || echo -e "0")"
if [[ "$EXPORT_JOBS" -eq 1 ]]; then
  echo -e " Celery Tasks     : ${MAGENTA}${CELERY_OK}/${COUNT} enqueued to 'qr_export'${NC}"
fi
echo -e "${CYAN}========================================================================${NC}"
