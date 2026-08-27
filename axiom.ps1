# Axiom Launcher Script for Windows PowerShell
# Author: Abdul Salam | Salamcs.app
# Description: One-click launcher for Axiom Android Security Framework (Matrix Hacker Edition)

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
    Write-Host " █████╗ ██╗  ██╗██╗ ██████╗ ███╗   ███╗" -ForegroundColor Green
    Write-Host "██╔══██╗╚██╗██╔╝██║██╔═══██╗████╗ ████║" -ForegroundColor Green
    Write-Host "███████║ ╚███╔╝ ██║██║   ██║██╔████╔██║" -ForegroundColor Green
    Write-Host "██╔══██║ ██╔██╗ ██║██║   ██║██║╚██╔╝██║" -ForegroundColor Green
    Write-Host "██║  ██║██╔╝ ██╗██║╚██████╔╝██║ ╚═╝ ██║" -ForegroundColor Green
    Write-Host "╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝     ╚═╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚡ ANDROID SECURITY FRAMEWORK — MATRIX EDITION ⚡" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor DarkGreen
    Write-Host "Author: Abdul Salam | Salamcs.app | Matrix Core v2.1.0" -ForegroundColor DarkCyan
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
                $serial = ($_ -split "\s+")[0]
                Write-Host "  ► $serial" -ForegroundColor Cyan
            }
            Write-Host ""
            return $true
        }
    } catch {
        Write-Host "✗ ADB error" -ForegroundColor Red
        return $false
    }
}

# ─── Quick Remote Control ────────────────────────────────────────────────────
function Quick-Remote {
    Write-Host "🎮 Starting GUI Remote Control..." -ForegroundColor Cyan
    
    try {
        $devices = adb devices | Select-String -Pattern "device$"
        $count = ($devices | Measure-Object -Line).Lines
        
        if ($count -eq 0) {
            Write-Host "✗ No devices connected!" -ForegroundColor Red
            Write-Host "Please connect a device first." -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Quick options:" -ForegroundColor Cyan
            Write-Host "  1. Connect USB and run: adb tcpip 5555" -ForegroundColor Green
            Write-Host "  2. Connect WiFi: adb connect <IP>:5555" -ForegroundColor Green
            Write-Host "  3. Press Enter to run interactive menu" -ForegroundColor Green
            Read-Host "Press Enter to continue"
            return
        }
        
        $firstDevice = ($devices | Select-Object -First 1).ToString()
        $serial = ($firstDevice -split "\s+")[0]
        Write-Host "✓ Using device: $serial" -ForegroundColor Green
        
        if ($serial -like "*:*") {
            $parts = $serial -split ":"
            $ip = $parts[0]
            $port = $parts[1]
            Write-Host "✓ Wireless connection: $ip`:$port" -ForegroundColor Green
            Write-Host "Starting GUI remote..." -ForegroundColor Cyan
            python axiom.py --gui-remote --remote-ip $ip --remote-port $port
        } else {
            Write-Host "📡 Enabling WiFi ADB on USB device..." -ForegroundColor Cyan
            Write-Host "Make sure WiFi is ON on your phone!" -ForegroundColor Yellow
            adb -s $serial tcpip 5555
            Start-Sleep -Seconds 2
            
            $ipOut = adb -s $serial shell ip addr show wlan0
            $ip = [regex]::Match($ipOut, 'inet (\d+\.\d+\.\d+\.\d+)').Groups[1].Value
            
            if ($ip) {
                Write-Host "✓ WiFi ADB enabled at $ip`:5555" -ForegroundColor Green
                Write-Host "⚠ Disconnect USB cable now, then press Enter..." -ForegroundColor Yellow
                Read-Host "Press Enter to continue"
                
                adb connect "$ip`:5555"
                Start-Sleep -Seconds 2
                
                Write-Host "Starting GUI remote..." -ForegroundColor Cyan
                python axiom.py --gui-remote --remote-ip $ip --remote-port 5555
            } else {
                Write-Host "✗ Could not get IP. Starting interactive mode..." -ForegroundColor Yellow
                python axiom.py
            }
        }
    } catch {
        Write-Host "✗ Error: $_" -ForegroundColor Red
        python axiom.py
    }
}

# ─── Quick Screenshot ────────────────────────────────────────────────────────
function Quick-Screenshot {
    Write-Host "📸 Taking screenshot..." -ForegroundColor Cyan
    
    try {
        $devices = adb devices | Select-String -Pattern "device$"
        $count = ($devices | Measure-Object -Line).Lines
        
        if ($count -eq 0) {
            Write-Host "✗ No devices connected!" -ForegroundColor Red
            return
        }
        
        $firstDevice = ($devices | Select-Object -First 1).ToString()
        $serial = ($firstDevice -split "\s+")[0]
        
        if ($serial -like "*:*") {
            $ip = ($serial -split ":")[0]
            python axiom.py --remote-screenshot --remote-ip $ip
        } else {
            python axiom.py --screenshot --device $serial
        }
    } catch {
        Write-Host "✗ Error: $_" -ForegroundColor Red
    }
}

# ─── Main Menu ───────────────────────────────────────────────────────────────
function Show-Menu {
    Print-Banner
    
    # Check devices
    try {
        $devices = adb devices | Select-String -Pattern "device$" | Measure-Object -Line
        $count = $devices.Lines
        if ($count -gt 0) {
            Write-Host "  📱 $count device(s) connected" -ForegroundColor Green
            Write-Host ""
        } else {
            Write-Host "  ⚠ No devices connected" -ForegroundColor Yellow
            Write-Host ""
        }
    } catch {}
    
    Write-Host "⚡ Quick Actions:" -ForegroundColor Cyan
    Write-Host "  [1] 🎮 Start GUI Remote Control (auto-detect)" -ForegroundColor Green
    Write-Host "  [2] 📸 Take Screenshot" -ForegroundColor Green
    Write-Host "  [3] 🔍 Auto-Discover & Connect" -ForegroundColor Green
    Write-Host "  [4] 📡 Enable WiFi ADB (USB connected)" -ForegroundColor Green
    Write-Host "  [5] 🖥️  Full Interactive Menu" -ForegroundColor Green
    Write-Host "  [0] 🚪 Exit" -ForegroundColor Green
    Write-Host ""
    Write-Host "───────────────────────────────────────────────────" -ForegroundColor DarkGreen
    Write-Host "Quick Commands:" -ForegroundColor DarkCyan
    Write-Host "  .\axiom.ps1 -Remote      → GUI Remote Control" -ForegroundColor Cyan
    Write-Host "  .\axiom.ps1 -Screenshot  → Take Screenshot" -ForegroundColor Cyan
    Write-Host "  .\axiom.ps1 -Menu        → Full Interactive Menu" -ForegroundColor Cyan
    Write-Host ""
    
    $choice = Read-Host "Axiom ⚡ Select option"
    
    switch ($choice) {
        "1" { Quick-Remote }
        "2" { Quick-Screenshot }
        "3" { python axiom.py --auto-connect }
        "4" {
            Write-Host "📡 Enabling WiFi ADB..." -ForegroundColor Cyan
            adb tcpip 5555
            Write-Host "✓ WiFi ADB enabled on port 5555" -ForegroundColor Green
            Write-Host "Get IP from phone: Settings → About Phone → Status" -ForegroundColor Yellow
            Write-Host "Then connect: adb connect <IP>:5555" -ForegroundColor Cyan
            Read-Host "Press Enter to continue"
        }
        "5" { python axiom.py }
        "0" {
            Write-Host "⚡ Exiting Axiom. Stay ethical!" -ForegroundColor Green
            exit 0
        }
        Default {
            Write-Host "Invalid option" -ForegroundColor Red
            Read-Host "Press Enter to continue"
        }
    }
    
    Show-Menu
}

# ─── Main Execution ──────────────────────────────────────────────────────────
if ($Help -or $h) {
    Write-Host "Axiom Launcher (Matrix Edition)"
    Write-Host ""
    Write-Host "Usage: .\axiom.ps1 [OPTION]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Remote, -r      Start GUI Remote Control (auto-detect)"
    Write-Host "  -Screenshot, -s  Take screenshot"
    Write-Host "  -Menu, -m        Open full interactive menu"
    Write-Host "  -Help, -h        Show this help"
    Write-Host ""
    exit 0
}

if ($Remote -or $r) {
    Setup-Venv
    Check-Dependencies
    Quick-Remote
    exit 0
}

if ($Screenshot -or $s) {
    Setup-Venv
    Check-Dependencies
    Quick-Screenshot
    exit 0
}

if ($Menu -or $m) {
    Setup-Venv
    python axiom.py
    exit 0
}

# Default: Interactive Menu
Setup-Venv
Check-Dependencies
Show-Menu