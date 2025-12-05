#!/bin/bash
# Entrypoint script for hub_auth Docker container

set -e

echo "Waiting for PostgreSQL..."
while ! nc -z $DATABASE_HOST $DATABASE_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser if it doesn't exist..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123');
    print('Superuser created: admin/admin123');
else:
    print('Superuser already exists');
" || true

exec "$@"

# Start Nginx in the background
echo "Starting Nginx..."
nginx -g "daemon on;" &

# Start Gunicorn (exec replaces the shell process)
echo "Starting Gunicorn..."
exec "$@"
