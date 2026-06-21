"""
Serve the static design export (frontend/template/) at the site root.

The exported HTML uses {{ ... }} placeholders that support.js renders in the
browser. That syntax collides with Django's template engine, so these files are
returned verbatim as files — never rendered server-side.
"""
from pathlib import Path

from django.conf import settings
from django.core.exceptions import SuspiciousFileOperation
from django.http import FileResponse, Http404
from django.utils._os import safe_join
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def serve_frontend(request, path=""):
    """Map any URL path to a file inside FRONTEND_DIR; '/' -> index.html.

    Decorated with ensure_csrf_cookie so the SPA always receives a csrftoken
    cookie that auth.js can read and echo back as the X-CSRFToken header.
    """
    if path == "" or path.endswith("/"):
        path += "index.html"

    try:
        full = Path(safe_join(str(settings.FRONTEND_DIR), path))
    except SuspiciousFileOperation:
        raise Http404("Not found")

    if not full.is_file():
        raise Http404("Not found")

    return FileResponse(full.open("rb"))


def auth_js(request):
    """Serve the repo-owned auth bridge (injected into index.html by deploy.sh)."""
    path = settings.ASSETS_DIR / "auth.js"
    if not path.is_file():
        raise Http404("Not found")
    return FileResponse(path.open("rb"), content_type="text/javascript")
