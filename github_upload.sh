#!/bin/bash
# Git-Upload-Skript für 360° Drehteller Projekt

# Farbcodes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Aktuelles Datum und Uhrzeit für Branch-Namen
BRANCH_NAME="web-vom-$(date +%d-%m-%y_%H-%M)"

# Projektverzeichnis
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# GitHub-Repository-URL
REPO_URL="https://github.com/alexanderbehrens1978/drehteller_360_grad_fotos.git"

# Zum Projektverzeichnis wechseln
cd "$PROJECT_DIR"

# Git-Konfiguration
git config --global user.name "Alexander Behrens"
git config --global user.email "axellander@web.de"

# Initialisiere Repository, falls nicht vorhanden
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Initialisiere Git-Repository...${NC}"
    git init
fi

# .gitignore erstellen/aktualisieren
echo -e "${YELLOW}Erstelle/aktualisiere .gitignore${NC}"
cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
myenv/
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Flask
instance/
.webassets-cache

# Captured Images and Generated Files
static/photos/*
static/sample_images/*
!static/photos/.gitkeep
!static/sample_images/.gitkeep

# Environment
.env
.venv
env/
venv/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# OS specific
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
EOL

# Leere .gitkeep Dateien für Verzeichnisse erstellen
mkdir -p static/photos static/sample_images
touch static/photos/.gitkeep static/sample_images/.gitkeep

# Dateien stagen
echo -e "${YELLOW}Füge Dateien zum Commit hinzu...${NC}"
git add .

# Status prüfen, ob es etwas zu committen gibt
if git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}Keine Änderungen zum Committen vorhanden.${NC}"
    HAS_CHANGES=false
else
    HAS_CHANGES=true
fi

# Commit-Nachricht
COMMIT_MESSAGE="Update vom $(date '+%d.%m.%Y %H:%M') - Web-Version"

# Commit erstellen, wenn es Änderungen gibt
if $HAS_CHANGES; then
    echo -e "${GREEN}Erstelle Commit: ${COMMIT_MESSAGE}${NC}"
    git commit -m "$COMMIT_MESSAGE"
else
    echo -e "${YELLOW}Überspringe Commit, da keine Änderungen vorhanden sind.${NC}"
fi

# Neuen Branch erstellen und wechseln
echo -e "${GREEN}Erstelle neuen Branch: ${BRANCH_NAME}${NC}"
git checkout -b "$BRANCH_NAME"

# Remote-Konfiguration prüfen
CURRENT_REMOTE=$(git config --get remote.origin.url || echo "")

if [ -z "$CURRENT_REMOTE" ]; then
    # Remote hinzufügen (falls nicht vorhanden)
    echo -e "${YELLOW}Füge Remote-Repository hinzu...${NC}"
    git remote add origin "$REPO_URL"
elif [ "$CURRENT_REMOTE" != "$REPO_URL" ]; then
    # Remote-URL aktualisieren, wenn sie sich geändert hat
    echo -e "${YELLOW}Aktualisiere Remote-Repository-URL...${NC}"
    git remote set-url origin "$REPO_URL"
fi

# Push zum GitHub-Repository
echo -e "${YELLOW}Pushe zum GitHub-Repository...${NC}"
if git push -u origin "$BRANCH_NAME"; then
    echo -e "${GREEN}Projekt erfolgreich auf GitHub hochgeladen!${NC}"
    echo -e "${YELLOW}Branch:${NC} $BRANCH_NAME"
    echo -e "${YELLOW}Repository:${NC} $REPO_URL"
    echo -e "${YELLOW}GitHub-URL:${NC} $REPO_URL/tree/$BRANCH_NAME"
else
    echo -e "${RED}Fehler beim Hochladen auf GitHub.${NC}"
    echo -e "${RED}Bitte überprüfe:${NC}"
    echo -e "  - Repository-URL: $REPO_URL"
    echo -e "  - GitHub-Zugangsdaten"
    echo -e "  - Ob das Repository auf GitHub existiert"
    exit 1
fi
