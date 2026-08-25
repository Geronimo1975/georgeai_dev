---
name: georgeai-backend
description: Work on the Django backend (auth API, serve_frontend, accounts app). Use for backend dev, running tests, migrations, or anything touching backend/.
---

# Django backend workflow

Venv lives at `backend/.venv` (gitignored). Shell state does not persist between
tool calls — call the venv binaries directly:

```bash
cd backend
.venv/bin/python manage.py test accounts     # tests (single: accounts.tests.ClassName.test_name)
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

## Database (no local DB!)

PostgreSQL lives in the shared `gethub-postgres` container on the VPS.
Local dev needs an SSH tunnel on port **5434** (5433 is taken by the n8n tunnel):

```bash
nc -z 127.0.0.1 5434 || {
  IP=$(ssh macbook-air "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' gethub-postgres")
  ssh -f -N -L 5434:$IP:5432 macbook-air
}
```

`backend/.env` already points `DATABASE_URL` at `127.0.0.1:5434/georgeai`.

## Architecture invariants — do not break

- `serve_frontend` (backend/backend/views.py) returns files from
  `frontend/template/` **verbatim as FileResponse — never through the Django
  template engine**. The export's `{{ }}` placeholders are rendered client-side
  by `support.js` and collide with Django template syntax.
- Custom email-based `User` (`AUTH_USER_MODEL = accounts.User`, no username).
- DRF: SessionAuthentication only, JSON renderer only, at `/api/auth/{signup,login,logout,me}`.
- `CSRF_COOKIE_HTTPONLY = False` is **intentional** — `serve_frontend` is
  `@ensure_csrf_cookie` so `auth.js` can echo the token as `X-CSRFToken`.
- `backend/assets/auth.js` hooks the export's signin modal *by structure*
  (input type + position, event delegation) — the export's fields have no ids
  and regenerate every deploy. It must degrade gracefully when `/api/auth/*`
  is absent.
- All config via `backend/.env` (django-environ); no secrets in source.

## How it is deployed

The backend is **live**, not hypothetical: `./deploy.sh` builds it and brings up
the `georgeai-app` container alongside nginx, then runs
`manage.py migrate --noinput` and fails the deploy if it errors.

- `georgeai-app` is **not routed by Traefik**. Only `georgeai-web` (nginx) is
  public; it proxies `/api/` to `georgeai-app:8000` over the shared network.
  A broken backend deploy therefore cannot take the site down.
- The `location /api/` block is declared **before** `location /` on purpose —
  otherwise API calls fall through to `try_files` and get answered with an HTML
  404, which is what made `auth.js` throw a `SyntaxError` when nothing served
  `/api/` at all.
- nginx sets `X-Forwarded-Proto https` on that proxy pass; Django's
  `SECURE_PROXY_SSL_HEADER` reads it, which is what stops `SECURE_SSL_REDIRECT`
  from bouncing every API call.
- Runtime env for the container comes from `deploy/backend.env` on the VPS
  (not `backend/.env`, which is local dev only).

Health check used by the deploy: `/api/auth/me` must return JSON containing
`authenticated`.
