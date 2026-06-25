#!/usr/bin/env bash

# Axiom Launcher Script
# Resolves the script directory even if run via symlink
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

# Force Python to use UTF-8 mode for stdout/stderr (prevents UnicodeEncodeError)
export PYTHONUTF8=1

# Use .venv for Unix/Linux/WSL to keep it isolated from Windows
VENV_DIR="$SCRIPT_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python3"

# Check for python3 in the system path
if ! command -v python3 &> /dev/null; then
    echo -e "\e[31m[!] Error: python3 is not installed or not in PATH.\e[0m"
    exit 1
fi

# Auto-setup virtual environment if missing
if [ ! -d "$VENV_DIR" ]; then
    echo -e "\e[34m[*] Python virtual environment not found. Creating one at $VENV_DIR...\e[0m"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "\e[31m[!] Failed to create virtual environment.\e[0m"
        exit 1
    fi
fi

# Upgrade pip and install dependencies if 'rich' isn't available in the venv
if ! "$VENV_PYTHON" -c "import rich" &> /dev/null; then
    echo -e "\e[34m[*] Installing required dependencies in virtual environment...\e[0m"
    "$VENV_PYTHON" -m pip install --upgrade pip
    "$VENV_PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt"
    if [ $? -ne 0 ]; then
        echo -e "\e[31m[!] Dependency installation failed.\e[0m"
        exit 1
    fi
fi

# Run Axiom using the virtual environment's python directly
"$VENV_PYTHON" "$SCRIPT_DIR/axiom.py" "$@"
