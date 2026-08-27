# ==============================================================================
#  Axiom — One-Click Terminal Installer for Windows PowerShell
#  Author: Abdul Salam | Salamcs.app
# ==============================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Stop"

Clear-Host
Write-Host " █████╗ ██╗  ██╗██╗ ██████╗ ███╗   ███╗" -ForegroundColor Green
Write-Host "██╔══██╗╚██╗██╔╝██║██╔═══██╗████╗ ████║" -ForegroundColor Green
Write-Host "███████║ ╚███╔╝ ██║██║   ██║██╔████╔██║" -ForegroundColor Green
Write-Host "██╔══██║ ██╔██╗ ██║██║   ██║██║╚██╔╝██║" -ForegroundColor Green
Write-Host "██║  ██║██╔╝ ██╗██║╚██████╔╝██║ ╚═╝ ██║" -ForegroundColor Green
Write-Host "╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝     ╚═╝" -ForegroundColor Green
Write-Host ""
Write-Host "⚡ AXIOM TERMINAL INSTALLER (WINDOWS POWERSHELL) ⚡" -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────────────────────────" -ForegroundColor DarkGreen
Write-Host ""

$InstallDir = Join-Path $HOME ".axiom"
$BinDir = Join-Path $InstallDir "bin"
$RepoUrl = "https://github.com/abdulsalam401/Axiom.git"

# 1. Check Python
Write-Host "🔍 [1/5] Checking environment and dependencies..." -ForegroundColor Cyan
try {
    $pyVer = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
    Write-Host "✓ Python $pyVer detected" -ForegroundColor Green
} catch {
    Write-Host "✗ Python is required but not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python from https://www.python.org/downloads/ (check 'Add python.exe to PATH')." -ForegroundColor Yellow
    exit 1
}

# Check ADB
try {
    $adbCheck = adb version 2>&1
    Write-Host "✓ ADB (Android Debug Bridge) detected" -ForegroundColor Green
} catch {
    Write-Host "⚠ ADB not found in PATH. Recommended to install Android Platform Tools." -ForegroundColor Yellow
}

# 2. Setup Source Directory
Write-Host ""
Write-Host "📦 [2/5] Setting up Axiom files..." -ForegroundColor Cyan

$CurrentScriptDir = $PSScriptRoot
if (-not $CurrentScriptDir) {
    try {
        $CurrentScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    } catch {
        $CurrentScriptDir = ""
    }
}

if ($CurrentScriptDir -and (Test-Path (Join-Path $CurrentScriptDir "axiom.py"))) {
    $TargetSrc = $CurrentScriptDir
    Write-Host "✓ Using local source directory: $TargetSrc" -ForegroundColor Green
} else {
    if (Test-Path (Join-Path $InstallDir ".git")) {
        Write-Host "Updating existing Axiom installation..." -ForegroundColor Green
        Set-Location $InstallDir
        git pull --quiet
    } else {
        Write-Host "Cloning Axiom repository to $InstallDir..." -ForegroundColor Green
        if (Test-Path $InstallDir) { Remove-Item -Recurse -Force $InstallDir }
        git clone --depth 1 $RepoUrl $InstallDir
    }
    $TargetSrc = $InstallDir
}

# 3. Setup Virtual Environment
Write-Host ""
Write-Host "🐍 [3/5] Configuring Python virtual environment..." -ForegroundColor Cyan
$VenvDir = Join-Path $TargetSrc "venv"

if (-not (Test-Path $VenvDir)) {
    python -m venv $VenvDir
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

& $VenvPip install --upgrade pip --quiet
& $VenvPip install -r (Join-Path $TargetSrc "requirements.txt") --quiet
& $VenvPip install -e $TargetSrc --quiet
Write-Host "✓ Python dependencies installed" -ForegroundColor Green

# 4. Create Global axiom.cmd and axiom.ps1 wrappers
Write-Host ""
Write-Host "🚀 [4/5] Creating global launcher commands..." -ForegroundColor Cyan

if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
}

$CmdLauncher = Join-Path $BinDir "axiom.cmd"
$PsLauncher  = Join-Path $BinDir "axiom.ps1"

# Create axiom.cmd
$CmdContent = @"
@echo off
set "PYTHONIOENCODING=utf-8"
"$VenvPython" "$TargetSrc\axiom.py" %*
"@
Set-Content -Path $CmdLauncher -Value $CmdContent -Encoding ASCII

# Create axiom.ps1
$PsContent = @"
`$env:PYTHONIOENCODING = "utf-8"
& "$VenvPython" "$TargetSrc\axiom.py" `$args
"@
Set-Content -Path $PsLauncher -Value $PsContent -Encoding UTF8

# Also copy into WindowsApps if available for immediate PATH access
$WindowsAppsDir = Join-Path $HOME "AppData\Local\Microsoft\WindowsApps"
if (Test-Path $WindowsAppsDir) {
    Copy-Item -Path $CmdLauncher -Destination (Join-Path $WindowsAppsDir "axiom.cmd") -Force
}

# 5. Ensure $BinDir is in User PATH
Write-Host ""
Write-Host "🔧 [5/5] Ensuring User PATH configuration..." -ForegroundColor Cyan

$UserPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($UserPath -notlike "*$BinDir*") {
    $NewUserPath = "$BinDir;$UserPath"
    [Environment]::SetEnvironmentVariable("PATH", $NewUserPath, "User")
    $env:PATH = "$BinDir;$env:PATH"
    Write-Host "✓ Added $BinDir to User PATH environment variable" -ForegroundColor Green
} else {
    Write-Host "✓ $BinDir already in PATH" -ForegroundColor Green
}

Write-Host ""
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "✓ AXIOM SUCCESSFULLY INSTALLED!" -ForegroundColor Cyan
Write-Host "═════════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "You can now launch Axiom from ANY Command Prompt or PowerShell:" -ForegroundColor White
Write-Host ""
Write-Host "    axiom" -ForegroundColor Green
Write-Host ""
Write-Host "Or run with specific flags:" -ForegroundColor White
Write-Host "    axiom --help" -ForegroundColor Cyan
Write-Host "    axiom --devices" -ForegroundColor Cyan
Write-Host "    axiom --remote" -ForegroundColor Cyan
Write-Host ""
Write-Host "Note: In newly opened terminal windows, simply type 'axiom' to begin." -ForegroundColor DarkGray
Write-Host ""
