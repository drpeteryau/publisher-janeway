#!/bin/bash
# Container entrypoint for Coolify deployments.
set -euo pipefail

cd /vol/janeway/src

if [ "${1:-web}" = "web" ]; then
    # Wait for the database to accept connections.
    python - <<'PY'
import os, socket, time, sys
host, port = os.environ["DB_HOST"], int(os.environ.get("DB_PORT", "5432"))
for _ in range(60):
    try:
        socket.create_connection((host, port), 2).close(); break
    except OSError:
        time.sleep(2)
else:
    sys.exit("database %s:%s unreachable" % (host, port))
PY

    python manage.py migrate --noinput

    # First boot only: create press + journal + default settings.
    if [ "${JANEWAY_AUTO_INSTALL:-true}" = "true" ]; then
        python manage.py shell -c "import sys; from press.models import Press; sys.exit(0 if Press.objects.exists() else 1)" \
            || python manage.py install_janeway --use-defaults
    fi

    # Optional first admin account (uses DJANGO_SUPERUSER_* variables).
    if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
        python manage.py createsuperuser --noinput \
            --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.org}" 2>/dev/null || true
    fi

    python manage.py collectstatic --noinput
    python manage.py build_assets || true

    exec gunicorn core.wsgi_coolify:application \
        --bind 0.0.0.0:8000 \
        --workers "${GUNICORN_WORKERS:-3}" \
        --timeout "${GUNICORN_TIMEOUT:-120}" \
        --access-logfile - \
        --forwarded-allow-ips="*"
fi

exec python manage.py "$@"
