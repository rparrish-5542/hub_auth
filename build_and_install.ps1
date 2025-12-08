# Hub Auth Client - Build and Install Script
# Run this script to build and test the package

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 58) -ForegroundColor Cyan
Write-Host "Hub Auth Client - Build and Install" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 58) -ForegroundColor Cyan
Write-Host ""

# Navigate to hub_auth directory
$hubAuthDir = "c:\Users\rparrish\GitHub\micro_service\hub_auth"
Set-Location $hubAuthDir

# Step 1: Install build tools
Write-Host "Step 1: Installing build tools..." -ForegroundColor Yellow
pip install --upgrade build wheel setuptools
Write-Host "Build tools installed" -ForegroundColor Green
Write-Host ""

# Step 2: Clean previous builds
Write-Host "Step 2: Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force build }
if (Test-Path "dist") { Remove-Item -Recurse -Force dist }
if (Test-Path "*.egg-info") { Remove-Item -Recurse -Force *.egg-info }
Write-Host "Previous builds cleaned" -ForegroundColor Green
Write-Host ""

# Step 3: Build the package
Write-Host "Step 3: Building package..." -ForegroundColor Yellow
python -m build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Package built successfully" -ForegroundColor Green
Write-Host ""

# Step 4: List build artifacts
Write-Host "Step 4: Build artifacts created:" -ForegroundColor Yellow
Get-ChildItem dist | ForEach-Object {
    Write-Host "  - $($_.Name)" -ForegroundColor Cyan
}
Write-Host ""

# Step 5: Install the package
Write-Host "Step 5: Installing package..." -ForegroundColor Yellow
$whl = Get-ChildItem "dist\*.whl" | Select-Object -First 1
pip install --upgrade --force-reinstall $whl.FullName
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installation failed!" -ForegroundColor Red
    exit 1
}
Write-Host "Package installed successfully" -ForegroundColor Green
Write-Host ""

# Step 6: Verify installation
Write-Host "Step 6: Verifying installation..." -ForegroundColor Yellow
python verify_install.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Verification failed!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Summary
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 58) -ForegroundColor Cyan
Write-Host "Build and Install Complete!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 58) -ForegroundColor Cyan
Write-Host ""
Write-Host "Package is ready to use!" -ForegroundColor Green
Write-Host ""
Write-Host "To install in other projects:" -ForegroundColor Yellow
Write-Host "  cd /path/to/your/project" -ForegroundColor Cyan
Write-Host "  pip install $hubAuthDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use editable install for development:" -ForegroundColor Yellow
Write-Host "  pip install -e $hubAuthDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "  - QUICKSTART.md - Quick start guide" -ForegroundColor Cyan
Write-Host "  - README_PACKAGE.md - Full documentation" -ForegroundColor Cyan
Write-Host "  - INSTALLATION.md - Detailed installation guide" -ForegroundColor Cyan
Write-Host ""
