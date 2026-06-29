#!/bin/bash
# Axiom Launcher Script
# Author: Abdul Salam | Salamcs.app
# Description: One-click launcher for Axiom Android Security Framework

set -e

# ─── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# ─── Configuration ──────────────────────────────────────────────────────────
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_CMD="python3"
AXIOM_CMD="$PYTHON_CMD axiom.py"

# ─── Banner ──────────────────────────────────────────────────────────────────
print_banner() {
    clear
    echo -e "${MAGENTA}"
    echo '    _    __  __ _   ___   __  __ '
    echo '   / \   \ \/ /| | / _ \ |  \/  |'
    echo '  / _ \   \  / | || | | || |\/| |'
    echo ' / ___ \   /  \| || |_| || |  | |'
    echo '/_/   \_\ /_/\_\_| \___/ |_|  |_|'
    echo -e "${NC}"
    echo -e "${CYAN}◈ ADVANCED ANDROID SECURITY FRAMEWORK ◈${NC}"
    echo -e "${YELLOW}Author: Abdul Salam | Salamcs.app${NC}"
    echo ""
}

# ─── Check Dependencies ──────────────────────────────────────────────────────
check_dependencies() {
    echo -e "${CYAN}🔍 Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python3 not found!${NC}"
        echo -e "${YELLOW}Install: sudo apt install python3 python3-pip python3-venv${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Python3 found${NC}"
    
    # Check ADB
    if ! command -v adb &> /dev/null; then
        echo -e "${YELLOW}⚠ ADB not found!${NC}"
        echo -e "${YELLOW}Install: sudo apt install adb${NC}"
        echo -e "${YELLOW}Or for wireless features, install: sudo apt install adb${NC}"
    else
        echo -e "${GREEN}✓ ADB found${NC}"
    fi
    
    # Check BlueZ (for Bluetooth features)
    if command -v hciconfig &> /dev/null; then
        echo -e "${GREEN}✓ BlueZ tools found${NC}"
    else
        echo -e "${YELLOW}⚠ BlueZ tools not found (for Bluetooth features)${NC}"
        echo -e "${YELLOW}Install: sudo apt install bluez bluez-utils${NC}"
    fi
    echo ""
}

# ─── Setup Virtual Environment ──────────────────────────────────────────────
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${CYAN}📦 Creating virtual environment...${NC}"
        python3 -m venv "$VENV_DIR"
        echo -e "${GREEN}✓ Virtual environment created${NC}"
    fi
    
    # Activate venv
    source "$VENV_DIR/bin/activate"
    
    # Install/update requirements
    echo -e "${CYAN}📦 Installing Python dependencies...${NC}"
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r "$PROJECT_DIR/requirements.txt" > /dev/null 2>&1
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    echo ""
}

# ─── Check Connected Devices ─────────────────────────────────────────────────
check_devices() {
    echo -e "${CYAN}📱 Checking connected devices...${NC}"
    
    # Check if ADB is available
    if ! command -v adb &> /dev/null; then
        echo -e "${RED}✗ ADB not available${NC}"
        echo -e "${YELLOW}Please install ADB first: sudo apt install adb${NC}"
        return 1
    fi
    
    # Get connected devices
    DEVICES=$(adb devices | grep -v "List" | grep -v "^$" | grep "device$" | wc -l)
    
    if [ "$DEVICES" -eq 0 ]; then
        echo -e "${YELLOW}⚠ No devices connected!${NC}"
        echo ""
        echo -e "${CYAN}Quick Connect Options:${NC}"
        echo -e "  ${GREEN}1.${NC} Connect via USB (then select option 8 for WiFi)"
        echo -e "  ${GREEN}2.${NC} Connect via WiFi: adb connect <IP>:5555"
        echo -e "  ${GREEN}3.${NC} Auto-discover: Select option 17 in menu"
        echo ""
        return 1
    else
        echo -e "${GREEN}✓ Found $DEVICES connected device(s)${NC}"
        adb devices | grep -v "List" | grep -v "^$" | grep "device$" | while read line; do
            SERIAL=$(echo $line | awk '{print $1}')
            echo -e "  ${CYAN}►${NC} $SERIAL"
        done
        echo ""
        return 0
    fi
}

# ─── Quick Remote Control ────────────────────────────────────────────────────
quick_remote() {
    echo -e "${CYAN}🎮 Starting GUI Remote Control...${NC}"
    
    # Check if any devices are connected
    DEVICE_COUNT=$(adb devices | grep -v "List" | grep -v "^$" | grep "device$" | wc -l)
    
    if [ "$DEVICE_COUNT" -eq 0 ]; then
        echo -e "${RED}✗ No devices connected!${NC}"
        echo -e "${YELLOW}Please connect a device first.${NC}"
        echo ""
        echo -e "${CYAN}Quick options:${NC}"
        echo -e "  ${GREEN}1.${NC} Connect USB and run: ${BOLD}adb tcpip 5555${NC}"
        echo -e "  ${GREEN}2.${NC} Connect WiFi: ${BOLD}adb connect <IP>:5555${NC}"
        echo -e "  ${GREEN}3.${NC} Press Enter to run interactive menu"
        read -p "Press Enter to continue..."
        return 1
    fi
    
    # Get the first connected device
    SERIAL=$(adb devices | grep -v "List" | grep -v "^$" | grep "device$" | head -1 | awk '{print $1}')
    echo -e "${GREEN}✓ Using device: $SERIAL${NC}"
    
    # Check if it's a wireless connection
    if [[ "$SERIAL" == *":"* ]]; then
        IP=$(echo $SERIAL | cut -d':' -f1)
        PORT=$(echo $SERIAL | cut -d':' -f2)
        echo -e "${GREEN}✓ Wireless connection: $IP:$PORT${NC}"
        echo -e "${CYAN}Starting GUI remote...${NC}"
        $AXIOM_CMD --gui-remote --remote-ip "$IP" --remote-port "$PORT"
    else
        # USB connection - try to enable WiFi
        echo -e "${CYAN}📡 Enabling WiFi ADB on USB device...${NC}"
        echo -e "${YELLOW}Make sure WiFi is ON on your phone!${NC}"
        adb -s "$SERIAL" tcpip 5555
        sleep 2
        
        # Get IP
        IP=$(adb -s "$SERIAL" shell ip addr show wlan0 | grep -oP '(?<=inet )\d+\.\d+\.\d+\.\d+' | head -1)
        if [ -z "$IP" ]; then
            IP=$(adb -s "$SERIAL" shell ifconfig wlan0 | grep -oP '(?<=inet addr:)\d+\.\d+\.\d+\.\d+')
        fi
        
        if [ -n "$IP" ]; then
            echo -e "${GREEN}✓ WiFi ADB enabled at $IP:5555${NC}"
            echo -e "${YELLOW}⚠ Disconnect USB cable now, then press Enter...${NC}"
            read -p "Press Enter to continue..."
            
            # Connect wirelessly
            adb connect "$IP:5555"
            sleep 2
            
            echo -e "${CYAN}Starting GUI remote...${NC}"
            $AXIOM_CMD --gui-remote --remote-ip "$IP" --remote-port 5555
        else
            echo -e "${RED}✗ Could not get IP address. Make sure WiFi is ON.${NC}"
            echo -e "${YELLOW}Starting interactive mode instead...${NC}"
            $AXIOM_CMD
        fi
    fi
}

# ─── Quick Screenshot ────────────────────────────────────────────────────────
quick_screenshot() {
    echo -e "${CYAN}📸 Taking screenshot...${NC}"
    
    DEVICE_COUNT=$(adb devices | grep -v "List" | grep -v "^$" | grep "device$" | wc -l)
    
    if [ "$DEVICE_COUNT" -eq 0 ]; then
        echo -e "${RED}✗ No devices connected!${NC}"
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
        echo -e "  ${GREEN}📱 $DEVICE_COUNT device(s) connected${NC}"
        echo ""
    else
        echo -e "  ${YELLOW}⚠ No devices connected${NC}"
        echo ""
    fi
    
    echo -e "${BOLD}${CYAN}Quick Actions:${NC}"
    echo -e "  ${GREEN}1.${NC} 🎮 Start GUI Remote Control (auto-detect)"
    echo -e "  ${GREEN}2.${NC} 📸 Take Screenshot"
    echo -e "  ${GREEN}3.${NC} 🔍 Auto-Discover & Connect"
    echo -e "  ${GREEN}4.${NC} 📡 Enable WiFi ADB (USB connected)"
    echo -e "  ${GREEN}5.${NC} 🖥️  Full Interactive Menu"
    echo -e "  ${GREEN}0.${NC} 🚪 Exit"
    echo ""
    echo -e "${BOLD}${BLUE}Quick Commands:${NC}"
    echo -e "  ${CYAN}./axiom.sh --remote${NC}  → GUI Remote Control"
    echo -e "  ${CYAN}./axiom.sh --screenshot${NC} → Take Screenshot"
    echo -e "  ${CYAN}./axiom.sh --menu${NC}      → Full Interactive Menu"
    echo ""
    
    read -p "$(echo -e ${CYAN}Select option: ${NC})" choice
    
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
            echo -e "${CYAN}📡 Enabling WiFi ADB...${NC}"
            adb tcpip 5555
            echo -e "${GREEN}✓ WiFi ADB enabled on port 5555${NC}"
            echo -e "${YELLOW}Get IP from phone: Settings → About Phone → Status${NC}"
            echo -e "${CYAN}Then connect: adb connect <IP>:5555${NC}"
            read -p "Press Enter to continue..."
            ;;
        5)
            $AXIOM_CMD
            ;;
        0)
            echo -e "${GREEN}👋 Exiting. Stay ethical!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
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
        echo "Axiom Launcher"
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