#!/bin/bash
# Axiom Launcher Script
# Author: Abdul Salam | Salamcs.app
# Description: One-click launcher for Axiom Android Security Framework (Matrix Hacker Edition)

set -e

# ─── Colors (Matrix / Hacker Theme) ──────────────────────────────────────────
NC='\033[0m'               # Reset
BOLD='\033[1m'             # Bold
DIM='\033[2m'              # Dim

# Matrix Greens & Mints (256-color & Standard ANSI fallbacks)
MATRIX_GREEN='\033[38;5;46m'     # Vibrant Neon Matrix Green
MINT_GREEN='\033[38;5;48m'       # Bright Mint Accent
EMERALD='\033[38;5;34m'          # Mid Emerald Green
DARK_EMERALD='\033[38;5;28m'     # Dark Emerald
CYBER_CYAN='\033[38;5;51m'       # Cyber Cyan Accent
WARN_YELLOW='\033[38;5;220m'     # Warning Gold
ALERT_RED='\033[38;5;196m'       # Alert Red

# ANSI Basic Fallbacks
GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
RED='\033[1;31m'

# ─── Configuration ──────────────────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_CMD="python3"
AXIOM_CMD="$PYTHON_CMD axiom.py"

# ─── Banner ──────────────────────────────────────────────────────────────────
print_banner() {
    clear
    echo -e "${MATRIX_GREEN}"
    echo ' █████╗ ██╗  ██╗██╗ ██████╗ ███╗   ███╗'
    echo '██╔══██╗╚██╗██╔╝██║██╔═══██╗████╗ ████║'
    echo '███████║ ╚███╔╝ ██║██║   ██║██╔████╔██║'
    echo '██╔══██║ ██╔██╗ ██║██║   ██║██║╚██╔╝██║'
    echo '██║  ██║██╔╝ ██╗██║╚██████╔╝██║ ╚═╝ ██║'
    echo '╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝     ╚═╝'
    echo -e "${NC}"
    echo -e "${MINT_GREEN}${BOLD}⚡ ANDROID SECURITY FRAMEWORK — MATRIX EDITION ⚡${NC}"
    echo -e "${DARK_EMERALD}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYBER_CYAN}Author:${NC} ${BOLD}Abdul Salam${NC} | ${MINT_GREEN}Salamcs.app${NC} | ${MATRIX_GREEN}Matrix Core v2.1.0${NC}"
    echo ""
}

# ─── Check Dependencies ──────────────────────────────────────────────────────
check_dependencies() {
    echo -e "${MINT_GREEN}🔍 Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${ALERT_RED}✗ Python3 not found!${NC}"
        echo -e "${WARN_YELLOW}Install: sudo apt install python3 python3-pip python3-venv${NC}"
        exit 1
    fi
    echo -e "${MATRIX_GREEN}✓ Python3 found${NC}"
    
    # Check ADB
    if ! command -v adb &> /dev/null; then
        echo -e "${WARN_YELLOW}⚠ ADB not found!${NC}"
        echo -e "${WARN_YELLOW}Install: sudo apt install adb${NC}"
        echo -e "${WARN_YELLOW}Or for wireless features, install: sudo apt install adb${NC}"
    else
        echo -e "${MATRIX_GREEN}✓ ADB found${NC}"
    fi
    
    # Check BlueZ (for Bluetooth features)
    if command -v hciconfig &> /dev/null; then
        echo -e "${MATRIX_GREEN}✓ BlueZ tools found${NC}"
    else
        echo -e "${WARN_YELLOW}⚠ BlueZ tools not found (for Bluetooth features)${NC}"
        echo -e "${WARN_YELLOW}Install: sudo apt install bluez bluez-utils${NC}"
    fi
    echo ""
}

# ─── Setup Virtual Environment ──────────────────────────────────────────────
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${MINT_GREEN}📦 Creating virtual environment...${NC}"
        python3 -m venv "$VENV_DIR"
        echo -e "${MATRIX_GREEN}✓ Virtual environment created${NC}"
    fi
    
    # Activate venv
    source "$VENV_DIR/bin/activate"
    
    # Install/update requirements
    echo -e "${MINT_GREEN}📦 Installing Python dependencies...${NC}"
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r "$PROJECT_DIR/requirements.txt" > /dev/null 2>&1
    echo -e "${MATRIX_GREEN}✓ Dependencies installed${NC}"
    echo ""
}

# ─── Check Connected Devices ─────────────────────────────────────────────────
check_devices() {
    echo -e "${MINT_GREEN}📱 Checking connected devices...${NC}"
    
    # Check if ADB is available
    if ! command -v adb &> /dev/null; then
        echo -e "${ALERT_RED}✗ ADB not available${NC}"
        echo -e "${WARN_YELLOW}Please install ADB first: sudo apt install adb${NC}"
        return 1
    fi
    
    # Get connected devices
    DEVICES=$(adb devices | grep -v "List" | grep -v "^$" | grep "device$" | wc -l)
    
    if [ "$DEVICES" -eq 0 ]; then
        echo -e "${WARN_YELLOW}⚠ No devices connected!${NC}"
        echo ""
        echo -e "${MINT_GREEN}Quick Connect Options:${NC}"
        echo -e "  ${MATRIX_GREEN}1.${NC} Connect via USB (then select option 8 for WiFi)"
        echo -e "  ${MATRIX_GREEN}2.${NC} Connect via WiFi: adb connect <IP>:5555"
        echo -e "  ${MATRIX_GREEN}3.${NC} Auto-discover: Select option 17 in menu"
        echo ""
        return 1
    else
        echo -e "${MATRIX_GREEN}✓ Found $DEVICES connected device(s)${NC}"
        adb devices | grep -v "List" | grep -v "^$" | grep "device$" | while read line; do
            SERIAL=$(echo $line | awk '{print $1}')
            echo -e "  ${MATRIX_GREEN}►${NC} ${CYBER_CYAN}$SERIAL${NC}"
        done
        echo ""
        return 0
    fi
}

# ─── Quick Remote Control ────────────────────────────────────────────────────
quick_remote() {
    echo -e "${MINT_GREEN}🎮 Starting GUI Remote Control...${NC}"
    
    # Check if any devices are connected
    DEVICE_COUNT=$(adb devices | grep -v "List" | grep -v "^$" | grep "device$" | wc -l)
    
    if [ "$DEVICE_COUNT" -eq 0 ]; then
        echo -e "${ALERT_RED}✗ No devices connected!${NC}"
        echo -e "${WARN_YELLOW}Please connect a device first.${NC}"
        echo ""
        echo -e "${MINT_GREEN}Quick options:${NC}"
        echo -e "  ${MATRIX_GREEN}1.${NC} Connect USB and run: ${BOLD}adb tcpip 5555${NC}"
        echo -e "  ${MATRIX_GREEN}2.${NC} Connect WiFi: ${BOLD}adb connect <IP>:5555${NC}"
        echo -e "  ${MATRIX_GREEN}3.${NC} Press Enter to run interactive menu"
        read -p "Press Enter to continue..."
        return 1
    fi
    
    # Get the first connected device
    SERIAL=$(adb devices | grep -v "List" | grep -v "^$" | grep "device$" | head -1 | awk '{print $1}')
    echo -e "${MATRIX_GREEN}✓ Using device: $SERIAL${NC}"
    
    # Check if it's a wireless connection
    if [[ "$SERIAL" == *":"* ]]; then
        IP=$(echo $SERIAL | cut -d':' -f1)
        PORT=$(echo $SERIAL | cut -d':' -f2)
        echo -e "${MATRIX_GREEN}✓ Wireless connection: $IP:$PORT${NC}"
        echo -e "${MINT_GREEN}Starting GUI remote...${NC}"
        $AXIOM_CMD --gui-remote --remote-ip "$IP" --remote-port "$PORT"
    else
        # USB connection - try to enable WiFi
        echo -e "${MINT_GREEN}📡 Enabling WiFi ADB on USB device...${NC}"
        echo -e "${WARN_YELLOW}Make sure WiFi is ON on your phone!${NC}"
        adb -s "$SERIAL" tcpip 5555
        sleep 2
        
        # Get IP
        IP=$(adb -s "$SERIAL" shell ip addr show wlan0 | grep -oP '(?<=inet )\d+\.\d+\.\d+\.\d+' | head -1)
        if [ -z "$IP" ]; then
            IP=$(adb -s "$SERIAL" shell ifconfig wlan0 | grep -oP '(?<=inet addr:)\d+\.\d+\.\d+\.\d+')
        fi
        
        if [ -n "$IP" ]; then
            echo -e "${MATRIX_GREEN}✓ WiFi ADB enabled at $IP:5555${NC}"
            echo -e "${WARN_YELLOW}⚠ Disconnect USB cable now, then press Enter...${NC}"
            read -p "Press Enter to continue..."
            
            # Connect wirelessly
            adb connect "$IP:5555"
            sleep 2
            
            echo -e "${MINT_GREEN}Starting GUI remote...${NC}"
            $AXIOM_CMD --gui-remote --remote-ip "$IP" --remote-port 5555
        else
            echo -e "${ALERT_RED}✗ Could not get IP address. Make sure WiFi is ON.${NC}"
            echo -e "${WARN_YELLOW}Starting interactive mode instead...${NC}"
            $AXIOM_CMD
        fi
    fi
}

# ─── Quick Screenshot ────────────────────────────────────────────────────────
quick_screenshot() {
    echo -e "${MINT_GREEN}📸 Taking screenshot...${NC}"
    
    DEVICE_COUNT=$(adb devices | grep -v "List" | grep -v "^$" | grep "device$" | wc -l)
    
    if [ "$DEVICE_COUNT" -eq 0 ]; then
        echo -e "${ALERT_RED}✗ No devices connected!${NC}"
        return 1
    fi
    
    SERIAL=$(adb devices | grep -v "List" | grep -v "^$" | grep "device$" | head -1 | awk '{print $1}')
    
    if [[ "$SERIAL" == *":"* ]]; then
        $AXIOM_CMD --remote-screenshot --remote-ip $(echo $SERIAL | cut -d':' -f1)
    else
        $AXIOM_CMD --screenshot --device "$SERIAL"
    fi
}

# ─── Main Menu ───────────────────────────────────────────────────────────────
show_menu() {
    print_banner
    
    # Check devices
    DEVICE_COUNT=$(adb devices 2>/dev/null | grep -v "List" | grep -v "^$" | grep "device$" | wc -l)
    if [ "$DEVICE_COUNT" -gt 0 ]; then
        echo -e "  ${MATRIX_GREEN}📱 $DEVICE_COUNT device(s) connected${NC}"
        echo ""
    else
        echo -e "  ${WARN_YELLOW}⚠ No devices connected${NC}"
        echo ""
    fi
    
    echo -e "${BOLD}${MINT_GREEN}⚡ Quick Actions:${NC}"
    echo -e "  ${MATRIX_GREEN}[1]${NC} 🎮 Start GUI Remote Control (auto-detect)"
    echo -e "  ${MATRIX_GREEN}[2]${NC} 📸 Take Screenshot"
    echo -e "  ${MATRIX_GREEN}[3]${NC} 🔍 Auto-Discover & Connect"
    echo -e "  ${MATRIX_GREEN}[4]${NC} 📡 Enable WiFi ADB (USB connected)"
    echo -e "  ${MATRIX_GREEN}[5]${NC} 🖥️  Full Interactive Menu"
    echo -e "  ${MATRIX_GREEN}[0]${NC} 🚪 Exit"
    echo ""
    echo -e "${BOLD}${DARK_EMERALD}───────────────────────────────────────────────────${NC}"
    echo -e "${BOLD}${CYBER_CYAN}Quick Commands:${NC}"
    echo -e "  ${MINT_GREEN}./axiom.sh --remote${NC}     → GUI Remote Control"
    echo -e "  ${MINT_GREEN}./axiom.sh --screenshot${NC} → Take Screenshot"
    echo -e "  ${MINT_GREEN}./axiom.sh --menu${NC}       → Full Interactive Menu"
    echo ""
    
    read -p "$(echo -e "${MINT_GREEN}Axiom ⚡ Select option: ${NC}")" choice
    
    case $choice in
        1)
            quick_remote
            ;;
        2)
            quick_screenshot
            ;;
        3)
            $AXIOM_CMD --auto-connect
            ;;
        4)
            echo -e "${MINT_GREEN}📡 Enabling WiFi ADB...${NC}"
            adb tcpip 5555
            echo -e "${MATRIX_GREEN}✓ WiFi ADB enabled on port 5555${NC}"
            echo -e "${WARN_YELLOW}Get IP from phone: Settings → About Phone → Status${NC}"
            echo -e "${MINT_GREEN}Then connect: adb connect <IP>:5555${NC}"
            read -p "Press Enter to continue..."
            ;;
        5)
            $AXIOM_CMD
            ;;
        0)
            echo -e "${MATRIX_GREEN}⚡ Exiting Axiom. Stay ethical!${NC}"
            exit 0
            ;;
        *)
            echo -e "${ALERT_RED}Invalid option${NC}"
            read -p "Press Enter to continue..."
            ;;
    esac
    
    show_menu
}

# ─── Command Line Arguments ──────────────────────────────────────────────────
case "$1" in
    --remote|-r)
        setup_venv
        check_dependencies
        quick_remote
        ;;
    --screenshot|-s)
        setup_venv
        check_dependencies
        quick_screenshot
        ;;
    --menu|-m)
        setup_venv
        $AXIOM_CMD
        ;;
    --help|-h)
        echo "Axiom Launcher (Matrix Edition)"
        echo ""
        echo "Usage: ./axiom.sh [OPTION]"
        echo ""
        echo "Options:"
        echo "  --remote, -r    Start GUI Remote Control (auto-detect)"
        echo "  --screenshot, -s Take screenshot"
        echo "  --menu, -m      Open full interactive menu"
        echo "  --help, -h      Show this help"
        echo ""
        echo "Without arguments, opens interactive menu"
        ;;
    *)
        # No arguments - show menu
        setup_venv
        check_dependencies
        show_menu
        ;;
esac