# Axiom PowerShell Launcher Script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
# Use .venv-win to isolate the Windows environment from WSL/Linux (.venv)
$VenvDir = Join-Path $ScriptDir ".venv-win"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

# Force Python to use UTF-8 mode for stdout/stderr (prevents UnicodeEncodeError with emojis on Windows)
$env:PYTHONUTF8 = "1"

# 1. Detect Host Python Cmd
$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
} else {
    Write-Host "[!] Error: Python is not installed or not in PATH." -ForegroundColor Red
    Exit 1
}

# 2. Auto-setup virtual environment if missing
if (-not (Test-Path $VenvDir)) {
    Write-Host "[*] Windows Python virtual environment not found. Creating one at $VenvDir..." -ForegroundColor Blue
    Start-Process $PythonCmd -ArgumentList "-m venv `"$VenvDir`"" -Wait -NoNewWindow
    if ($LASTEXITCODE -ne 0 -and -not (Test-Path $VenvPython)) {
        Write-Host "[!] Failed to create virtual environment." -ForegroundColor Red
        Exit 1
    }
}

# 3. Upgrade pip and install dependencies if 'rich' isn't available in the venv
& $VenvPython -c "import rich" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[*] Installing required dependencies in virtual environment..." -ForegroundColor Blue
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r "$ScriptDir\requirements.txt"
}

# 4. Run Axiom using the virtual environment's python directly (bypassing execution policies)
& $VenvPython "$ScriptDir\axiom.py" $args
