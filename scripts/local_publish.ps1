#!/usr/bin/env pwsh
# Local PyPI publish script with safety checks

param(
    [switch]$Force,
    [switch]$DryRun,
    [switch]$TestPyPI
)

$ErrorActionPreference = "Stop"

Write-Host "🔧 Local PyPI Publish Script" -ForegroundColor Cyan
Write-Host "================================`n" -ForegroundColor Cyan

# Check if we're in the right directory
if (!(Test-Path "pyproject.toml") -or !(Test-Path "setup.py")) {
    Write-Host "❌ Error: Must run from hub_auth root directory" -ForegroundColor Red
    exit 1
}

# Check if README_PACKAGE.md exists
if (!(Test-Path "README_PACKAGE.md")) {
    Write-Host "❌ Error: README_PACKAGE.md not found!" -ForegroundColor Red
    exit 1
}

# Get current version
$version = (Select-String -Path "pyproject.toml" -Pattern 'version = "(.+)"').Matches[0].Groups[1].Value
Write-Host "📦 Package version: $version" -ForegroundColor Green

# Check for uncommitted changes
$gitStatus = git status --porcelain
if ($gitStatus -and !$Force) {
    Write-Host "⚠️  Warning: You have uncommitted changes:" -ForegroundColor Yellow
    Write-Host $gitStatus
    Write-Host "`nUse -Force to proceed anyway or commit your changes first." -ForegroundColor Yellow
    exit 1
}

# Check if tag exists
$tagExists = git tag -l "v$version"
if (!$tagExists -and !$Force) {
    Write-Host "⚠️  Warning: Git tag v$version does not exist" -ForegroundColor Yellow
    $createTag = Read-Host "Create tag v$version? (y/N)"
    if ($createTag -eq 'y') {
        git tag "v$version"
        Write-Host "✅ Created tag v$version" -ForegroundColor Green
        Write-Host "💡 Don't forget to push: git push origin v$version" -ForegroundColor Cyan
    }
}

# Clean old builds
Write-Host "`n🧹 Cleaning old builds..." -ForegroundColor Cyan
if (Test-Path "dist") { Remove-Item -Recurse -Force dist }
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "*.egg-info") { Remove-Item -Recurse -Force *.egg-info }

# Build package
Write-Host "`n🔨 Building package..." -ForegroundColor Cyan
py -m build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    exit 1
}

# Check package
Write-Host "`n🔍 Checking package..." -ForegroundColor Cyan
py -m twine check dist/*

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Package check failed!" -ForegroundColor Red
    exit 1
}

# List artifacts
Write-Host "`n📦 Built artifacts:" -ForegroundColor Cyan
Get-ChildItem dist | Format-Table Name, Length -AutoSize

# Dry run mode
if ($DryRun) {
    Write-Host "`n✅ Dry run complete - no upload performed" -ForegroundColor Green
    Write-Host "💡 Remove -DryRun flag to actually publish" -ForegroundColor Cyan
    exit 0
}

# Confirm upload
Write-Host "`n⚠️  Ready to upload version $version to PyPI" -ForegroundColor Yellow
if ($TestPyPI) {
    Write-Host "   Target: TestPyPI (https://test.pypi.org)" -ForegroundColor Yellow
} else {
    Write-Host "   Target: Production PyPI (https://pypi.org)" -ForegroundColor Yellow
}

if (!$Force) {
    $confirm = Read-Host "Continue? (y/N)"
    if ($confirm -ne 'y') {
        Write-Host "❌ Upload cancelled" -ForegroundColor Red
        exit 1
    }
}

# Upload
Write-Host "`n📤 Uploading to PyPI..." -ForegroundColor Cyan
if ($TestPyPI) {
    py -m twine upload --repository testpypi dist/*
} else {
    py -m twine upload dist/*
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Successfully published hub-auth-client v$version!" -ForegroundColor Green
    Write-Host "📦 View at: https://pypi.org/project/hub-auth-client/$version/" -ForegroundColor Cyan
    Write-Host "`n💡 Next steps:" -ForegroundColor Cyan
    Write-Host "   - Push tag: git push origin v$version" -ForegroundColor White
    Write-Host "   - Create GitHub release: gh release create v$version" -ForegroundColor White
    Write-Host "   - Test install: pip install --upgrade hub-auth-client" -ForegroundColor White
} else {
    Write-Host "`n❌ Upload failed!" -ForegroundColor Red
    exit 1
}
