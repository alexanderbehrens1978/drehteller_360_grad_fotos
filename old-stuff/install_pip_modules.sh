#!/bin/bash
# install_pip_modules.sh

# Farbcodes für Terminal-Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Drehteller 360° - Python Abhängigkeiten Installation${NC}"
echo "=============================================="

# Überprüfen, ob das Skript mit sudo ausgeführt wird
if [ "$EUID" -ne 0 ]
  then echo -e "${RED}Bitte führen Sie das Skript mit sudo aus.${NC}"
  echo "Beispiel: sudo bash install_pip_modules.sh"
  exit 1
fi

# Überprüfen, ob Python 3 installiert ist
if ! command -v python3 &> /dev/null
then
    echo -e "${RED}Python 3 ist nicht installiert. Bitte installieren Sie Python 3.${NC}"
    exit 1
fi

# Überprüfen, ob pip3 installiert ist
if ! command -v pip3 &> /dev/null
then
    echo -e "${YELLOW}pip3 ist nicht installiert. Versuche pip3 zu installieren...${NC}"
    apt-get update
    apt-get install -y python3-pip

    if ! command -v pip3 &> /dev/null
    then
        echo -e "${RED}Konnte pip3 nicht installieren. Bitte installieren Sie pip3 manuell.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}pip3 ist installiert. Aktualisiere pip...${NC}"
python3 -m pip install --upgrade pip

# Erstelle eine virtuelle Umgebung, wenn sie nicht existiert
if [ ! -d "myenv" ]; then
    echo -e "${YELLOW}Erstelle virtuelle Python-Umgebung 'myenv'...${NC}"
    python3 -m venv myenv
fi

# Aktiviere die virtuelle Umgebung
echo -e "${YELLOW}Aktiviere virtuelle Umgebung...${NC}"
source myenv/bin/activate

# Aktualisiere pip in der virtuellen Umgebung
echo -e "${YELLOW}Aktualisiere pip in der virtuellen Umgebung...${NC}"
pip install --upgrade pip setuptools wheel

# Installiere die benötigten Module
echo -e "${YELLOW}Installiere Python-Module...${NC}"

pip install flask==2.3.2
pip install werkzeug==2.3.6
pip install opencv-python-headless==4.7.0.72
pip install numpy==1.24.3
pip install pillow==9.5.0
pip install pyserial==3.5
pip install scipy==1.10.1
pip install pandas==2.0.1
pip install requests==2.30.0
pip install imageio==2.31.1

# Installiere zusätzliche Module
echo -e "${YELLOW}Installiere zusätzliche Python-Module...${NC}"
pip install python-dotenv
pip install gunicorn

# Erstelle die benötigten Verzeichnisse
echo -e "${YELLOW}Erstelle Verzeichnisstruktur...${NC}"
mkdir -p static/photos
mkdir -p static/sample_images
mkdir -p projects

# Generiere ein Platzhalter-Bild
echo -e "${YELLOW}Generiere Platzhalter-Bild...${NC}"
cat > generate_placeholder.py << 'EOL'
from PIL import Image, ImageDraw, ImageFont
import os

def generate_placeholder(output_path='static/placeholder.jpg', width=640, height=480):
    """
    Generiert ein Platzhalter-Bild mit Text

    :param output_path: Pfad zum Speichern des Bildes
    :param width: Bildbreite in Pixeln
    :param height: Bildhöhe in Pixeln
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
        font = ImageFont.load_default()
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

    return output_path

if __name__ == "__main__":
    generate_placeholder()
EOL

python generate_placeholder.py

# Benutzerrechte für Video-Geräte
echo -e "${YELLOW}Füge aktuellen Benutzer zur Video-Gruppe hinzu...${NC}"
usermod -a -G video $USER

# Bestätigungsnachricht
echo -e "${GREEN}Installation abgeschlossen!${NC}"
echo "Aktivieren Sie die virtuelle Umgebung mit: source myenv/bin/activate"
echo "Starten Sie die Anwendung mit: python web.py"