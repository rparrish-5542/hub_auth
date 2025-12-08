# Database Schema Setup Guide

## Overview

The hub_auth project is now configured to use a separate PostgreSQL schema, allowing it to coexist with other Django projects on the same database.

## Configuration

### Environment Variables

Add the following to your `.env` file or environment:

```bash
DATABASE_SCHEMA=hub_auth
```

If not set, it defaults to `hub_auth`.

### Search Path

The database is configured with:
```
search_path=hub_auth,public
```

This means:
- Tables will be created in the `hub_auth` schema
- Django auth/admin tables will also be in `hub_auth` schema
- Falls back to `public` schema if needed

## Setup Steps

### 1. Create the Schema in PostgreSQL

Connect to your database and run:

```sql
-- Create the hub_auth schema
CREATE SCHEMA IF NOT EXISTS hub_auth;

-- Grant permissions to your user
GRANT ALL ON SCHEMA hub_auth TO myadmin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hub_auth TO myadmin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA hub_auth TO myadmin;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA hub_auth GRANT ALL ON TABLES TO myadmin;
ALTER DEFAULT PRIVILEGES IN SCHEMA hub_auth GRANT ALL ON SEQUENCES TO myadmin;
```

### 2. Run Migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

All tables will be created in the `hub_auth` schema.

### 3. Collect Static Files

```powershell
python manage.py collectstatic --noinput
```

## Verification

### Check Schema in PostgreSQL

```sql
-- List all schemas
\dn

-- List tables in hub_auth schema
\dt hub_auth.*

-- Verify search path
SHOW search_path;
```

### Expected Tables in hub_auth Schema

- `hub_auth.authentication_user`
- `hub_auth.authentication_tokenvalidation`
- `hub_auth.authentication_serviceclient`
- `hub_auth.django_migrations`
- `hub_auth.django_session`
- `hub_auth.auth_*` (Django auth tables)
- etc.

## Multiple Projects on Same Database

### Example Setup

**Project 1: hub_auth**
```python
DATABASES = {
    'default': {
        ...
        'OPTIONS': {
            'options': '-c search_path=hub_auth,public'
        },
    }
}
```

**Project 2: employee_manage**
```python
DATABASES = {
    'default': {
        ...
        'OPTIONS': {
            'options': '-c search_path=employee_manage,public'
        },
    }
}
```

Each project will have its own schema and won't interfere with each other.

## Troubleshooting

### Tables Created in Wrong Schema

If tables were created in `public` before adding schema configuration:

```sql
-- Move tables to correct schema
ALTER TABLE public.authentication_user SET SCHEMA hub_auth;
ALTER TABLE public.authentication_tokenvalidation SET SCHEMA hub_auth;
-- etc.
```

Or drop and recreate:

```powershell
# WARNING: This will delete all data
python manage.py migrate --fake-initial
python manage.py migrate --run-syncdb
```

### Permission Errors

```sql
-- Grant necessary permissions
GRANT USAGE ON SCHEMA hub_auth TO myadmin;
GRANT CREATE ON SCHEMA hub_auth TO myadmin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA hub_auth TO myadmin;
```

### Check Current Schema

In Django shell:

```python
python manage.py shell

from django.db import connection
cursor = connection.cursor()
cursor.execute("SHOW search_path;")
print(cursor.fetchone())
```

## Notes

- The schema is set via the `search_path` PostgreSQL connection option
- Django will automatically create all tables in the first schema in the search path
- The `public` schema is included as a fallback for PostgreSQL system tables
- Each project can have completely isolated tables while sharing the same database
