import http.server
import json
import socket
import threading
import urllib.parse
import webbrowser
from pathlib import Path
from typing import Optional
import secrets as secrets_lib
import html

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _load_template(name: str) -> str:
    """Load an HTML template from the templates directory."""
    return (_TEMPLATE_DIR / name).read_text(encoding="utf-8")


def _find_free_port() -> int:
    """Find a random available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


def prompt_via_browser(key_name: str) -> Optional[str]:
    """
    Opens a browser window with a local auth page for the user to enter a token.
    Uses a secure session nonce to prevent CSRF.
    """
    session_nonce = secrets_lib.token_urlsafe(16)
    result = {"token": None}
    port = _find_free_port()
    got_token = threading.Event()

    class AuthHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed_url = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed_url.query)
            
            # CSRF Protection: Nonce must match
            if params.get("nonce", [None])[0] != session_nonce:
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b"Forbidden: Invalid or missing session nonce.")
                return

            # XSS Protection: Escape variable content
            safe_key = html.escape(key_name)
            content = _load_template("auth.html").replace("{key_name}", safe_key)
            # Inject nonce into the form via a hidden field or similar if needed
            # In our simple case, we just expect it back in the POST
            
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode())

        def do_POST(self):
            if self.path == "/submit":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                try:
                    data = json.loads(body)
                    # CSRF Protection: Check nonce in POST body
                    if data.get("nonce") != session_nonce:
                        self.send_response(403)
                        self.end_headers()
                        return

                    result["token"] = data.get("token")
                except (json.JSONDecodeError, KeyError):
                    pass

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok": true}')

                got_token.set()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass

    server = http.server.HTTPServer(('127.0.0.1', port), AuthHandler)
    server.timeout = 1
    url = f"http://127.0.0.1:{port}/?nonce={session_nonce}&key={urllib.parse.quote(key_name)}"

    webbrowser.open(url)

    while not got_token.is_set():
        server.handle_request()

    server.server_close()
    return result.get("token")


def prompt_approval_via_browser(skill_name: str, cmd_name: str, args: dict) -> bool:
    """
    Opens a browser window for the user to approve a critical action.
    Uses session nonce for CSRF protection.
    """
    session_nonce = secrets_lib.token_urlsafe(16)
    result = {"approved": False}
    port = _find_free_port()
    decided = threading.Event()

    class ApprovalHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            parsed_url = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed_url.query)
            
            if params.get("nonce", [None])[0] != session_nonce:
                self.send_response(403)
                self.end_headers()
                return

            # XSS Protection: Escape all dynamic content
            safe_skill = html.escape(skill_name)
            safe_cmd = html.escape(cmd_name)
            args_json = html.escape(json.dumps(args, indent=2))

            content = (_load_template("approval.html")
                    .replace("{skill_name}", safe_skill)
                    .replace("{cmd_name}", safe_cmd)
                    .replace("{args_json}", args_json))
            
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content.encode())

        def do_POST(self):
            if self.path == "/respond":
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                try:
                    data = json.loads(body)
                    if data.get("nonce") != session_nonce:
                        self.send_response(403)
                        self.end_headers()
                        return
                    result["approved"] = data.get("approved", False)
                except (json.JSONDecodeError, KeyError):
                    pass

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok": true}')

                decided.set()
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass

    server = http.server.HTTPServer(('127.0.0.1', port), ApprovalHandler)
    server.timeout = 1
    url = f"http://127.0.0.1:{port}/?nonce={session_nonce}"

    webbrowser.open(url)

    while not decided.is_set():
        server.handle_request()

    server.server_close()
    return result["approved"]
