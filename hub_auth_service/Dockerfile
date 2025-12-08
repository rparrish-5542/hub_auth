# Employee Management Service Dockerfile
FROM python:3.14-slim-trixie

# ----------------------------
# Environment Variables
# ----------------------------
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STATIC_ROOT=/app/staticfiles

# ----------------------------
# Install system dependencies
# ----------------------------
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    netcat-traditional \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------
# Create app directories
# ----------------------------
WORKDIR /app
RUN mkdir -p /app/staticfiles /app/logs /app/run

# ----------------------------
# Copy Python requirements
# ----------------------------
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install gunicorn

# ----------------------------
# Copy application code
# ----------------------------
COPY . /app/

# ----------------------------
# Collect static files
# ----------------------------
RUN python manage.py collectstatic --noinput --clear || true

# ----------------------------
# Copy Nginx config
# ----------------------------
COPY default.conf /etc/nginx/conf.d/default.conf

# ----------------------------
# Copy entrypoint script
# ----------------------------
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# ----------------------------
# Create non-root user at the end
# ----------------------------
# RUN groupadd -r appuser && useradd -r -g appuser appuser \
   # && chown -R appuser:appuser /app

# Switch to non-root user (last step)
# USER appuser

# ----------------------------
# Expose HTTP port only
# ----------------------------
EXPOSE 80

# ----------------------------
# Entrypoint and CMD
# ----------------------------
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "employee_manage.wsgi:application", "--bind=127.0.0.1:8001", "--workers=3", "--timeout=60", "--access-logfile=-", "--error-logfile=-"]

