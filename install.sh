#!/usr/bin/env bash
# ==============================================================================
#  Axiom — One-Click Terminal Installer for Linux, WSL, & macOS
#  Author: Abdul Salam | Salamcs.app
# ==============================================================================

set -e

# Colors
GREEN='\033[38;5;46m'
MINT='\033[38;5;48m'
CYBER='\033[38;5;51m'
YELLOW='\033[38;5;220m'
RED='\033[38;5;196m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

clear
echo -e "${GREEN}"
echo ' █████╗ ██╗  ██╗██╗ ██████╗ ███╗   ███╗'
echo '██╔══██╗╚██╗██╔╝██║██╔═══██╗████╗ ████║'
echo '███████║ ╚███╔╝ ██║██║   ██║██╔████╔██║'
echo '██╔══██║ ██╔██╗ ██║██║   ██║██║╚██╔╝██║'
echo '██║  ██║██╔╝ ██╗██║╚██████╔╝██║ ╚═╝ ██║'
echo '╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝     ╚═╝'
echo -e "${NC}"
echo -e "${MINT}${BOLD}⚡ AXIOM TERMINAL INSTALLER (LINUX / WSL / MACOS) ⚡${NC}"
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo ""

# 1. Detect environment
INSTALL_DIR="$HOME/.axiom"
BIN_DIR="$HOME/.local/bin"
REPO_URL="https://github.com/abdulsalam401/Axiom.git"

echo -e "${CYBER}🔍 [1/5] Checking environment and dependencies...${NC}"

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is required but not installed.${NC}"
    echo -e "${YELLOW}Install with:${NC} sudo apt update && sudo apt install -y python3 python3-pip python3-venv"
    exit 1
fi

PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Python $PY_VER detected${NC}"

# Check Git
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}⚠ Git not found. Attempting to install or use local directory...${NC}"
fi

# Check ADB
if command -v adb &> /dev/null; then
    echo -e "${GREEN}✓ ADB (Android Debug Bridge) detected${NC}"
else
    echo -e "${YELLOW}⚠ ADB not found. Recommended to install:${NC} sudo apt install adb (or android-platform-tools)"
fi

# 2. Setup directory
echo ""
echo -e "${CYBER}📦 [2/5] Setting up Axiom files in ${INSTALL_DIR}...${NC}"

# Check if we are running inside an existing Axiom clone
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || echo "")"

if [ -f "$CURRENT_DIR/axiom.py" ]; then
    echo -e "${GREEN}✓ Using local source directory: $CURRENT_DIR${NC}"
    TARGET_SRC="$CURRENT_DIR"
else
    if [ -d "$INSTALL_DIR/.git" ]; then
        echo -e "${MINT}Updating existing Axiom installation...${NC}"
        cd "$INSTALL_DIR" && git pull --quiet
    else
        echo -e "${MINT}Cloning Axiom from GitHub...${NC}"
        rm -rf "$INSTALL_DIR"
        git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
    fi
    TARGET_SRC="$INSTALL_DIR"
fi

# 3. Setup Python Virtual Environment
echo ""
echo -e "${CYBER}🐍 [3/5] Configuring isolated virtual environment...${NC}"
VENV_DIR="$TARGET_SRC/venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet
pip install -r "$TARGET_SRC/requirements.txt" --quiet
pip install -e "$TARGET_SRC" --quiet
echo -e "${GREEN}✓ Virtual environment and packages installed${NC}"

# 4. Create Global Launcher Command
echo ""
echo -e "${CYBER}🚀 [4/5] Creating global 'axiom' command in ${BIN_DIR}...${NC}"
mkdir -p "$BIN_DIR"

LAUNCHER_SCRIPT="$BIN_DIR/axiom"
cat << 'EOF' > "$LAUNCHER_SCRIPT"
#!/usr/bin/env bash
TARGET_DIR="__AXIOM_TARGET_DIR__"
source "$TARGET_DIR/venv/bin/activate"
export PYTHONIOENCODING="utf-8"
exec python3 "$TARGET_DIR/axiom.py" "$@"
EOF

# Substitute actual path
sed -i "s|__AXIOM_TARGET_DIR__|$TARGET_SRC|g" "$LAUNCHER_SCRIPT"
chmod +x "$LAUNCHER_SCRIPT"

# Also try /usr/local/bin if running as root or with sudo
if [ "$EUID" -eq 0 ]; then
    cp "$LAUNCHER_SCRIPT" /usr/local/bin/axiom
    chmod +x /usr/local/bin/axiom
    echo -e "${GREEN}✓ Global symlink created at /usr/local/bin/axiom${NC}"
fi

# 5. Ensure ~/.local/bin is in PATH
echo ""
echo -e "${CYBER}🔧 [5/5] Ensuring PATH configuration...${NC}"

ensure_path() {
    local rc_file="$1"
    if [ -f "$rc_file" ]; then
        if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$rc_file"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc_file"
            echo -e "${GREEN}✓ Added ~/.local/bin to $rc_file${NC}"
        fi
    fi
}

ensure_path "$HOME/.bashrc"
ensure_path "$HOME/.zshrc"
ensure_path "$HOME/.profile"

export PATH="$HOME/.local/bin:$PATH"

echo ""
echo -e "${GREEN}═════════════════════════════════════════════════════════════════${NC}"
echo -e "${MINT}${BOLD}✓ AXIOM SUCCESSFULLY INSTALLED!${NC}"
echo -e "${GREEN}═════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "You can now launch Axiom from ${BOLD}ANY terminal${NC} simply by typing:"
echo ""
echo -e "    ${GREEN}${BOLD}axiom${NC}"
echo ""
echo -e "Or run with specific flags:"
echo -e "    ${MINT}axiom --help${NC}"
echo -e "    ${MINT}axiom --devices${NC}"
echo -e "    ${MINT}axiom --remote${NC}"
echo ""
echo -e "${DIM}If the 'axiom' command is not recognized immediately, restart your terminal or run:${NC}"
echo -e "    ${CYBER}source ~/.bashrc${NC}  (or source ~/.zshrc)"
echo ""
