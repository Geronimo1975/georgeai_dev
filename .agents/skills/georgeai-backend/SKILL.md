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
