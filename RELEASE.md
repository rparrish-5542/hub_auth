# Release Process

This document describes how to release a new version of `hub-auth-client` to PyPI.

## Automated Release (Recommended)

### Option 1: Using GitHub UI (Manual Trigger)

1. Go to [Actions → Version Bump](https://github.com/<your-org>/hub_auth/actions/workflows/version-bump.yml)
2. Click "Run workflow"
3. Select version bump type:
   - **patch**: Bug fixes (1.0.44 → 1.0.45)
   - **minor**: New features, backwards compatible (1.0.44 → 1.1.0)
   - **major**: Breaking changes (1.0.44 → 2.0.0)
4. Enter release description (optional)
5. Click "Run workflow"

This will:
- ✅ Bump version in `setup.py` and `pyproject.toml`
- ✅ Create a git tag (`v1.0.45`)
- ✅ Create a GitHub Release
- ✅ Trigger CI/CD to build and publish to PyPI

### Option 2: Manual Git Tag

```bash
# 1. Update version manually
cd c:\Users\rparrish\GitHub\micro_service\hub_auth

# Edit pyproject.toml and setup.py with new version number
# Example: 1.0.45 → 1.0.46

# 2. Commit changes
git add pyproject.toml setup.py
git commit -m "chore: bump version to 1.0.46"

# 3. Create and push tag
git tag v1.0.46
git push origin main
git push origin v1.0.46
```

The CI/CD pipeline will automatically:
- Run tests
- Build the package
- Publish to PyPI

### Option 3: GitHub Release UI

1. Go to [Releases → Create a new release](https://github.com/<your-org>/hub_auth/releases/new)
2. Click "Choose a tag" → Type new version (e.g., `v1.0.46`) → "Create new tag"
3. Fill in release title and description
4. Click "Publish release"

## Manual Release (Fallback)

If automation fails or you need manual control:

```powershell
# 1. Update version
cd c:\Users\rparrish\GitHub\micro_service\hub_auth

# Edit pyproject.toml and setup.py

# 2. Build package
py -m build

# 3. Check package
py -m twine check dist/*

# 4. Upload to PyPI
py -m twine upload dist/*
# Enter PyPI token when prompted

# 5. Create git tag
git tag v1.0.46
git push origin main
git push origin v1.0.46
```

## CI/CD Pipeline Details

### Workflow Triggers

- **Pull Requests**: Builds and tests only (no publish)
- **Push to main**: Builds, tests, dry-run (no publish)
- **Tags (`v*.*.*`)**: Builds, tests, and publishes to PyPI
- **Releases**: Builds, tests, and publishes to PyPI

### Required GitHub Secrets

Configure in **Settings → Security → Secrets and variables → Actions**:

1. **PYPI_API_TOKEN**: PyPI API token for `hub-auth-client`
   - Get from: https://pypi.org/manage/account/token/
   - Scope: "Project: hub-auth-client" or "Entire account"
   - Format: `pypi-...`

### Trusted Publishing (Optional, More Secure)

Instead of using API tokens, set up PyPI Trusted Publishing:

1. Go to PyPI project settings: https://pypi.org/manage/project/hub-auth-client/settings/publishing/
2. Add a new publisher:
   - **Owner**: `<your-org>`
   - **Repository**: `hub_auth`
   - **Workflow name**: `publish-package.yml`
   - **Environment**: `pypi` (must match workflow)
3. In `.github/workflows/publish-package.yml`, uncomment the trusted publishing step

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (1.X.0): New features, backwards compatible
- **PATCH** (1.0.X): Bug fixes

## Changelog

Update `CHANGELOG.md` (if exists) or include in GitHub Release notes:

```markdown
## v1.0.45 (2026-03-25)

### Fixed
- Fixed Django 6.0.3 compatibility with format_html()
- Fixed middleware authentication to set request.msal_user

### Changed
- Updated admin templates to use mark_safe() for static HTML
```

## Verification

After release:

1. **Check PyPI**: https://pypi.org/project/hub-auth-client/
2. **Test install**:
   ```bash
   pip install --upgrade hub-auth-client
   python -c "import hub_auth_client; print(hub_auth_client.__version__)"
   ```
3. **Check GitHub**: https://github.com/<your-org>/hub_auth/releases

## Troubleshooting

### Build fails

```bash
# Check for syntax errors
py -m py_compile hub_auth_client/*.py

# Verify README exists
ls README_PACKAGE.md
```

### PyPI upload fails

- **401 Unauthorized**: Check PYPI_API_TOKEN secret
- **403 Forbidden**: Package name might be taken (first upload only)
- **400 Bad Request**: File already exists (same version uploaded twice)

### Version conflicts

If you need to re-release after fixing a build issue:

```bash
# Delete local dist files
rm -rf dist/ build/ *.egg-info

# Bump patch version
# Edit pyproject.toml and setup.py (increment patch by 1)

# Rebuild and upload
py -m build
py -m twine upload dist/*
```
