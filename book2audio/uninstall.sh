#!/bin/bash
# book2audio uninstall script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

INSTALL_DIR="$HOME/.book2audio"
BIN_DIR="/usr/local/bin"
LOCAL_BIN="$HOME/.local/bin"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          book2audio நீக்கும் கருவி                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Confirmation
echo -e "${YELLOW}நீங்கள் book2audio ஐ நிச்சயமாக நீக்க விரும்புகிறீர்களா?${NC}"
echo ""
echo "நீக்கப்படும் கோப்புகள்:"
echo "    - $INSTALL_DIR"
echo "    - /usr/local/bin/book2audio (அல்லது ~/.local/bin/book2audio)"
echo ""
read -p "தொடரவா? (y/n): " -n 1 -r
echo ""
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}நீக்கல் ரத்து செய்யப்பட்டது${NC}"
    exit 0
fi

echo -e "${BLUE}[*] book2audio ஐ நீக்குகிறது...${NC}"

# Remove symlink from /usr/local/bin
if [ -f "$BIN_DIR/book2audio" ] || [ -L "$BIN_DIR/book2audio" ]; then
    rm -f "$BIN_DIR/book2audio"
    echo -e "${GREEN}[✓] $BIN_DIR/book2audio நீக்கப்பட்டது${NC}"
fi

# Remove symlink from ~/.local/bin
if [ -f "$LOCAL_BIN/book2audio" ] || [ -L "$LOCAL_BIN/book2audio" ]; then
    rm -f "$LOCAL_BIN/book2audio"
    echo -e "${GREEN}[✓] $LOCAL_BIN/book2audio நீக்கப்பட்டது${NC}"
fi

# Remove installation directory
if [ -d "$INSTALL_DIR" ]; then
    rm -rf "$INSTALL_DIR"
    echo -e "${GREEN}[✓] $INSTALL_DIR நீக்கப்பட்டது${NC}"
fi

# Remove PATH entry from bashrc/profile if added by installer
if [ -f "$HOME/.bashrc" ]; then
    sed -i '/\.local\/bin/d' "$HOME/.bashrc" 2>/dev/null || true
fi
if [ -f "$HOME/.profile" ]; then
    sed -i '/\.local\/bin/d' "$HOME/.profile" 2>/dev/null || true
fi

echo ""
echo -e "${GREEN}[✓] book2audio வெற்றிகரமாக நீக்கப்பட்டது!${NC}"
echo ""
echo -e "${CYAN}மீண்டும் நிறுவ: install.sh ஐ இயக்கவும்${NC}"
