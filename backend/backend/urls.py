"""URL configuration for georgeai.dev.

/admin/ is handled by Django; everything else is served from the static
design export (frontend/template/) via the catch-all.
"""
from django.contrib import admin
from django.urls import include, path, re_path

from .views import auth_js, serve_frontend

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("auth.js", auth_js),
    # catch-all: serve the design export at the site root (keep this last)
    re_path(r"^(?P<path>.*)$", serve_frontend),
]
