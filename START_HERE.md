# 📖 Hub Auth Client - Documentation Index

Welcome! This is the **hub-auth-client** pip package for MSAL JWT validation with Entra ID RBAC.

## 🎯 Quick Navigation

### 🚀 **Want to get started quickly?**
→ Read **[QUICKSTART.md](QUICKSTART.md)**

### 📦 **Want to install in employee_manage?**
→ Read **[INSTALL_IN_EMPLOYEE_MANAGE.md](INSTALL_IN_EMPLOYEE_MANAGE.md)**

### 📚 **Want full package documentation?**
→ Read **[README_PACKAGE.md](README_PACKAGE.md)**

### 🔧 **Having installation issues?**
→ Read **[INSTALLATION.md](INSTALLATION.md)**

### 🗄️ **Want database-driven permissions?**
→ Read **[DYNAMIC_PERMISSIONS.md](DYNAMIC_PERMISSIONS.md)** (Recommended!)

### 🐳 **Want to run the optional Django service?**
→ Read **[hub_auth_service/README.md](hub_auth_service/README.md)**

## 📁 What's in This Directory?

### 🆕 Package Files (hub-auth-client)

```
hub_auth_client/              # The pip-installable package
├── __init__.py              # Main exports
├── validator.py             # MSAL token validator
├── exceptions.py            # Custom exceptions
└── django/                  # Django integration
    ├── authentication.py    # DRF auth backend
    ├── middleware.py        # Django middleware
    ├── permissions.py       # Permission classes
    ├── decorators.py        # View decorators
    ├── models.py           # Scope/Role/Endpoint models
    ├── admin.py            # Django admin interface
    ├── dynamic_permissions.py  # Database-driven permissions
    └── migrations/         # Database migrations
```

### 📝 Documentation Files

| File | Purpose | When to Read |
|------|---------|--------------|
| **QUICKSTART.md** | Get started in 5 minutes | First time using |
| **README_PACKAGE.md** | Complete package docs | Need detailed info |
| **DYNAMIC_PERMISSIONS.md** | Database-driven permissions | Configure via admin ⭐ |
| **DATABASE_CONFIG_GUIDE.md** | Database-driven configuration | Store Azure AD creds in DB 🆕 |
| **ADMIN_SSO_GUIDE.md** | Admin SSO setup | MSAL-based admin login 🔐 |
| **RLS_GUIDE.md** | PostgreSQL Row-Level Security | Database-level security 🔒 |
| **RLS_ADMIN_GUIDE.md** | RLS via Django Admin | Manage RLS without command line 🎯 |
| **DYNAMIC_PERMISSIONS_SUMMARY.md** | Quick overview | Understanding dynamic permissions |
| **INSTALLATION.md** | Installation guide | Installation issues |
| **INSTALL_IN_EMPLOYEE_MANAGE.md** | employee_manage integration | Installing in employee_manage |

### 🎓 Example Files

```
examples/
├── example_settings.py      # Django settings example
├── example_views.py         # View examples
├── example_urls.py          # URL configuration
└── .env.example            # Environment variables
```

### 🧪 Test Files

```
tests/
├── test_validator.py        # Core validation tests
├── test_django_integration.py  # Django tests
├── conftest.py             # pytest config
└── requirements-test.txt   # Test dependencies
```

### 🛠️ Build Files

| File | Purpose |
|------|---------|
| `setup.py` | Package setup configuration |
| `pyproject.toml` | Modern Python project config |
| `MANIFEST.in` | Package file manifest |
| `LICENSE` | MIT License |
| `requirements-package.txt` | Package dependencies |
| `build_and_install.ps1` | Automated build script |
| `verify_install.py` | Installation verification |

### 🐳 Optional Django Service

```
hub_auth_service/            # Optional centralized service
├── README.md               # Service documentation
├── manage.py               # Django management
├── requirements.txt        # Service dependencies
├── docker-compose.yml      # Docker setup
├── DOCKER.md              # Docker deployment guide
├── SCHEMA_SETUP.md        # Database schema guide
├── hub_auth/              # Django settings
├── authentication/         # Auth app
└── services/              # Service modules
```

**Note:** Most users don't need the service. The package works standalone.

## 🎯 Common Tasks

### Build the Package

```powershell
cd c:\Users\rparrish\GitHub\micro_service\hub_auth
.\build_and_install.ps1
```

Or manually:

```powershell
pip install build wheel
python -m build
```

### Install in a Project

```powershell
cd /path/to/your/project
pip install c:\Users\rparrish\GitHub\micro_service\hub_auth
```

### Verify Installation

```powershell
python verify_install.py
```

### Run Tests

```powershell
pip install -r tests/requirements-test.txt
pytest tests/
```

## 🔑 Key Features

- ✅ **MSAL JWT Validation** - Validates tokens with Azure AD
- ✅ **Scope-Based RBAC** - Entra ID scope validation
- ✅ **Role-Based RBAC** - App role validation
- ✅ **Database-Driven Permissions** - Configure scopes/roles through Django admin
- ✅ **Database-Driven Configuration** - Store Azure AD credentials in database 🆕
- ✅ **PostgreSQL RLS** - Row-level security enforcement at database level
- ✅ **Django Integration** - Middleware, auth backend, permissions
- ✅ **Pip Installable** - Easy installation in any project
- ✅ **Well Tested** - Comprehensive test suite
- ✅ **Well Documented** - Multiple documentation levels

## 📖 Documentation by Use Case

### "I want to understand what this package does"
1. Read [README.md](README.md) - Package overview
2. Read [README_PACKAGE.md](README_PACKAGE.md) - Complete documentation
3. Browse [examples/](examples/) - Code examples

### "I want to install this in my project"
1. Read [QUICKSTART.md](QUICKSTART.md) - Quick start
2. Read [INSTALLATION.md](INSTALLATION.md) - Detailed guide
3. Run `verify_install.py` - Verify it works


### "I want database-driven permissions"
1. Read [DYNAMIC_PERMISSIONS.md](DYNAMIC_PERMISSIONS.md) - Complete guide
2. See [DYNAMIC_PERMISSIONS_SUMMARY.md](DYNAMIC_PERMISSIONS_SUMMARY.md) - Quick overview
3. Configure scopes/roles in Django admin

### "I want to store Azure AD credentials in database (no .env files)"
1. Read [DATABASE_CONFIG_GUIDE.md](DATABASE_CONFIG_GUIDE.md) - Complete guide 🆕
2. Add `hub_auth_client.django` to INSTALLED_APPS
3. Run migrations and configure via Django admin
4. Remove environment variables (optional)

### "I want database-level row security (RLS)"
1. Read [RLS_GUIDE.md](RLS_GUIDE.md) - Complete PostgreSQL RLS guide
2. Configure RLS policies in Django admin
3. Enable RLS middleware
4. Test with different user scopes/roles

### "I want to run the Django service"
1. Read [hub_auth_service/README.md](hub_auth_service/README.md) - Service docs
2. Read [hub_auth_service/DOCKER.md](hub_auth_service/DOCKER.md) - Docker deployment
3. Understand when you need it (most projects don't)

### "I'm having issues"
1. Read [INSTALLATION.md](INSTALLATION.md) - Troubleshooting section
2. Run `verify_install.py` - Check installation
3. Check Azure AD configuration

### "I want to contribute or modify"
1. Install in editable mode: `pip install -e .`
2. Read source code in `hub_auth_client/`
3. Run tests: `pytest tests/`
4. Add your changes

## 🆘 Getting Help

### Documentation
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Full Docs**: [README_PACKAGE.md](README_PACKAGE.md)
- **Installation**: [INSTALLATION.md](INSTALLATION.md)
- **Dynamic Permissions**: [DYNAMIC_PERMISSIONS.md](DYNAMIC_PERMISSIONS.md)
- **Examples**: [examples/](examples/)

### Verification
```powershell
python verify_install.py
```

### Testing
```powershell
pytest tests/ -v
```

## 🎊 What You Can Do

2. ✅ Install in other microservices
3. ✅ Use scope-based RBAC
4. ✅ Use role-based RBAC
5. ✅ Configure permissions via Django admin
6. ✅ Validate MSAL JWT tokens
7. ✅ Integrate with Django/DRF
8. ✅ Run tests
9. ✅ Build and distribute


## 📞 Support

For issues or questions:
- Check the documentation files above
- Review examples in `examples/`
- Run `verify_install.py`
- Check troubleshooting in `INSTALLATION.md`

---

**Ready to get started? → Read [QUICKSTART.md](QUICKSTART.md)**
