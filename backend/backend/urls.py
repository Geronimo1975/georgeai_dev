"""URL configuration for georgeai.dev.

/admin/ is handled by Django; everything else is served from the static
design export (frontend/template/) via the catch-all.
"""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path

from console import auth_views as console_auth
from console import urls as console_urls

from .views import auth_js, serve_frontend

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    # GeorgeAI Console — JSON/SSE API + the SPA shell (all /console/* paths)
    path("api/console/v1/", include((console_urls.api, "console_api"))),
    # Passwordless: email -> one-time code (console/auth_views.py). Staff also
    # have password login at /admin/, whose session opens the console too.
    path("console/login/", console_auth.login_email, name="console_login"),
    path("console/login/code/", console_auth.login_code, name="console_login_code"),
    path("console/logout/", auth_views.LogoutView.as_view(next_page="/console/login/"), name="console_logout"),
    path("console/", include((console_urls.pages, "console"))),
    path("auth.js", auth_js),
    # catch-all: serve the design export at the site root (keep this last)
    re_path(r"^(?P<path>.*)$", serve_frontend),
]
