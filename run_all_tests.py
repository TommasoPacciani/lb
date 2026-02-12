#!/usr/bin/env python3
"""
run_all_tests.py — launched by entrypoint.sh inside the container.

Creates the Mininet topology, waits for it to stabilise, then runs
each test in sequence and writes result files to /tmp.
"""

import signal
import sys
import time

# ── Timeout helper ──────────────────────────────────────────────────
GLOBAL_TIMEOUT = 120       # max seconds for the entire run
SETUP_TIMEOUT  = 20        # max seconds for controller.setup()
TEST_TIMEOUT   = 60        # max seconds per individual test

class TimeoutError(Exception):
    pass

def _timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

signal.signal(signal.SIGALRM, _timeout_handler)

sys.path.insert(0, "/app")

from topo import build_topology
import controller
import test_arp
import test_iperf
import test_tcp_consistency


def write_result(name, value):
    with open(f"/tmp/result_{name}", "w") as f:
        f.write(value)


def main():
    print("Building topology...")
    net = build_topology()
    net.start()
    print("Topology started, waiting for it to stabilise...")
    time.sleep(3)

    # Program the switch and set static ARP
    print("\nProgramming load balancer...")
    try:
        signal.alarm(SETUP_TIMEOUT)
        controller.setup(net)
        signal.alarm(0)
    except TimeoutError:
        print(f"[setup] TIMEOUT after {SETUP_TIMEOUT}s")
        net.stop()
        sys.exit(1)
    time.sleep(2)

    # ── ARP test ────────────────────────────────────────────────────
    print("\n>>> Running ARP test...")
    try:
        signal.alarm(TEST_TIMEOUT)
        passed, _ = test_arp.run_on_host(net, "h1")
        signal.alarm(0)
        write_result("arp", "PASS" if passed else "FAIL")
    except TimeoutError:
        print(f"[test_arp] TIMEOUT after {TEST_TIMEOUT}s")
        write_result("arp", "FAIL")
    except Exception as e:
        print(f"[test_arp] ERROR: {e}")
        write_result("arp", "FAIL")

    # ── iperf bandwidth test ────────────────────────────────────────
    print("\n>>> Running iperf bandwidth test...")
    try:
        signal.alarm(TEST_TIMEOUT)
        passed, _ = test_iperf.run(net)
        signal.alarm(0)
        write_result("iperf", "PASS" if passed else "FAIL")
    except TimeoutError:
        print(f"[test_iperf] TIMEOUT after {TEST_TIMEOUT}s")
        write_result("iperf", "FAIL")
    except Exception as e:
        print(f"[test_iperf] ERROR: {e}")
        write_result("iperf", "FAIL")

    # ── TCP consistency test ────────────────────────────────────────
    print("\n>>> Running TCP consistency test...")
    try:
        signal.alarm(TEST_TIMEOUT)
        passed, _ = test_tcp_consistency.run(net)
        signal.alarm(0)
        write_result("tcp", "PASS" if passed else "FAIL")
    except TimeoutError:
        print(f"[test_tcp_consistency] TIMEOUT after {TEST_TIMEOUT}s")
        write_result("tcp", "FAIL")
    except Exception as e:
        print(f"[test_tcp_consistency] ERROR: {e}")
        write_result("tcp", "FAIL")

    print("\nStopping topology...")
    net.stop()


if __name__ == "__main__":
    main()
