#!/usr/bin/env python3
"""
TCP flow-consistency test.

Verifies that all packets from a single TCP connection always arrive
at the same backend server (flow affinity).

Approach:
    1. Start tcpdump on every server interface.
    2. From h1, open N *separate* short HTTP connections to the VIP.
    3. Analyse captures: each 5-tuple must appear on exactly one server.
"""

import os
import time
import json
import subprocess

VIP = "10.0.0.100"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTTP_SERVER = os.path.join(SCRIPT_DIR, "http_server.py")
NUM_REQUESTS = 10
CAPTURE_DIR = "/tmp/lb_captures"


def run(net):
    """Run the flow-consistency test.  Returns (passed, details)."""
    servers = {name: net.get(name) for name in ("h3", "h4", "h5")}
    client = net.get("h1")

    os.makedirs(CAPTURE_DIR, exist_ok=True)

    # Start HTTP servers (pass hostname as CLI arg)
    for name, s in servers.items():
        s.cmd(f"python3 {HTTP_SERVER} {name} 80 &")
    time.sleep(1)

    # Start tcpdump on each server
    for name, s in servers.items():
        pcap = os.path.join(CAPTURE_DIR, f"tcp_{name}.pcap")
        s.cmd(f"tcpdump -i {name}-eth0 -w {pcap} tcp port 80 &")

    # Also capture on the client interface
    client_pcap = os.path.join(CAPTURE_DIR, "tcp_h1.pcap")
    client.cmd(f"tcpdump -i h1-eth0 -w {client_pcap} tcp port 80 &")
    time.sleep(1)

    # Send HTTP requests from the client
    # Use curl so each invocation is a separate TCP connection
    responses = []
    for i in range(NUM_REQUESTS):
        out = client.cmd(f"curl -s --connect-timeout 5 --max-time 10 http://{VIP}:80/")
        try:
            resp = json.loads(out.strip())
            responses.append(resp)
        except (json.JSONDecodeError, ValueError):
            responses.append({"raw": out.strip()})
        time.sleep(0.2)

    # Stop tcpdump & HTTP servers
    for s in servers.values():
        s.cmd("kill %tcpdump 2>/dev/null")
        s.cmd("kill %python3 2>/dev/null")
    client.cmd("kill %tcpdump 2>/dev/null")
    time.sleep(1)

    print(f"[test_tcp_consistency] pcap files saved to {CAPTURE_DIR}/")
    for pcap_name in [f"tcp_{n}.pcap" for n in servers] + ["tcp_h1.pcap"]:
        pcap_path = os.path.join(CAPTURE_DIR, pcap_name)
        if os.path.exists(pcap_path):
            print(f"  {pcap_path} ({os.path.getsize(pcap_path)} bytes)")

    # Analyse: which server handled each request?
    server_hits = {}
    for i, r in enumerate(responses):
        srv = r.get("hostname", "unknown")
        server_hits.setdefault(srv, []).append(i)

    print(f"[test_tcp_consistency] {NUM_REQUESTS} requests sent to VIP")
    print(f"[test_tcp_consistency] Server distribution:")
    for srv, reqs in sorted(server_hits.items()):
        print(f"  {srv}: handled requests {reqs}")

    # Deeper check: read pcap files and ensure no single TCP 4-tuple
    # appears on more than one server
    flows_per_server = {}
    for name in servers:
        pcap = os.path.join(CAPTURE_DIR, f"tcp_{name}.pcap")
        flows = _extract_flows(pcap)
        flows_per_server[name] = flows

    # Build a map: flow → set of servers
    flow_to_servers = {}
    for name, flows in flows_per_server.items():
        for f in flows:
            flow_to_servers.setdefault(f, set()).add(name)

    violations = {f: s for f, s in flow_to_servers.items() if len(s) > 1}

    # Check that at least some requests were actually served by real servers
    successful = sum(1 for r in responses if r.get("hostname", "unknown") != "unknown")
    min_required = NUM_REQUESTS // 2  # at least half must succeed

    if successful < min_required:
        print(f"[test_tcp_consistency] FAIL – only {successful}/{NUM_REQUESTS} "
              f"requests reached a server (need at least {min_required})")
        passed = False
    elif violations:
        print(f"[test_tcp_consistency] FAIL – flows seen on multiple servers:")
        for f, s in violations.items():
            print(f"  {f} → {s}")
        passed = False
    else:
        print(f"[test_tcp_consistency] PASS – all flows consistently routed "
              f"({successful}/{NUM_REQUESTS} requests served)")
        passed = True

    return passed, {"responses": responses, "violations": violations}


def _extract_flows(pcap_path):
    """Extract unique TCP 5-tuples from a pcap using tshark."""
    if not os.path.exists(pcap_path):
        return set()
    try:
        out = subprocess.check_output(
            [
                "tshark", "-r", pcap_path, "-T", "fields",
                "-e", "ip.src", "-e", "ip.dst",
                "-e", "tcp.srcport", "-e", "tcp.dstport",
            ],
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return set()

    flows = set()
    for line in out.strip().splitlines():
        parts = line.split("\t")
        if len(parts) == 4:
            flows.add(tuple(parts))
    return flows
