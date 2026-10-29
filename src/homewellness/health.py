"""Tiny HTTP health endpoint for the container health check.

NOTE: Phase 3 can serve the same path from the FastAPI application.
"""

import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def start_health_server(
    port: int, is_ready: Callable[[], bool] = lambda: True
) -> ThreadingHTTPServer:
    """Serve GET /healthz. Answer 200 when ready and 503 when not."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - name required by the base class
            if self.path != "/healthz":
                status, body = 404, b"not found"
            elif is_ready():
                status, body = 200, b"ok"
            else:
                status, body = 503, b"not ready"
            self.send_response(status)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            return  # Keep container logs quiet.

    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
