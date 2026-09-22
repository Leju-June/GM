# PowerShell build script for PyInstaller
# Ensure we run from the project root
cd $PSScriptRoot
cd ..

Write-Host "Cleaning up previous builds..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

Write-Host "Running PyInstaller..."

# Important: Playwright in a PyInstaller bundle expects the browsers to be
# located in its own package folder (site-packages/playwright/driver/package/.local-browsers).
# Setting PLAYWRIGHT_BROWSERS_PATH=0 forces playwright to download them there.
$env:PLAYWRIGHT_BROWSERS_PATH = "0"
Write-Host "Downloading local Chromium for Playwright bundling..."
playwright install chromium

# We use --onedir (default) and include Playwright browsers
# Exclude PyQt6 to prevent conflict with PySide6
pyinstaller --name="CleanGuardian" --windowed --add-data="src/guardian/extraction/dom_extract.js;guardian/extraction" --collect-all="playwright" --collect-all="pyahocorasick" --exclude-module PyQt6 src/guardian/__main__.py

Write-Host "Build Complete! Check the dist/CleanGuardian directory."
