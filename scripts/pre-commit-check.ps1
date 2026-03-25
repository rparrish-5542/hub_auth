#!/usr/bin/env pwsh
# Pre-commit quality checks script

$ErrorActionPreference = "Stop"

Write-Host "🔍 Running Pre-Commit Quality Checks" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

$failed = $false

# Check if we're in the right directory
if (!(Test-Path "pyproject.toml") -or !(Test-Path "setup.py")) {
    Write-Host "❌ Error: Must run from hub_auth root directory" -ForegroundColor Red
    exit 1
}

# 1. Black (code formatting)
Write-Host "📝 Checking code formatting with Black..." -ForegroundColor Cyan
py -m black --check --diff hub_auth_client/
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Black formatting issues found" -ForegroundColor Red
    Write-Host "💡 Fix with: black hub_auth_client/" -ForegroundColor Yellow
    $failed = $true
} else {
    Write-Host "✅ Black: OK`n" -ForegroundColor Green
}

# 2. isort (import sorting)
Write-Host "📚 Checking import sorting with isort..." -ForegroundColor Cyan
py -m isort --check-only --diff hub_auth_client/
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Import sorting issues found" -ForegroundColor Red
    Write-Host "💡 Fix with: isort hub_auth_client/" -ForegroundColor Yellow
    $failed = $true
} else {
    Write-Host "✅ isort: OK`n" -ForegroundColor Green
}

# 3. Flake8 (style guide)
Write-Host "🎨 Checking style with Flake8..." -ForegroundColor Cyan
py -m flake8 hub_auth_client/ --max-line-length=120 --extend-ignore=E203,W503 --exclude=__pycache__,migrations,*.pyc,.git,__init__.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Flake8 style issues found" -ForegroundColor Red
    $failed = $true
} else {
    Write-Host "✅ Flake8: OK`n" -ForegroundColor Green
}

# 4. MyPy (type checking)
Write-Host "🔤 Checking types with MyPy..." -ForegroundColor Cyan
py -m mypy hub_auth_client/ --ignore-missing-imports --no-strict-optional
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  MyPy type issues found" -ForegroundColor Yellow
    # Don't fail on mypy errors for now
} else {
    Write-Host "✅ MyPy: OK`n" -ForegroundColor Green
}

# 5. Bandit (security)
Write-Host "🔒 Checking security with Bandit..." -ForegroundColor Cyan
py -m bandit -r hub_auth_client/ -ll -i
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Security issues found" -ForegroundColor Red
    $failed = $true
} else {
    Write-Host "✅ Bandit: OK`n" -ForegroundColor Green
}

# 6. Safety (dependency vulnerabilities)
Write-Host "🛡️  Checking dependencies with Safety..." -ForegroundColor Cyan
py -m safety check --short-report
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Vulnerable dependencies found" -ForegroundColor Yellow
    # Don't fail on safety errors for now
} else {
    Write-Host "✅ Safety: OK`n" -ForegroundColor Green
}

# 7. Tests
Write-Host "🧪 Running tests..." -ForegroundColor Cyan
py -m pytest --cov=hub_auth_client --cov-report=term-missing
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tests failed" -ForegroundColor Red
    $failed = $true
} else {
    Write-Host "✅ Tests: OK`n" -ForegroundColor Green
}

# Summary
Write-Host "`n====================================`n" -ForegroundColor Cyan
if ($failed) {
    Write-Host "❌ Pre-commit checks FAILED" -ForegroundColor Red
    Write-Host "🔧 Please fix the issues above before committing" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✅ All checks passed! Ready to commit." -ForegroundColor Green
    exit 0
}
