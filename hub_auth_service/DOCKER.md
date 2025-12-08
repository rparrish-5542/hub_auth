# Hub Auth - Docker Deployment Guide

## Quick Start (Development)

### 1. Copy Environment File
```bash
cp .env.example .env
```

Edit `.env` and update with your Azure AD credentials:
```env
AZURE_AD_TENANT_ID=your-actual-tenant-id
AZURE_AD_CLIENT_ID=your-actual-client-id
AZURE_AD_CLIENT_SECRET=your-actual-client-secret
```

### 2. Build and Start Services
```bash
docker-compose up -d --build
```

### 3. Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### 4. Create Service Client
```bash
docker-compose exec web python manage.py shell
```

In the shell:
```python
from authentication.models import ServiceClient
import secrets

client = ServiceClient.objects.create(
    name='employee_manage',
    description='Employee management service',
    api_key=secrets.token_urlsafe(32),
    is_active=True
)
print(f"API Key: {client.api_key}")
exit()
```

### 5. Access Services
- **Hub Auth API**: http://localhost:8000/api/auth/
- **Admin Interface**: http://localhost:8000/admin/
- **Database**: localhost:5433 (external port)

## Production Deployment

### 1. Update Production Environment
Create `.env` file with production settings:
```env
DEBUG=False
SECRET_KEY=your-strong-secret-key-here
ALLOWED_HOSTS=hub-auth.yourdomain.com,localhost

DATABASE_NAME=hub_auth_db
DATABASE_USER=hub_auth_user
DATABASE_PASSWORD=strong-db-password-here
DATABASE_HOST=db
DATABASE_PORT=5432

AZURE_AD_TENANT_ID=your-tenant-id
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret

CORS_ALLOWED_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com
```

### 2. Deploy with Production Compose
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### 3. SSL/TLS Setup
For production, add SSL certificates to nginx configuration or use a reverse proxy like Traefik or Caddy.

## Docker Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f db
```

### Execute Commands
```bash
# Django management commands
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell

# Database backup
docker-compose exec db pg_dump -U myadmin hub_auth_db > backup.sql

# Database restore
docker-compose exec -T db psql -U myadmin hub_auth_db < backup.sql
```

### Stop Services
```bash
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build web
```

## Scaling

### Multiple Web Workers
Edit `docker-compose.yml`:
```yaml
web:
  deploy:
    replicas: 3
```

Or use docker-compose scale:
```bash
docker-compose up -d --scale web=3
```

## Monitoring

### Health Checks
```bash
# Web service health
curl http://localhost:8000/admin/login/

# Database health
docker-compose exec db pg_isready -U myadmin
```

### Resource Usage
```bash
docker stats
```

## Troubleshooting

### Database Connection Issues
```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec web python manage.py dbshell
```

### Migration Issues
```bash
# Reset migrations (development only)
docker-compose exec web python manage.py migrate authentication zero
docker-compose exec web python manage.py migrate
```

### Permission Issues
```bash
# Fix file permissions
docker-compose exec web chown -R $(id -u):$(id -g) /app/logs /app/staticfiles
```

## Network Configuration

### Connect Other Services
Other Docker services can connect to hub_auth via the network:

```yaml
# In another docker-compose.yml
services:
  employee_service:
    environment:
      - HUB_AUTH_URL=http://hub_auth_service:8000
    networks:
      - hub_auth_hub_auth_network

networks:
  hub_auth_hub_auth_network:
    external: true
```

## Backup and Restore

### Automated Backups
Add to crontab:
```bash
0 2 * * * docker-compose -f /path/to/docker-compose.yml exec -T db pg_dump -U myadmin hub_auth_db | gzip > /backups/hub_auth_$(date +\%Y\%m\%d).sql.gz
```

### Manual Backup
```bash
docker-compose exec db pg_dump -U myadmin hub_auth_db | gzip > hub_auth_backup.sql.gz
```

### Restore from Backup
```bash
gunzip -c hub_auth_backup.sql.gz | docker-compose exec -T db psql -U myadmin hub_auth_db
```

## Updates and Maintenance

### Update Container Images
```bash
docker-compose pull
docker-compose up -d
```

### Clean Up Old Images
```bash
docker image prune -a
```

## Security Best Practices

1. **Use secrets management** for sensitive data (Docker Swarm secrets, Kubernetes secrets, etc.)
2. **Enable HTTPS** in production with valid SSL certificates
3. **Restrict network access** using firewall rules
4. **Regular backups** of database and configuration
5. **Update images regularly** to get security patches
6. **Use non-root user** in containers (add to Dockerfile)
7. **Scan images** for vulnerabilities: `docker scan hub_auth_web`

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEBUG` | Django debug mode | `True` | No |
| `SECRET_KEY` | Django secret key | auto-generated | Yes (production) |
| `ALLOWED_HOSTS` | Comma-separated hostnames | `localhost,127.0.0.1` | No |
| `DATABASE_NAME` | PostgreSQL database name | `hub_auth_db` | No |
| `DATABASE_USER` | PostgreSQL username | `myadmin` | No |
| `DATABASE_PASSWORD` | PostgreSQL password | `secret123` | Yes |
| `DATABASE_HOST` | PostgreSQL host | `db` | No |
| `DATABASE_PORT` | PostgreSQL port | `5432` | No |
| `AZURE_AD_TENANT_ID` | Azure AD tenant ID | - | Yes |
| `AZURE_AD_CLIENT_ID` | Azure AD client ID | - | Yes |
| `AZURE_AD_CLIENT_SECRET` | Azure AD client secret | - | Yes |
| `CORS_ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000,...` | No |
