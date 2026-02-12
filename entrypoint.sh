#!/usr/bin/env bash
#
# entrypoint.sh — runs inside the Docker container.
# Starts OVS, launches Mininet, programs the switch, and runs tests.
#

CYAN="\033[0;36m"
GREEN="\033[0;32m"
RED="\033[0;31m"
NC="\033[0m"

banner() {
    echo -e "\n${CYAN}──────────────────────────────────────────${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}──────────────────────────────────────────${NC}"
}

# ── 1. Start Open vSwitch ──────────────────────────────────────────
banner "Starting Open vSwitch"
service openvswitch-switch start
sleep 2
ovs-vsctl show
echo ""

# ── 2. Run topology + controller setup + tests via Python ──────────
banner "Starting Mininet, programming switch, and running tests"
timeout 120 python3 /app/run_all_tests.py || echo "Test runner exited with code $?"

# ── 3. Summary ──────────────────────────────────────────────────────
banner "Results"
printf "%-25s %s\n" "Test" "Status"
printf "%-25s %s\n" "-------------------------" "------"

for test in arp iperf tcp; do
    file="/tmp/result_${test}"
    if [ -f "$file" ]; then
        status=$(cat "$file")
        if [[ "$status" == "PASS" || "$status" == "DONE" ]]; then
            printf "%-25s ${GREEN}%s${NC}\n" "$test" "$status"
        else
            printf "%-25s ${RED}%s${NC}\n" "$test" "$status"
        fi
    else
        printf "%-25s ${RED}%s${NC}\n" "$test" "NOT RUN"
    fi
done

service openvswitch-switch stop 2>/dev/null || true
echo -e "\nDone."
