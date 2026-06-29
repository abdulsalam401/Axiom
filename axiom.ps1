# Axiom Launcher Script for Windows PowerShell
# Author: Abdul Salam | Salamcs.app
# Description: One-click launcher for Axiom Android Security Framework

param(
    [switch]$Remote,
    [switch]$r,
    [switch]$Screenshot,
    [switch]$s,
    [switch]$Menu,
    [switch]$m,
    [switch]$Help,
    [switch]$h
)

# ─── Configuration ──────────────────────────────────────────────────────────
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $ProjectDir "venv"
$PythonCmd = "python"
$AxiomCmd = "$PythonCmd axiom.py"

# ─── Banner ──────────────────────────────────────────────────────────────────
function Print-Banner {
    Clear-Host
    Write-Host "    _    __  __ _   ___   __  __ " -ForegroundColor Magenta
    Write-Host "   / \   \ \/ /| | / _ \ |  \/  |" -ForegroundColor Magenta
    Write-Host "  / _ \   \  / | || | | || |\/| |" -ForegroundColor Magenta
    Write-Host " / ___ \   /  \| || |_| || |  | |" -ForegroundColor Magenta
    Write-Host "/_/   \_\ /_/\_\_| \___/ |_|  |_|" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "◈ ADVANCED ANDROID SECURITY FRAMEWORK ◈" -ForegroundColor Cyan
    Write-Host "Author: Abdul Salam | Salamcs.app" -ForegroundColor Yellow
    Write-Host ""
}

# ─── Check Dependencies ──────────────────────────────────────────────────────
function Check-Dependencies {
    Write-Host "🔍 Checking dependencies..." -ForegroundColor Cyan
    
    # Check Python
    try {
        $pyVersion = python --version 2>&1
        Write-Host "✓ Python found: $pyVersion" -ForegroundColor Green
    } catch {
        Write-Host "✗ Python not found!" -ForegroundColor Red
        Write-Host "Install Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Check ADB
    try {
        $adbVersion = adb version 2>&1
        Write-Host "✓ ADB found" -ForegroundColor Green
    } catch {
        Write-Host "⚠ ADB not found!" -ForegroundColor Yellow
        Write-Host "Download Android Platform Tools from:" -ForegroundColor Yellow
        Write-Host "https://developer.android.com/studio/releases/platform-tools" -ForegroundColor Yellow
    }
    
    Write-Host ""
}

# ─── Setup Virtual Environment ──────────────────────────────────────────────
function Setup-Venv {
    if (-not (Test-Path $VenvDir)) {
        Write-Host "📦 Creating virtual environment..." -ForegroundColor Cyan
        python -m venv $VenvDir
        Write-Host "✓ Virtual environment created" -ForegroundColor Green
    }
    
    # Activate venv
    & "$VenvDir\Scripts\Activate.ps1"
    
    # Install requirements
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Cyan
    pip install --upgrade pip > $null 2>&1
    pip install -r "$ProjectDir\requirements.txt" > $null 2>&1
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
    Write-Host ""
}

# ─── Check Connected Devices ────────────────────────────────────────────────
function Check-Devices {
    Write-Host "📱 Checking connected devices..." -ForegroundColor Cyan
    
    try {
        $devices = adb devices | Select-String -Pattern "device$" | Measure-Object -Line
        $count = $devices.Lines
        
        if ($count -eq 0) {
            Write-Host "⚠ No devices connected!" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Quick Connect Options:" -ForegroundColor Cyan
            Write-Host "  1. Connect via USB (then use option 8 for WiFi)" -ForegroundColor Green
            Write-Host "  2. Connect via WiFi: adb connect <IP>:5555" -ForegroundColor Green
            Write-Host "  3. Auto-discover: Select option 17 in menu" -ForegroundColor Green
            Write-Host ""
            return $false
        } else {
            Write-Host "✓ Found $count connected device(s)" -ForegroundColor Green
            adb devices | Select-String -Pattern "device$" | ForEach-Object {
                $serial = ($_ -split '\s+')[0]
                Write-Host "  ► $serial" -ForegroundColor Cyan
            }
            Write-Host ""
            return $true
        }
    } catch {
        Write-Host "⚠ ADB not available" -ForegroundColor Yellow
        return $false
    }
}

# ─── Quick Remote Control ────────────────────────────────────────────────────
function Quick-Remote {
    Write-Host "🎮 Starting GUI Remote Control..." -ForegroundColor Cyan
    
    $deviceCount = (adb devices | Select-String -Pattern "device$").Count
    
    if ($deviceCount -eq 0) {
        Write-Host "✗ No devices connected!" -ForegroundColor Red
        Write-Host "Please connect a device first." -ForegroundColor Yellow
        Read-Host "Press Enter to continue"
        return
    }
    
    $serial = (adb devices | Select-String -Pattern "device$" | Select-Object -First 1) -replace '\s+device$', ''
    Write-Host "✓ Using device: $serial" -ForegroundColor Green
    
    if ($serial -match ":") {
        $ip = ($serial -split ":")[0]
        $port = ($serial -split ":")[1]
        Write-Host "✓ Wireless connection: $ip`:$port" -ForegroundColor Green
        Write-Host "Starting GUI remote..." -ForegroundColor Cyan
        & $AxiomCmd --gui-remote --remote-ip $ip --remote-port $port
    } else {
        Write-Host "📡 Enabling WiFi ADB on USB device..." -ForegroundColor Cyan
        Write-Host "Make sure WiFi is ON on your phone!" -ForegroundColor Yellow
        adb -s $serial tcpip 5555
        Start-Sleep -Seconds 2
        
        $ip = (adb -s $serial shell ip addr show wlan0 | Select-String -Pattern 'inet (\d+\.\d+\.\d+\.\d+)/') -replace '.*inet (\d+\.\d+\.\d+\.\d+)/.*', '$1'
        if (-not $ip) {
            $ip = (adb -s $serial shell ifconfig wlan0 | Select-String -Pattern 'inet addr:(\d+\.\d+\.\d+\.\d+)') -replace '.*inet addr:(\d+\.\d+\.\d+\.\d+).*', '$1'
        }
        
        if ($ip) {
            Write-Host "✓ WiFi ADB enabled at $ip`:5555" -ForegroundColor Green
            Write-Host "⚠ Disconnect USB cable now, then press Enter..." -ForegroundColor Yellow
            Read-Host "Press Enter to continue"
            
            adb connect "$ip`:5555"
            Start-Sleep -Seconds 2
            
            Write-Host "Starting GUI remote..." -ForegroundColor Cyan
            & $AxiomCmd --gui-remote --remote-ip $ip --remote-port 5555
        } else {
            Write-Host "✗ Could not get IP address. Make sure WiFi is ON." -ForegroundColor Red
            Write-Host "Starting interactive mode instead..." -ForegroundColor Yellow
            & $AxiomCmd
        }
    }
}

# ─── Quick Screenshot ────────────────────────────────────────────────────────
function Quick-Screenshot {
    Write-Host "📸 Taking screenshot..." -ForegroundColor Cyan
    
    $deviceCount = (adb devices | Select-String -Pattern "device$").Count
    
    if ($deviceCount -eq 0) {
        Write-Host "✗ No devices connected!" -ForegroundColor Red
        return
    }
    
    $serial = (adb devices | Select-String -Pattern "device$" | Select-Object -First 1) -replace '\s+device$', ''
    
    if ($serial -match ":") {
        $ip = ($serial -split ":")[0]
        & $AxiomCmd --remote-screenshot --remote-ip $ip
    } else {
        & $AxiomCmd --screenshot --device $serial
    }
}

# ─── Main Menu ──────────────────────────────────────────────────────────────
function Show-Menu {
    Print-Banner
    
    $deviceCount = (adb devices 2>$null | Select-String -Pattern "device$").Count
    if ($deviceCount -gt 0) {
        Write-Host "  📱 $deviceCount device(s) connected" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "  ⚠ No devices connected" -ForegroundColor Yellow
        Write-Host ""
    }
    
    Write-Host "Quick Actions:" -ForegroundColor Cyan -Bold
    Write-Host "  1. 🎮 Start GUI Remote Control (auto-detect)" -ForegroundColor Green
    Write-Host "  2. 📸 Take Screenshot" -ForegroundColor Green
    Write-Host "  3. 🔍 Auto-Discover & Connect" -ForegroundColor Green
    Write-Host "  4. 📡 Enable WiFi ADB (USB connected)" -ForegroundColor Green
    Write-Host "  5. 🖥️  Full Interactive Menu" -ForegroundColor Green
    Write-Host "  0. 🚪 Exit" -ForegroundColor Green
    Write-Host ""
    Write-Host "Quick Commands:" -ForegroundColor Blue -Bold
    Write-Host "  .\axiom.ps1 -Remote     → GUI Remote Control" -ForegroundColor Cyan
    Write-Host "  .\axiom.ps1 -Screenshot → Take Screenshot" -ForegroundColor Cyan
    Write-Host "  .\axiom.ps1 -Menu       → Full Interactive Menu" -ForegroundColor Cyan
    Write-Host ""
    
    $choice = Read-Host "Select option"
    
    switch ($choice) {
        "1" { Quick-Remote }
        "2" { Quick-Screenshot }
        "3" { & $AxiomCmd --auto-connect }
        "4" { 
            Write-Host "📡 Enabling WiFi ADB..." -ForegroundColor Cyan
            adb tcpip 5555
            Write-Host "✓ WiFi ADB enabled on port 5555" -ForegroundColor Green
            Write-Host "Get IP from phone: Settings → About Phone → Status" -ForegroundColor Yellow
            Write-Host "Then connect: adb connect <IP>:5555" -ForegroundColor Cyan
            Read-Host "Press Enter to continue"
        }
        "5" { & $AxiomCmd }
        "0" { 
            Write-Host "👋 Exiting. Stay ethical!" -ForegroundColor Green
            exit 0
        }
        default { 
            Write-Host "Invalid option" -ForegroundColor Red
            Read-Host "Press Enter to continue"
        }
    }
    
    Show-Menu
}

# ─── Main Execution ─────────────────────────────────────────────────────────

# Handle command line arguments
if ($Remote -or $r) {
    Setup-Venv
    Check-Dependencies
    Quick-Remote
} elseif ($Screenshot -or $s) {
    Setup-Venv
    Check-Dependencies
    Quick-Screenshot
} elseif ($Menu -or $m) {
    Setup-Venv
    & $AxiomCmd
} elseif ($Help -or $h) {
    Write-Host "Axiom Launcher"
    Write-Host ""
    Write-Host "Usage: .\axiom.ps1 [OPTION]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Remote, -r    Start GUI Remote Control (auto-detect)"
    Write-Host "  -Screenshot, -s Take screenshot"
    Write-Host "  -Menu, -m      Open full interactive menu"
    Write-Host "  -Help, -h      Show this help"
    Write-Host ""
    Write-Host "Without arguments, opens interactive menu"
} else {
    # No arguments - show menu
    Setup-Venv
    Check-Dependencies
    Show-Menu
}