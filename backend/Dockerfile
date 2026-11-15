# georgeai.dev Django API.
#
# Serves /api/auth/* only — nginx (georgeai-web) stays the edge and keeps
# serving the design-tool export, because that path is fast, proven, and has
# nothing to gain from going through Python. See deploy/nginx.conf.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# psycopg[binary] ships its own libpq, so no build toolchain is needed here.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# collectstatic needs the settings to import, which needs an env. These are
# throwaway build-time values — the real ones arrive via env_file at runtime.
RUN SECRET_KEY=build-only \
    DATABASE_URL=postgres://u:p@127.0.0.1:5432/db \
    python manage.py collectstatic --noinput

RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

EXPOSE 8000

# Migrations run before gunicorn binds the port, so no request can reach code
# whose tables don't exist yet (e.g. bootstrap querying a new model mid-deploy).
# 3 workers is right for a 1-vCPU share; the access log goes to stdout so
# `docker logs` is the single place to look. gthread, not sync: console replies
# stream as SSE for minutes (DeepSeek Reasoner, long Opus answers). A sync
# worker would be killed at --timeout mid-stream and block a whole process per
# open stream; gthread workers keep heartbeating while threads stream.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers 3 --worker-class gthread --threads 8 --timeout 120 --access-logfile - --error-logfile -"]
