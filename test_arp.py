#!/usr/bin/env python3
"""
ARP verification test.

Checks that:
1. arping to the VIP receives a reply.
2. The reply MAC is the LB's fake MAC (00:00:00:00:00:ff).

Captures pcap files in /tmp/lb_captures/ for debugging.
"""

import os
import subprocess
import sys
import time
import re

VIP = "10.0.0.100"
LB_MAC = "00:00:00:00:00:ff"
CAPTURE_DIR = "/tmp/lb_captures"


def run_on_host(net, host_name="h1"):
    """Run the ARP test from a Mininet host and return (passed, details)."""
    h = net.get(host_name)
    s1 = net.get("s1")

    os.makedirs(CAPTURE_DIR, exist_ok=True)

    # Start pcap capture on the client interface and on the switch
    host_pcap = os.path.join(CAPTURE_DIR, f"arp_{host_name}.pcap")
    switch_pcap = os.path.join(CAPTURE_DIR, "arp_s1.pcap")

    h.cmd(f"tcpdump -i {host_name}-eth0 -w {host_pcap} arp &")
    s1.cmd(f"tcpdump -i any -w {switch_pcap} arp &")
    time.sleep(1)  # let tcpdump start

    # Send a single ARP request
    out = h.cmd(f"arping -c 1 -w 5 {VIP}")
    print(f"[test_arp] arping output:\n{out}")

    # Check ARP table
    arp_table = h.cmd("arp -n")
    print(f"[test_arp] ARP table:\n{arp_table}")

    # Stop tcpdump
    time.sleep(1)  # let tcpdump flush
    h.cmd("kill %tcpdump 2>/dev/null")
    s1.cmd("kill %tcpdump 2>/dev/null")
    time.sleep(0.5)

    print(f"[test_arp] pcap files saved to {CAPTURE_DIR}/")
    for pcap in (host_pcap, switch_pcap):
        if os.path.exists(pcap):
            print(f"  {pcap} ({os.path.getsize(pcap)} bytes)")

    # Verify the VIP is in the ARP table with the LB MAC
    # arp -n output line looks like:  10.0.0.100  ether  00:00:00:00:00:ff  C  h1-eth0
    passed = False
    for line in arp_table.splitlines():
        if VIP in line and LB_MAC in line.lower():
            passed = True
            break

    return passed, arp_table


# def main():
#     """Standalone mode: run inside a host namespace (e.g. via `h1 python3 test_arp.py`)."""
#     out = subprocess.run(
#         ["arping", "-c", "1", "-w", "5", VIP],
#         capture_output=True, text=True,
#     )
#     print(f"[test_arp] arping stdout:\n{out.stdout}")
#     print(f"[test_arp] arping stderr:\n{out.stderr}")

#     arp_out = subprocess.run(["arp", "-n"], capture_output=True, text=True)
#     print(f"[test_arp] ARP table:\n{arp_out.stdout}")

#     passed = LB_MAC in arp_out.stdout.lower()
#     status = "PASS" if passed else "FAIL"
#     print(f"\n[test_arp] {status}")
#     sys.exit(0 if passed else 1)


# if __name__ == "__main__":
#     main()
