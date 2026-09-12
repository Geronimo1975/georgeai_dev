import http.server
import socketserver
import subprocess
import threading
from pathlib import Path

import pytest

import build

ROOT = Path(__file__).resolve().parents[1]

SITE_DIR = None


class SiteHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(SITE_DIR), **k)

    def do_GET(self):
        if self.path.startswith("/api/"):
            # mirrors backend/accounts/views.py:MeView for an anonymous visitor
            body = b'{"authenticated": false}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, *a):
        pass


@pytest.mark.browser
def test_browser_suite(tmp_path):
    global SITE_DIR
    out = tmp_path / "site"
    build.build(out)
    SITE_DIR = out
    with socketserver.TCPServer(("127.0.0.1", 0), SiteHandler) as srv:
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            proc = subprocess.run(["node", str(ROOT / "tests" / "browser" / "check_pages.mjs"), f"http://127.0.0.1:{port}"],
                                  capture_output=True, text=True, timeout=600)
        finally:
            srv.shutdown()
    print(proc.stdout)
    assert proc.returncode == 0, proc.stdout + proc.stderr
