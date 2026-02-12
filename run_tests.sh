#!/usr/bin/env bash
#
# run_tests.sh — build a Docker container and run the full LB test suite.
#
# Usage:
#   ./run_tests.sh              # build + run all tests
#   ./run_tests.sh --shell      # build + drop into interactive shell
#
set -euo pipefail

IMAGE_NAME="lb-assignment"
CONTAINER_NAME="lb-runner"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ── Colours ─────────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

banner() { echo -e "\n${CYAN}══════════════════════════════════════════${NC}"; echo -e "${CYAN}  $1${NC}"; echo -e "${CYAN}══════════════════════════════════════════${NC}\n"; }

# ── Build ───────────────────────────────────────────────────────────
banner "Building Docker image: ${IMAGE_NAME}"
docker build -t "${IMAGE_NAME}" "${SCRIPT_DIR}"

# ── Run mode ────────────────────────────────────────────────────────
if [[ "${1:-}" == "--shell" ]]; then
    banner "Starting interactive shell"
    docker run --rm -it --privileged --entrypoint="" \
        --name "${CONTAINER_NAME}" \
        "${IMAGE_NAME}" bash
    exit 0
fi

# ── Run tests inside container ──────────────────────────────────────
banner "Running test suite inside container"
docker run --rm --privileged --entrypoint="" \
    --name "${CONTAINER_NAME}" \
    "${IMAGE_NAME}" \
    bash /app/entrypoint.sh
