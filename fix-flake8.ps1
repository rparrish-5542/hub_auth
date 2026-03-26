# Auto-fix Flake8 issues in hub_auth_client
# Run this script from the hub_auth directory

Write-Host "Installing autopep8..." -ForegroundColor Cyan
py -m pip install autopep8 black isort

Write-Host "`nRunning isort (import sorting)..." -ForegroundColor Cyan
py -m isort hub_auth_client/django/admin.py hub_auth_client/django/admin_actions.py

Write-Host "`nRunning autopep8 (PEP 8 formatting)..." -ForegroundColor Cyan
py -m autopep8 --in-place --aggressive --aggressive --max-line-length=120 `
    hub_auth_client/django/admin.py `
    hub_auth_client/django/admin_actions.py

Write-Host "`nRunning autoflake (remove unused imports)..." -ForegroundColor Cyan
py -m pip install autoflake
py -m autoflake --in-place --remove-unused-variables --remove-all-unused-imports `
    hub_auth_client/django/admin.py `
    hub_auth_client/django/admin_actions.py

Write-Host "`n✅ Auto-formatting complete!" -ForegroundColor Green
Write-Host "Review changes with: git diff" -ForegroundColor Yellow
Write-Host "Then commit: git add -A && git commit -m 'style: fix Flake8 violations with autopep8'" -ForegroundColor Yellow
