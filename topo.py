#!/usr/bin/env python3
"""
Mininet topology for the load-balancer assignment.

Topology
--------
        h1 ──┐                ┌── h3 (server, 500 kbit link)
              ├── s1 (OVS) ──┼── h4 (server, 500 kbit link)
        h2 ──┘                └── h5 (server, 500 kbit link)

VIP: 10.0.0.100   LB MAC: 00:00:00:00:00:ff
Hosts h1–h2 are clients, h3–h5 are backend servers.
Client–switch links are uncapped; server–switch links are 500 kbit/s.
"""

from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.cli import CLI


# ── Topology parameters ────────────────────────────────────────────
VIP = "10.0.0.100"
LB_MAC = "00:00:00:00:00:ff"
SERVER_BW = 0.5  # Mbit/s  (= 500 kbit/s)

CLIENTS = {
    "h1": {"ip": "10.0.0.1/24", "mac": "00:00:00:00:00:01"},
    "h2": {"ip": "10.0.0.2/24", "mac": "00:00:00:00:00:02"},
}

SERVERS = {
    "h3": {"ip": "10.0.0.3/24", "mac": "00:00:00:00:00:03"},
    "h4": {"ip": "10.0.0.4/24", "mac": "00:00:00:00:00:04"},
    "h5": {"ip": "10.0.0.5/24", "mac": "00:00:00:00:00:05"},
}


def build_topology():
    """Create and return a Mininet network with the LB topology."""

    setLogLevel("info")

    net = Mininet(
        switch=OVSSwitch,
        controller=RemoteController,
        link=TCLink,
        autoSetMacs=False,
    )

    # Controller
    # net.addController("c0", ip="127.0.0.1", port=6653)

    # Switch – OpenFlow 1.3
    s1 = net.addSwitch("s1", protocols="OpenFlow13")

    # Clients
    hosts = {}
    for name, cfg in CLIENTS.items():
        h = net.addHost(name, ip=cfg["ip"], mac=cfg["mac"])
        net.addLink(h, s1)  # uncapped
        hosts[name] = h

    # Servers (bandwidth-limited links)
    for name, cfg in SERVERS.items():
        h = net.addHost(name, ip=cfg["ip"], mac=cfg["mac"])
        net.addLink(h, s1, bw=SERVER_BW)
        hosts[name] = h

    return net


# ── Main ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    net = build_topology()
    net.start()

    print("\n" + "=" * 60)
    print("  Load-Balancer topology is up.")
    print(f"  VIP = {VIP}   LB MAC = {LB_MAC}")
    print("  Clients : " + ", ".join(CLIENTS))
    print("  Servers : " + ", ".join(SERVERS))
    print("=" * 60 + "\n")

    CLI(net)
    net.stop()
