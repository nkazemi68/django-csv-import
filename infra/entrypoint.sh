#!/usr/bin/env bash
set -e

until pg_isready -h "${DB_HOST:-db}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" ; do
  echo "waiting for db..."
  sleep 1
done

# optional migrate
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Running migrations..."
  python manage.py migrate --noinput
fi

# optional collectstatic
if [ "${RUN_COLLECTSTATIC:-0}" = "1" ]; then
  echo "Collectstatic..."
  python manage.py collectstatic --noinput
fi

# finally start the service (CMD will be applied after entrypoint)
exec "$@"
