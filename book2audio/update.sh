#!/bin/bash
# book2audio update script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

INSTALL_DIR="$HOME/.book2audio"
GITHUB_REPO="https://github.com/username/book2audio.git"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           book2audio புதுப்பிப்பு கருவி                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if installed
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${RED}[✗] book2audio நிறுவப்படவில்லை${NC}"
    echo "    முதலில் install.sh ஐ இயக்கவும்"
    exit 1
fi

# Check internet connection
echo -e "${BLUE}[*] இணைய இணைப்பை சரிபார்க்கிறது...${NC}"
if ! ping -c 1 github.com &> /dev/null; then
    echo -e "${RED}[✗] இணைய இணைப்பு கிடைக்கவில்லை${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] இணைய இணைப்பு சரி${NC}"

# Backup current installation
echo -e "${BLUE}[*] தற்போதைய நிறுவலை காப்புப்பிரதி எடுக்கிறது...${NC}"
BACKUP_DIR="$HOME/.book2audio_backup_$(date +%Y%m%d_%H%M%S)"
cp -r "$INSTALL_DIR" "$BACKUP_DIR"
echo -e "${GREEN}[✓] காப்புப்பிரதி: ${BACKUP_DIR}${NC}"

# Clone or pull latest changes
echo -e "${BLUE}[*] சமீபத்திய பதிப்பைப் பெறுகிறது...${NC}"

TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

if git clone "$GITHUB_REPO" book2audio_temp 2>/dev/null; then
    cd book2audio_temp
    
    # Update installation
    cp book2audio.py "$INSTALL_DIR/"
    cp update.sh "$INSTALL_DIR/" 2>/dev/null || true
    cp uninstall.sh "$INSTALL_DIR/" 2>/dev/null || true
    
    # Make executable
    chmod +x "$INSTALL_DIR/book2audio.py"
    chmod +x "$INSTALL_DIR/update.sh" 2>/dev/null || true
    chmod +x "$INSTALL_DIR/uninstall.sh" 2>/dev/null || true
    
    # Update wrapper script
    cat > "$INSTALL_DIR/book2audio" << 'EOF'
#!/bin/bash
# book2audio wrapper script
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
exec python3 "$SCRIPT_DIR/book2audio.py" "$@"
EOF
    chmod +x "$INSTALL_DIR/book2audio"
    
    # Update Python packages
    echo -e "${BLUE}[*] Python தொகுப்புகளை புதுப்பிக்கிறது...${NC}"
    python3 -m pip install --upgrade gTTS langdetect beautifulsoup4 python-docx markdown odfpy pydub --quiet 2>/dev/null || true
    
    echo -e "${GREEN}[✓] பயன்பாடு வெற்றிகரமாக புதுப்பிக்கப்பட்டது!${NC}"
    
    # Cleanup
    cd /
    rm -rf "$TEMP_DIR"
    
    # Show version
    echo ""
    echo -e "${CYAN}புதுப்பிக்கப்பட்ட பதிப்பு:${NC}"
    python3 "$INSTALL_DIR/book2audio.py" --help 2>/dev/null | head -5
    
else
    echo -e "${RED}[✗] GitHub இருப்பிடத்திலிருந்து பதிவேற்ற முடியவில்லை${NC}"
    echo "    காப்புப்பிரதியை மீட்டெடுக்கிறது..."
    rm -rf "$INSTALL_DIR"
    cp -r "$BACKUP_DIR" "$INSTALL_DIR"
    echo -e "${YELLOW}[!] காப்புப்பிரதி மீட்டெடுக்கப்பட்டது${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Cleanup backup after successful update
echo -e "${BLUE}[*] காப்புப்பிரதியை சுத்தம் செய்கிறது...${NC}"
rm -rf "$BACKUP_DIR"

echo ""
echo -e "${GREEN}புதுப்பிப்பு முடிந்தது! 🎉${NC}"
echo -e "${CYAN}பயன்பாடு: book2audio -h${NC}"
