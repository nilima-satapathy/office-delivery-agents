"""Serve the manager demo. Default port is 8877."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app import dispatch


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._send("GET", b"")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        self._send("POST", self.rfile.read(length) if length else b"")

    def _send(self, method, body):
        status, content_type, payload = dispatch(method, self.path, body)
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        print(f"[demo] {self.address_string()} {fmt % args}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8877)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Demo ready at http://127.0.0.1:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
