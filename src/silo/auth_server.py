"""
Browser-based localhost auth server for secure token entry.
Follows the industry-standard pattern used by GitHub CLI, Stripe CLI, gcloud, etc.
The token never touches the terminal, stdout, or LLM context.
"""
import http.server
import json
import socket
import threading
import urllib.parse
import webbrowser
from pathlib import Path

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _load_template(name: str) -> str:
    """Load an HTML template from the templates directory."""
    return (_TEMPLATE_DIR / name).read_text(encoding="utf-8")


def _find_free_port() -> int:
    """Find a random available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def prompt_via_browser(key_name: str) -> str | None:
    """
    Opens a browser window with a local auth page for the user to enter a token.
    Returns the token string, or None if the user closed the browser / timed out.
    """
    result = {"token": None}
    port = _find_free_port()
    got_token = threading.Event()

    class AuthHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            html = _load_template("auth.html").replace("{key_name}", key_name)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())

        def do_POST(self):
            if self.path == "/submit":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                try:
                    data = json.loads(body)
                    result["token"] = data.get("token")
                except (json.JSONDecodeError, KeyError):
                    pass

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok": true}')

                # Signal the main loop to stop
                got_token.set()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # Suppress request logging to avoid leaking info to stdout

    server = http.server.HTTPServer(('127.0.0.1', port), AuthHandler)
    server.timeout = 1  # Check for token every second
    url = f"http://127.0.0.1:{port}/?key={urllib.parse.quote(key_name)}"

    webbrowser.open(url)

    # Poll-based loop: handle requests until token is submitted
    while not got_token.is_set():
        server.handle_request()

    server.server_close()
    return result.get("token")
