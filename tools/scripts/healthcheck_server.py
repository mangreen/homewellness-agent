"""Placeholder HTTP health endpoint for Phase 1.

NOTE: Phase 3 replaces this script with the FastAPI application.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - name required by the base class
        status = 200 if self.path == "/healthz" else 404
        self.send_response(status)
        self.end_headers()
        self.wfile.write(b"ok" if status == 200 else b"not found")

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return  # Keep container logs quiet.


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
