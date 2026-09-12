import http.server
import socketserver
import subprocess
import threading
from pathlib import Path

import pytest

import build

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.browser
def test_browser_suite(tmp_path):
    out = tmp_path / "site"
    build.build(out)
    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(*a, directory=str(out), **k)
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as srv:
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
