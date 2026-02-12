#!/usr/bin/env python3
"""
TCP bandwidth test using iperf.

Starts iperf servers on backend hosts, then runs iperf clients from h1 and h2
simultaneously targeting the VIP.  Each client's flow is hashed to a different
backend server, so both should achieve ~500 kbit/s (the per-server link cap).

Configuration (VIP, server list) is imported from controller.py.
"""

import re
import time
import threading

from controller import VIP, SERVERS, CLIENTS


DURATION = 10  # seconds


def _run_client(client, vip, duration, results, name):
    """Run iperf client and store parsed bandwidth in results dict."""
    out = client.cmd(f"iperf -c {vip} -t {duration}")
    print(f"[test_iperf] {name}:\n{out}")
    m = re.search(r"([\d.]+)\s+(K|M|G)?bits/sec", out)
    if m:
        bw = float(m.group(1))
        unit = m.group(2) or ""
        if unit == "K":
            bw /= 1000
        elif unit == "G":
            bw *= 1000
        results[name] = bw  # Mbit/s
    else:
        results[name] = 0.0


def run(net):
    """Run the iperf bandwidth test.  Returns (passed, results)."""
    server_names = [f"h{s['port']}" for s in SERVERS]
    servers = [net.get(name) for name in server_names]
    client_names = [c["name"] for c in CLIENTS]
    clients = [net.get(name) for name in client_names]

    # Start iperf servers
    for s in servers:
        s.cmd("iperf -s &")
    time.sleep(1)

    # Run iperf clients simultaneously
    results = {}
    threads = []
    for c, name in zip(clients, client_names):
        t = threading.Thread(target=_run_client, args=(c, VIP, DURATION, results, name))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Cleanup
    for s in servers:
        s.cmd("kill %iperf 2>/dev/null")

    total = sum(results.values())
    results["aggregate"] = total

    print(f"\n[test_iperf] Results (Mbit/s):")
    for k, v in results.items():
        print(f"  {k:12s}: {v:.3f}")

    # Check that every client achieved non-zero bandwidth
    # (if the controller isn't configured, traffic won't reach the servers)
    client_bws = {k: v for k, v in results.items() if k != "aggregate"}
    all_connected = all(bw > 0 for bw in client_bws.values())
    passed = all_connected and len(client_bws) > 0

    if passed:
        print(f"[test_iperf] PASS – all clients achieved bandwidth through VIP")
    else:
        failed = [k for k, v in client_bws.items() if v <= 0]
        print(f"[test_iperf] FAIL – clients with zero bandwidth: {failed}")

    return passed, results
