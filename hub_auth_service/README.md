# Hub Auth Service

This directory contains the optional Django service implementation for hub_auth.

**⚠️ Most users should use the `hub-auth-client` package instead of running this service.**

## What's in This Directory

This is the original Django microservice for centralized authentication. It includes:

- **User Synchronization** - Syncs users from Azure AD to Django database
- **Service-to-Service Auth** - API keys for service authentication
- **Admin Interface** - Django admin for managing users and permissions
- **Database Models** - User profiles, service clients, audit logs

## When to Use This Service

Use the Django service when you need:
- Centralized user database across multiple projects
- Service-to-service authentication with API keys
- User profile storage and management
- Audit logging of authentication events

## When to Use the Package Instead

Use the `hub-auth-client` package (one directory up) when you:
- Only need JWT token validation
- Want scope/role-based permissions
- Want to avoid running a separate service
- Need flexible, database-driven configuration

**👉 Most projects should use the package.**

## Service Documentation

- [DOCKER.md](DOCKER.md) - Docker deployment guide
- [SCHEMA_SETUP.md](SCHEMA_SETUP.md) - Database schema configuration

## Quick Start

### Using Docker

```bash
cd hub_auth_service

# Copy environment file
cp ../.env.example .env
# Edit .env with your Azure AD credentials

# Build and start
docker-compose up -d --build

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access admin at http://localhost:8000/admin
```

### Without Docker

```bash
cd hub_auth_service

# Install dependencies
pip install -r requirements.txt

# Configure database
# Edit hub_auth/settings.py with your database credentials

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Service Structure

```
hub_auth_service/
├── manage.py               # Django management script
├── requirements.txt        # Service dependencies
├── docker-compose.yml      # Development Docker setup
├── docker-compose.prod.yml # Production Docker setup
├── Dockerfile              # Development Docker image
├── Dockerfile.prod         # Production Docker image
├── entrypoint.sh          # Docker entrypoint script
├── default.conf           # nginx configuration
├── nginx.conf             # nginx configuration
├── hub_auth/              # Django project settings
├── authentication/        # Authentication app
├── services/              # Service client app
├── DOCKER.md             # Docker deployment guide
└── SCHEMA_SETUP.md       # Database schema guide
```

## Environment Variables

Required environment variables (set in `.env`):

```bash
# Azure AD Configuration
AZURE_AD_TENANT_ID=your-tenant-id
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret

# Database (optional, defaults to SQLite)
DATABASE_SCHEMA=hub_auth
DATABASE_NAME=your_db_name
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Django
SECRET_KEY=your-secret-key
DEBUG=True  # Set to False in production
ALLOWED_HOSTS=localhost,127.0.0.1
```

## API Endpoints

The service provides these endpoints:

- `/api/validate-token/` - Validate JWT tokens
- `/api/sync-user/` - Sync user from Azure AD
- `/api/create-service-client/` - Create service-to-service client
- `/admin/` - Django admin interface

## Integration with Package

The `hub-auth-client` package can work with or without this service:

- **With Service**: Package validates tokens, service manages users/profiles
- **Without Service**: Package validates tokens independently, no user database

Most projects don't need the service complexity.

## Migration from Service to Package

If you're currently using this service and want to migrate to the package:

1. Install the package: `pip install c:\Users\rparrish\GitHub\micro_service\hub_auth`
2. Follow the [INSTALLATION.md](../INSTALLATION.md) guide
3. Replace service API calls with direct token validation
4. Use `DynamicPermission` classes for scope/role checks
5. Keep the service running only if you need user sync or API keys

## Support

For package usage, see the main [README.md](../README.md) and [START_HERE.md](../START_HERE.md).

For service-specific issues, refer to [DOCKER.md](DOCKER.md) and [SCHEMA_SETUP.md](SCHEMA_SETUP.md).
