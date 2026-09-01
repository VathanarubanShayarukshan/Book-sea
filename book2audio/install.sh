#!/bin/bash
# book2audio installer script
# Supports: Termux, Kali Linux, Ubuntu, Debian, and derivatives

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║        _            _     _   _                _            ║"
echo "║       | |          | |   | | | |              | |           ║"
echo "║   ___ | | _____  __| | __| | | |__   __ _  __| | ___  _ __ ║"
echo "║  / _ \| |/ \\/ /|__  |/ _\` | | '_ \ / _\` |/ _\` |/ _ \| '_ \║"
echo "║ | (_) |   <  <   | | | (_| | | | | | (_| | (_| | (_) | | |║║"
echo "║  \___/|_|\_/\_\  |_|\__,_|_|_| |_|\__,_|\__,_|\___/|_| |_|║"
echo "║                                                            ║"
echo "║         Convert Books to Audio Files v1.0.0                ║"
echo "║                                                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Installation directory
INSTALL_DIR="$HOME/.book2audio"
BIN_DIR="/usr/local/bin"
SCRIPT_NAME="book2audio"

echo -e "${BLUE}[*] நிறுவல் தொடங்குகிறது...${NC}"

# Check if running as root (not required, but helpful)
check_root() {
    if [ "$EUID" -eq 0 ]; then
        ROOT_MODE=true
        echo -e "${YELLOW}[!] Root முறையில் இயக்கப்படுகிறது${NC}"
    else
        ROOT_MODE=false
    fi
}

# Detect package manager
detect_package_manager() {
    if command -v apt-get &> /dev/null; then
        PKG_MANAGER="apt-get"
        PKG_INSTALL="apt-get install -y"
    elif command -v pkg &> /dev/null; then
        PKG_MANAGER="pkg"
        PKG_INSTALL="pkg install -y"
    elif command -v pacman &> /dev/null; then
        PKG_MANAGER="pacman"
        PKG_INSTALL="pacman -S --noconfirm"
    elif command -v dnf &> /dev/null; then
        PKG_MANAGER="dnf"
        PKG_INSTALL="dnf install -y"
    elif command -v yum &> /dev/null; then
        PKG_MANAGER="yum"
        PKG_INSTALL="yum install -y"
    else
        echo -e "${RED}[✗] தொகுப்பு மேலாளர் கிடைக்கவில்லை${NC}"
        exit 1
    fi
    echo -e "${GREEN}[✓] தொகுப்பு மேலாளர்: ${PKG_MANAGER}${NC}"
}

# Check and install Python
check_python() {
    echo -e "${BLUE}[*] Python சரிபார்க்கிறது...${NC}"
    
    if command -v python3 &> /dev/null; then
        PYTHON=python3
        PIP=pip3
    elif command -v python &> /dev/null; then
        PYTHON=python
        PIP=pip
    else
        echo -e "${YELLOW}[!] Python நிறுவப்படவில்லை, நிறுவுகிறது...${NC}"
        $PKG_INSTALL python python-pip
        PYTHON=python3
        PIP=pip3
    fi
    
    # Check if externally managed (PEP 668)
    EXTERNALLY_MANAGED=""
    if [ -f "/usr/lib/python3.13/EXTERNALLY-MANAGED" ] || [ -f "/usr/lib/python3.12/EXTERNALLY-MANAGED" ] || [ -f "/usr/lib/python3.11/EXTERNALLY-MANAGED" ]; then
        EXTERNALLY_MANAGED="--break-system-packages"
        echo -e "${YELLOW}[!] Python externally managed, using --break-system-packages${NC}"
    fi
    
    echo -e "${GREEN}[✓] Python பதிப்பு: $($PYTHON --version)${NC}"
}

# Check and install pip packages
install_pip_packages() {
    echo -e "${BLUE}[*] Python தொகுப்புகளை நிறுவுகிறது...${NC}"
    
    # Upgrade pip first
    $PYTHON -m pip install --upgrade pip $EXTERNALLY_MANAGED --quiet 2>/dev/null || true
    
    # Required packages
    PACKAGES=(
        "gTTS"
        "langdetect"
        "beautifulsoup4"
        "python-docx"
        "markdown"
        "odfpy"
        "pydub"
        "edge-tts"
        "PyPDF2"
    )
    
    for package in "${PACKAGES[@]}"; do
        echo -ne "    நிறுவுகிறது: ${package}... "
        $PYTHON -m pip install "$package" $EXTERNALLY_MANAGED --quiet 2>/dev/null && \
            echo -e "${GREEN}✓${NC}" || \
            echo -e "${YELLOW}⚠ மேம்படுத்தல் தேவை${NC}"
    done
    
    echo -e "${GREEN}[✓] Python தொகுப்புகள் நிறுவப்பட்டன${NC}"
}

# Check and install ffmpeg
check_ffmpeg() {
    echo -e "${BLUE}[*] ffmpeg சரிபார்க்கிறது...${NC}"
    
    if command -v ffmpeg &> /dev/null; then
        echo -e "${GREEN}[✓] ffmpeg ஏற்கனவே நிறுவப்பட்டுள்ளது${NC}"
    else
        echo -e "${YELLOW}[!] ffmpeg நிறுவப்படவில்லை, நிறுவுகிறது...${NC}"
        $PKG_INSTALL ffmpeg
        echo -e "${GREEN}[✓] ffmpeg நிறுவப்பட்டது${NC}"
    fi
}

# Create installation directory
create_install_dir() {
    echo -e "${BLUE}[*] நிறுவல் கோப்பகத்தை உருவாக்குகிறது: ${INSTALL_DIR}${NC}"
    mkdir -p "$INSTALL_DIR"
}

# Copy files
copy_files() {
    echo -e "${BLUE}[*] கோப்புகளை நகலெடுக்கிறது...${NC}"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Copy main script
    cp "$SCRIPT_DIR/book2audio.py" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/book2audio.py"
    
    # Copy update and uninstall scripts
    cp "$SCRIPT_DIR/update.sh" "$INSTALL_DIR/" 2>/dev/null || true
    cp "$SCRIPT_DIR/uninstall.sh" "$INSTALL_DIR/" 2>/dev/null || true
    chmod +x "$INSTALL_DIR/update.sh" 2>/dev/null || true
    chmod +x "$INSTALL_DIR/uninstall.sh" 2>/dev/null || true
    
    echo -e "${GREEN}[✓] கோப்புகள் நகலெடுக்கப்பட்டன${NC}"
}

# Create symlink
create_symlink() {
    echo -e "${BLUE}[*] குறுக்குவழியை உருவாக்குகிறது...${NC}"
    
    # Create wrapper script with proper Python path
    cat > "$INSTALL_DIR/$SCRIPT_NAME" << EOF
#!/bin/bash
# book2audio wrapper script
exec $PYTHON "$INSTALL_DIR/book2audio.py" "\$@"
EOF
    chmod +x "$INSTALL_DIR/$SCRIPT_NAME"
    
    # Create symlink in PATH
    if [ "$ROOT_MODE" = true ]; then
        ln -sf "$INSTALL_DIR/$SCRIPT_NAME" "$BIN_DIR/$SCRIPT_NAME"
        # Also create in /usr/bin if /usr/local/bin not in PATH
        if ! echo "$PATH" | grep -q "/usr/local/bin"; then
            ln -sf "$INSTALL_DIR/$SCRIPT_NAME" "/usr/bin/$SCRIPT_NAME"
        fi
    else
        # For non-root users, add to user's local bin
        LOCAL_BIN="$HOME/.local/bin"
        mkdir -p "$LOCAL_BIN"
        ln -sf "$INSTALL_DIR/$SCRIPT_NAME" "$LOCAL_BIN/$SCRIPT_NAME"
        
        # Add to PATH if not already there
        if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.bashrc"
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$HOME/.profile" 2>/dev/null || true
            echo -e "${YELLOW}[!] PATH புதுப்பிக்கப்பட்டது. புதிய டெர்மினலைத் திறக்கவும்.${NC}"
        fi
    fi
    
    echo -e "${GREEN}[✓] குறுக்குவழி உருவாக்கப்பட்டது${NC}"
}

# Test installation
test_installation() {
    echo -e "${BLUE}[*] நிறுவலை சோதிக்கிறது...${NC}"
    
    if command -v book2audio &> //null; then
        echo -e "${GREEN}[✓] book2audio வெற்றிகரமாக நிறுவப்பட்டது!${NC}"
        echo ""
        echo -e "${CYAN}பயன்பாட்டு எடுத்துக்காட்டுகள்:${NC}"
        echo "    book2audio -h              # உதவி மெனு"
        echo "    book2audio -lh             # மொழி பட்டியல்"
        echo "    book2audio -i book.txt -o audiobook.mp3  # மாற்றம்"
        echo ""
        echo -e "${GREEN}நிறுவல் முடிந்தது! 🎉${NC}"
    else
        echo -e "${YELLOW}[!] குறுக்குவழி கிடைக்கவில்லை, ஆனால் நிறுவல் முடிந்தது${NC}"
        echo ""
        echo -e "${CYAN}பயன்படுத்த:${NC}"
        echo "    python3 $INSTALL_DIR/book2audio.py -h"
        echo ""
        echo -e "${CYAN}அல்லது PATH-இல் சேர்:${NC}"
        echo "    export PATH=\"\$PATH:$INSTALL_DIR\""
        echo "    book2audio -h"
    fi
}

# Main installation function
main() {
    check_root
    detect_package_manager
    check_python
    check_ffmpeg
    install_pip_packages
    create_install_dir
    copy_files
    create_symlink
    test_installation
}

# Run installation
main
