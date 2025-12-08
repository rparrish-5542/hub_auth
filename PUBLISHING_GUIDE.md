# Publishing hub-auth-client to PyPI

This guide walks through publishing the `hub-auth-client` package to PyPI (Python Package Index) for easy installation across projects.

## Prerequisites

1. **PyPI Account**: Create an account at [https://pypi.org/account/register/](https://pypi.org/account/register/)
2. **API Token**: Generate an API token at [https://pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)
   - Scope: "Entire account" (for first publish) or "Project: hub-auth-client" (after first publish)
   - Save the token securely - you'll only see it once!

## Manual Publishing (One-Time Setup)

### Step 1: Install Build Tools

```bash
pip install --upgrade pip
pip install build twine
```

### Step 2: Build the Package

```bash
cd hub_auth
python -m build
```

This creates:
- `dist/hub_auth_client-1.0.0-py3-none-any.whl` (wheel file)
- `dist/hub_auth_client-1.0.0.tar.gz` (source distribution)

### Step 3: Test Upload (Optional - TestPyPI)

```bash
# Upload to TestPyPI first to verify everything works
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ hub-auth-client
```

### Step 4: Upload to PyPI

```bash
python -m twine upload dist/*
```

When prompted:
- **Username**: `__token__`
- **Password**: Your PyPI API token (starts with `pypi-`)

## Automated Publishing via GitHub Actions

The repository includes a GitHub Actions workflow (`.github/workflows/publish-package.yml`) that automatically publishes to PyPI when you push to main or create a release.

### Setup GitHub Secrets

1. Go to your repository: `https://github.com/rparrish-5542/hub_auth/settings/secrets/actions`
2. Add a new repository secret:
   - **Name**: `PYPI_API_TOKEN`
   - **Value**: Your PyPI API token

### Trigger Publishing

**Option 1: Push to Main**
```bash
git add .
git commit -m "Update hub-auth-client"
git push origin main
```

**Option 2: Create a Release**
```bash
git tag v1.0.0
git push origin v1.0.0
```

Or create a release through GitHub UI at:
`https://github.com/rparrish-5542/hub_auth/releases/new`

## Verifying Publication

After publishing:

1. **Check PyPI**: Visit [https://pypi.org/project/hub-auth-client/](https://pypi.org/project/hub-auth-client/)
2. **Test Installation**:
   ```bash
   pip install hub-auth-client
   ```
3. **Verify Import**:
   ```python
   import hub_auth_client
   print(hub_auth_client.__version__)
   ```

## Version Updates

When releasing a new version:

1. **Update Version** in both:
   - `setup.py` (line 8): `version="1.0.1"`
   - `pyproject.toml` (line 7): `version = "1.0.1"`

2. **Update Changelog**: Document changes in `CHANGELOG.md`

3. **Build and Publish**:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

4. **Tag the Release**:
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

## Alternative: GitHub Packages

If you prefer to use GitHub Packages instead of PyPI:

### Configure `.pypirc`:
```ini
[distutils]
index-servers =
    github

[github]
repository = https://upload.pypi.org/legacy/
username = rparrish-5542
password = <GITHUB_TOKEN>
```

### Update GitHub Workflow:
```yaml
- name: Publish to GitHub Packages
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.GITHUB_TOKEN }}
  run: |
    python -m twine upload \
      --repository-url https://upload.pypi.org/legacy/ \
      dist/*
```

### Install from GitHub Packages:
```bash
pip install --index-url https://pypi.pkg.github.com/rparrish-5542 hub-auth-client
```

## Troubleshooting

### Error: "The user '...' isn't allowed to upload to project 'hub-auth-client'"
- The package name is already taken. Change `name` in `setup.py` and `pyproject.toml`

### Error: "File already exists"
- You're trying to upload a version that already exists. Increment the version number.

### Error: "Invalid or non-existent authentication information"
- Your API token is incorrect. Verify it's copied correctly including the `pypi-` prefix
- Username must be `__token__` (not your PyPI username)

### Error: "HTTPError: 403 Client Error: Invalid or non-existent authentication"
- Token has wrong scope. Create a new token with "Entire account" scope for first upload

## Next Steps

After publishing to PyPI:

1. ✅ **Update employee_manage**: The `requirements.txt` already includes `hub-auth-client==1.0.0`
2. ✅ **Simplified CI/CD**: The workflow now installs directly from PyPI
3. ✅ **Cleaner Dockerfile**: No more local wheel copying
4. 🔄 **Test the Pipeline**: Push changes to verify everything works

## Support

For issues or questions:
- **Repository**: [https://github.com/rparrish-5542/hub_auth](https://github.com/rparrish-5542/hub_auth)
- **PyPI**: [https://pypi.org/project/hub-auth-client/](https://pypi.org/project/hub-auth-client/)
