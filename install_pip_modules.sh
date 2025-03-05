#!/bin/bash
# Installationsskript für 360° Drehteller Projekt

# Farbcodes für Terminal-Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}360° Drehteller - Systemweite Abhängigkeiten Installation${NC}"
echo "=============================================="

# Überprüfen, ob das Skript mit sudo ausgeführt wird
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Bitte führen Sie das Skript mit sudo aus:${NC}"
    echo -e "${YELLOW}sudo bash install_pip_modules.sh${NC}"
    exit 1
fi

# Python-Version prüfen
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}Erkannte Python-Version: ${PYTHON_VERSION}${NC}"

if [[ "$PYTHON_VERSION" != "3.12"* ]]; then
    echo -e "${YELLOW}WARNUNG: Empfohlene Python-Version ist 3.12${NC}"
fi

# Systemabhängigkeiten installieren
echo -e "\n${GREEN}Installiere Systemabhängigkeiten...${NC}"
apt-get update
apt-get install -y \
    python3-dev \
    python3-venv \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libv4l-dev \
    v4l-utils \
    fswebcam \
    gphoto2 \
    git \
    curl \
    libatlas-base-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libxvidcore-dev \
    libx264-dev \
    gfortran \
    openexr \
    libopenexr-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev

# Benutzerrechte für serielle Ports und Video-Geräte
echo -e "\n${GREEN}Konfiguriere Benutzerrechte...${NC}"
# Aktuellen Benutzer zu relevanten Gruppen hinzufügen
usermod -a -G dialout $SUDO_USER
usermod -a -G video $SUDO_USER

# Virtuelle Umgebung einrichten
echo -e "\n${GREEN}Richte virtuelle Python-Umgebung ein...${NC}"
cd "$( dirname "${BASH_SOURCE[0]}" )"

# Virtuelle Umgebung erstellen, falls nicht vorhanden
if [ ! -d "myenv" ]; then
    python3 -m venv myenv
fi

# Virtuelle Umgebung aktivieren
source myenv/bin/activate

# pip aktualisieren
pip install --upgrade pip setuptools wheel

# Abhängigkeiten installieren
pip install -r requirements.txt

# Verzeichnisstruktur erstellen
echo -e "\n${GREEN}Erstelle Verzeichnisstruktur...${NC}"
mkdir -p static/photos
mkdir -p static/sample_images
mkdir -p static/projects
mkdir -p projects

# Platzhalter-Bild erstellen
echo -e "\n${GREEN}Generiere Platzhalter-Bild...${NC}"
python3 - << 'EOL'
from PIL import Image, ImageDraw, ImageFont
import os

def generate_placeholder(output_path='static/placeholder.jpg', width=640, height=480):
    """
    Generiert ein Platzhalter-Bild mit Text
    """
    # Stelle sicher, dass der Zielordner existiert
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Erstelle ein neues Bild mit grauem Hintergrund
    image = Image.new('RGB', (width, height), color=(240, 240, 240))
    draw = ImageDraw.Draw(image)

    # Zeichne Rahmen
    draw.rectangle((0, 0, width-1, height-1), outline=(200, 200, 200), width=2)

    # Füge Text hinzu
    try:
        # Versuche, einen Standardschriftsatz zu laden
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except IOError:
        # Fallback auf Standardschriftart
        font = ImageFont.load_default()

    text = "Kein Bild verfügbar"
    text_width = 200  # Ungefähre Textbreite
    text_position = ((width - text_width) // 2, height // 2 - 15)
    draw.text(text_position, text, fill=(100, 100, 100), font=font)

    # Speichere das Bild
    image.save(output_path)
    print(f"Platzhalter-Bild erstellt: {output_path}")

generate_placeholder()
EOL

# Berechtigungen korrigieren
chown -R $SUDO_USER:$SUDO_USER myenv
chown -R $SUDO_USER:$SUDO_USER static

echo -e "\n${GREEN}Installation abgeschlossen!${NC}"
echo -e "${YELLOW}Aktivieren Sie die virtuelle Umgebung mit:${NC} source myenv/bin/activate"
echo -e "${YELLOW}Starten Sie die Anwendung mit:${NC} python web.py"
