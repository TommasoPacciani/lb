#!/usr/bin/env python3
"""
Minimal HTTP server for load-balancer backend hosts.

Returns a JSON body identifying which server handled the request.
Usage:
    python3 http_server.py <hostname> [port]
"""

import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"hostname": self.server.hostname})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, fmt, *args):
        pass


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <hostname> [port]", file=sys.stderr)
        sys.exit(1)
    hostname = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 80
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.hostname = hostname
    print(f"Backend HTTP server ({hostname}) listening on 0.0.0.0:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
