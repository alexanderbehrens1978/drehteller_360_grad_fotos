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

# GitHub-Repository-URL (bitte anpassen)
REPO_URL="https://github.com/DEIN_GITHUB_USERNAME/360-drehteller.git"

# Vor dem Commit ausschließen
EXCLUDE_FILES=(
    "myenv/"
    ".git/"
    "static/photos/*"
    "static/sample_images/*"
    "projects/"
    "*.log"
    "__pycache__/"
    ".env"
)

# Zum Projektverzeichnis wechseln
cd "$PROJECT_DIR"

# Git-Konfiguration
git config --global user.name "Alexander Behrens"
git config --global user.email "axellander@web.de"

# Initialisiere Repository, falls nicht vorhanden
if [ ! -d ".git" ]; then
    git init
fi

# .gitignore erstellen/aktualisieren
echo "Erstelle/aktualisiere .gitignore"
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

# Commit-Nachricht
COMMIT_MESSAGE="Update vom $(date '+%d.%m.%Y %H:%M') - Web-Version"

# Commit erstellen
echo -e "${GREEN}Erstelle Commit: ${COMMIT_MESSAGE}${NC}"
git commit -m "$COMMIT_MESSAGE"

# Neuen Branch erstellen und wechseln
echo -e "${GREEN}Erstelle neuen Branch: ${BRANCH_NAME}${NC}"
git checkout -b "$BRANCH_NAME"

# Remote hinzufügen (falls nicht vorhanden)
git remote add origin "$REPO_URL" 2>/dev/null

# Push zum GitHub-Repository
echo -e "${YELLOW}Pushe zum GitHub-Repository...${NC}"
git push -u origin "$BRANCH_NAME"

echo -e "${GREEN}Projekt erfolgreich auf GitHub hochgeladen!${NC}"
echo -e "${YELLOW}Branch:${NC} $BRANCH_NAME"
echo -e "${YELLOW}Repository:${NC} $REPO_URL"
