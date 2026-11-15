#!/usr/bin/env bash
# Local dev server for the Django backend + GeorgeAI Console.
#
# Uses a LOCAL SQLite database (backend/db.sqlite3, gitignored) so local work can
# never touch the production PostgreSQL behind the ssh tunnel. To work against
# Postgres instead, run manage.py directly with DATABASE_URL from backend/.env.
#
#   ./dev.sh            # migrate + runserver on :8000
#   PORT=8010 ./dev.sh
set -euo pipefail
cd "$(dirname "$0")"

export DATABASE_URL="sqlite:///db.sqlite3"   # relative → backend/db.sqlite3
export DEBUG=True
export SECURE_SSL_REDIRECT=False
export SESSION_COOKIE_SECURE=False
export CSRF_COOKIE_SECURE=False

# The venv lives OUTSIDE iCloud Drive: iCloud evicts files and lazily re-downloads
# them, which makes an in-repo .venv hang for minutes on import. Create it with:
#   python3.12 -m venv ~/.venvs/georgeai_dev && ~/.venvs/georgeai_dev/bin/pip install -r requirements.txt
VENV="${GEORGEAI_VENV:-$HOME/.venvs/georgeai_dev}"
PY="$VENV/bin/python"
[ -x "$PY" ] || PY=.venv/bin/python

"$PY" manage.py migrate --noinput
exec "$PY" manage.py runserver "127.0.0.1:${PORT:-8000}"
