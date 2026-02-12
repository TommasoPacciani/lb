#!/usr/bin/env python3
"""
Model-solution controller: round-robin load balancer using raw OVS commands.

This script programs the OVS switch using ovs-ofctl and configures static ARP on clients.

Milestones implemented
----------------------
1. ARP handling   – static ARP entries on clients mapping VIP → LB MAC.
2. Forward path   – OFPGT_SELECT group table, one bucket per server.
3. Reverse path   – per-server flow rules rewriting src IP/MAC back to VIP.
4. L2 forwarding  – basic flood rule for non-VIP traffic.

Usage (inside Mininet, after topology is up):
    python3 controller.py
"""

import subprocess
import sys

# ── Configuration ───────────────────────────────────────────────────
SWITCH = "s1"
VIP = "10.0.0.100"
LB_MAC = "00:00:00:00:00:ff"
GROUP_ID = 1

# Ports are assigned by Mininet in the order links are created:
#   h1→s1 = port 1, h2→s1 = port 2, h3→s1 = port 3, h4→s1 = port 4, h5→s1 = port 5
SERVERS = [
    {"ip": "10.0.0.3", "mac": "00:00:00:00:00:03", "port": 3},
    {"ip": "10.0.0.4", "mac": "00:00:00:00:00:04", "port": 4},
    {"ip": "10.0.0.5", "mac": "00:00:00:00:00:05", "port": 5},
]

CLIENTS = [
    {"name": "h1", "ip": "10.0.0.1"},
    {"name": "h2", "ip": "10.0.0.2"},
]


def run(cmd, check=True):
    """Run a shell command and print it."""
    if isinstance(cmd, str):
        parts = cmd.split()
    else:
        parts = cmd
    print(f"  $ {' '.join(parts)}")
    try:
        result = subprocess.run(parts, capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        print(f"    TIMEOUT after 10s")
        if check:
            sys.exit(1)
        return None
    if result.stdout.strip():
        print(f"    {result.stdout.strip()}")
    if result.returncode != 0 and check:
        print(f"    ERROR: {result.stderr.strip()}")
        sys.exit(1)
    return result


def setup_switch():
    """Program the OVS switch with group table and flow rules."""

    # Ensure OF1.3
    run(f"ovs-vsctl set bridge {SWITCH} protocols=OpenFlow13")

    # Clear existing flows and groups
    run(f"ovs-ofctl -O OpenFlow13 del-flows {SWITCH}")
    run(f"ovs-ofctl -O OpenFlow13 del-groups {SWITCH}")

    pass



def setup_static_arp(net=None):
    """Add static ARP entries on clients mapping VIP → LB MAC.
    """
    pass
def setup(net=None):
    """Full setup: program switch + configure ARP."""
    print("=" * 50)
    print("  Programming OVS switch")
    print("=" * 50)
    setup_switch()

    print("\n" + "=" * 50)
    print("  Configuring static ARP on clients")
    print("=" * 50)
    setup_static_arp(net)

    print("\n✓ Load balancer setup complete.\n")


if __name__ == "__main__":
    setup()
