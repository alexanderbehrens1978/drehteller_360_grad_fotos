#!/bin/bash
# setup_and_autostart.sh

# Farbcodes für Terminal-Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  360° Drehteller - Komplette Systemeinrichtung  ${NC}"
echo -e "${BLUE}==================================================${NC}"

# Überprüfen, ob das Skript mit sudo ausgeführt wird
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Bitte führen Sie das Skript mit sudo aus:${NC}"
  echo -e "${YELLOW}sudo bash setup_and_autostart.sh${NC}"
  exit 1
fi

# Verzeichnis des Projekts bestimmen
PROJECT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo -e "${YELLOW}Projektverzeichnis: ${PROJECT_DIR}${NC}"

# Benutzernamen ermitteln (vom sudo-Aufruf)
REAL_USER=${SUDO_USER:-$USER}
REAL_USER_HOME=$(eval echo ~$REAL_USER)
echo -e "${YELLOW}Nutzerverzeichnis: ${REAL_USER_HOME}${NC}"

# 1. System-Abhängigkeiten installieren
echo -e "\n${GREEN}1. Installiere System-Abhängigkeiten...${NC}"
apt-get update
apt-get install -y \
    python3-venv \
    python3-dev \
    python3-pip \
    python3-opencv \
    fswebcam \
    v4l-utils \
    libatlas-base-dev \
    git \
    curl \
    nginx \
    gphoto2

# Installiere Arduino CLI
if ! command -v arduino-cli &> /dev/null; then
    echo -e "${YELLOW}Installiere Arduino CLI...${NC}"
    curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | BINDIR=/usr/local/bin sh
    arduino-cli core update-index
    arduino-cli core install arduino:avr
fi

# 2. Python virtuelle Umgebung einrichten
echo -e "\n${GREEN}2. Richte virtuelle Python-Umgebung ein...${NC}"
cd "$PROJECT_DIR"

# Alte Umgebung vollständig entfernen, falls vorhanden
if [ -d "myenv" ]; then
    echo -e "${YELLOW}Entferne alte virtuelle Umgebung...${NC}"
    rm -rf myenv
fi

# Virtuelle Umgebung erstellen
echo -e "${YELLOW}Erstelle neue virtuelle Umgebung...${NC}"
python3 -m venv myenv

# Wichtig: Sofort richtige Eigentümerrechte für den tatsächlichen Benutzer setzen
chown -R $REAL_USER:$REAL_USER "$PROJECT_DIR/myenv"
chmod -R u+rwX "$PROJECT_DIR/myenv"

# Abhängigkeiten innerhalb der virtuellen Umgebung installieren
echo -e "${YELLOW}Installiere Python-Abhängigkeiten...${NC}"
# Verwende eine Kombination, die den Kontext beibehält aber als richtiger Benutzer ausführt
su - $REAL_USER -c "cd $PROJECT_DIR && source myenv/bin/activate && pip install --upgrade pip wheel setuptools"

# Python-Version feststellen
PYTHON_VERSION=$(su - $REAL_USER -c "cd $PROJECT_DIR && source myenv/bin/activate && python -c 'import sys; print(f\"{sys.version_info.major}.{sys.version_info.minor}\")'")
echo -e "${YELLOW}Python-Version: ${PYTHON_VERSION}${NC}"

# Erstelle oder aktualisiere requirements.txt basierend auf der Python-Version
if [[ "$PYTHON_VERSION" == "3.12" ]]; then
    echo -e "${YELLOW}Python 3.12 erkannt. Erstelle kompatible requirements.txt...${NC}"
    cat > "$PROJECT_DIR/requirements.txt" << EOL
# Datei: requirements.txt
# Python-Abhängigkeiten für das 360° Drehteller Fotografie-System
# Angepasst für Python 3.12

# Webframework
Flask>=3.0.3
Werkzeug>=3.0.6
Jinja2==3.1.6

# Serielle Kommunikation
pyserial==3.5

# Bildverarbeitung für Python 3.12
numpy==2.0.0
opencv-python==4.11.0.86
# Wähle eine der folgenden OpenCV-Varianten:
# opencv-contrib-python==4.11.0.86  # Mit zusätzlichen Funktionen
# opencv-python-headless==4.11.0.86  # Für Server ohne GUI

# Aktualisiert für bessere Kompatibilität
Pillow>=10.3.0

# Kamerasteuerung
gphoto2==2.3.4

# Utilities
python-dotenv==1.0.0
EOL
else
    echo -e "${YELLOW}Python ${PYTHON_VERSION} erkannt. Erstelle kompatible requirements.txt...${NC}"
    cat > "$PROJECT_DIR/requirements.txt" << EOL
# Datei: requirements.txt
# Python-Abhängigkeiten für das 360° Drehteller Fotografie-System
# Angepasst für Python ${PYTHON_VERSION}

# Webframework
Flask>=3.0.3
Werkzeug>=3.0.6
Jinja2==3.1.6

# Serielle Kommunikation
pyserial==3.5

# Bildverarbeitung
numpy==1.24.3
opencv-python-headless==4.7.0.72

# Bildbearbeitung
Pillow>=10.3.0

# Kamerasteuerung
gphoto2==2.3.4

# Utilities
python-dotenv==1.0.0
EOL
fi

# Setze Berechtigungen für requirements.txt
chown $REAL_USER:$REAL_USER "$PROJECT_DIR/requirements.txt"

# Installiere die Python-Abhängigkeiten als richtiger Benutzer
echo -e "${YELLOW}Installiere Abhängigkeiten aus requirements.txt...${NC}"
su - $REAL_USER -c "cd $PROJECT_DIR && source myenv/bin/activate && pip install -r requirements.txt"

# Installiere fehlende OpenCV-Variante für Python 3.12
if [[ "$PYTHON_VERSION" == "3.12" ]]; then
    echo -e "${YELLOW}Installiere zusätzliche OpenCV-Varianten für Python 3.12...${NC}"
    su - $REAL_USER -c "cd $PROJECT_DIR && source myenv/bin/activate && pip install opencv-contrib-python==4.11.0.86"
fi

# Nochmals überprüfen, ob alle Berechtigungen richtig gesetzt sind
chown -R $REAL_USER:$REAL_USER "$PROJECT_DIR/myenv"
chmod -R u+rwX "$PROJECT_DIR/myenv"

# 3. Verzeichnisstruktur erstellen
echo -e "\n${GREEN}3. Erstelle Verzeichnisstruktur...${NC}"
mkdir -p "$PROJECT_DIR/static/photos"
mkdir -p "$PROJECT_DIR/static/sample_images"
mkdir -p "$PROJECT_DIR/projects"

# Berechtigungen setzen
chown -R $REAL_USER:$REAL_USER "$PROJECT_DIR/static"
chown -R $REAL_USER:$REAL_USER "$PROJECT_DIR/projects"

# Berechtigungen für serielle Ports und Video-Geräte
echo -e "${YELLOW}Füge Benutzer zu notwendigen Gruppen hinzu...${NC}"
usermod -a -G dialout $REAL_USER
usermod -a -G video $REAL_USER

# 4. Platzhalter-Bild erstellen, falls nicht vorhanden
echo -e "\n${GREEN}4. Erzeuge Platzhalter-Bild...${NC}"
if [ ! -f "$PROJECT_DIR/static/placeholder.jpg" ]; then
    # Führe diesen Code als normaler Benutzer aus, nicht als root
    su - $REAL_USER -c "cd $PROJECT_DIR && source myenv/bin/activate && python - << 'EOL'
from PIL import Image, ImageDraw, ImageFont
import os

def generate_placeholder(output_path='static/placeholder.jpg', width=640, height=480):
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

    text = \"Kein Bild verfügbar\"
    text_width = 200  # Ungefähre Textbreite
    text_position = ((width - text_width) // 2, height // 2 - 15)
    draw.text(text_position, text, fill=(100, 100, 100), font=font)

    # Speichere das Bild
    image.save(output_path)
    print(f\"Platzhalter-Bild erstellt: {output_path}\")

generate_placeholder()
EOL"
    # Berechtigungen setzen
    chown $REAL_USER:$REAL_USER "$PROJECT_DIR/static/placeholder.jpg"
fi

# 5. Systemd-Service für Autostart einrichten
echo -e "\n${GREEN}5. Richte Autostart-Service ein...${NC}"

# Service-Datei erstellen
cat > /etc/systemd/system/drehteller360.service << EOL
[Unit]
Description=360 Drehteller Fotografie System
After=network.target

[Service]
User=${REAL_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/myenv/bin/python ${PROJECT_DIR}/web.py
Restart=always
Environment="PATH=${PROJECT_DIR}/myenv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=${PROJECT_DIR}"

[Install]
WantedBy=multi-user.target
EOL

# Systemd neu laden und Service aktivieren
systemctl daemon-reload
systemctl enable drehteller360.service
systemctl start drehteller360.service

echo -e "${GREEN}Service gestartet und für Autostart eingerichtet.${NC}"

# 6. Nginx als Reverse Proxy einrichten (optional)
echo -e "\n${GREEN}6. Nginx als Reverse Proxy einrichten?${NC}"
read -p "Möchten Sie Nginx als Reverse Proxy einrichten? (j/n): " setup_nginx

if [[ $setup_nginx == "j" || $setup_nginx == "J" ]]; then
    # Nginx-Konfiguration erstellen
    cat > /etc/nginx/sites-available/drehteller360 << EOL
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias ${PROJECT_DIR}/static;
    }
}
EOL

    # Aktiviere die Konfiguration
    ln -sf /etc/nginx/sites-available/drehteller360 /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # Testen und neustarten
    nginx -t && systemctl restart nginx

    echo -e "${GREEN}Nginx als Reverse Proxy eingerichtet. Das System ist nun über Port 80 erreichbar.${NC}"
else
    echo -e "${YELLOW}Nginx-Setup übersprungen. Das System ist direkt über Port 5000 erreichbar.${NC}"
fi

# 7. Erstelle ein praktisches Start/Stop-Skript
echo -e "\n${GREEN}7. Erstelle Hilfsskript für Start/Stop/Status...${NC}"

cat > "${PROJECT_DIR}/drehteller.sh" << EOL
#!/bin/bash
# drehteller.sh - Hilfsskript zum Verwalten des 360° Drehteller-Systems

# Farbcodes für Terminal-Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Prüfe auf root-Rechte für bestimmte Befehle
check_root() {
    if [ "\$EUID" -ne 0 ]; then
        echo -e "\${RED}Dieser Befehl benötigt Administratorrechte.\${NC}"
        echo -e "\${YELLOW}Bitte mit sudo ausführen: sudo \$0 \$1\${NC}"
        exit 1
    fi
}

case "\$1" in
    start)
        check_root
        systemctl start drehteller360.service
        echo -e "\${GREEN}360° Drehteller-System gestartet.\${NC}"
        ;;
    stop)
        check_root
        systemctl stop drehteller360.service
        echo -e "\${GREEN}360° Drehteller-System gestoppt.\${NC}"
        ;;
    restart)
        check_root
        systemctl restart drehteller360.service
        echo -e "\${GREEN}360° Drehteller-System neugestartet.\${NC}"
        ;;
    status)
        systemctl status drehteller360.service
        ;;
    logs)
        journalctl -u drehteller360.service -f
        ;;
    fix-modules)
        echo -e "\${BLUE}Führe NumPy/OpenCV-Fix aus...\${NC}"
        
        # Aktiviere virtuelle Umgebung
        source myenv/bin/activate
        
        # Python-Version ermitteln
        PYTHON_VERSION=\$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        
        if [[ "\$PYTHON_VERSION" == "3.12" ]]; then
            echo -e "\${YELLOW}Python 3.12 erkannt. Installiere kompatible Versionen...\${NC}"
            pip uninstall -y numpy opencv-python opencv-python-headless opencv-contrib-python
            pip install numpy==2.0.0
            pip install opencv-python==4.11.0.86
            pip install opencv-contrib-python==4.11.0.86
        else
            echo -e "\${YELLOW}Python \${PYTHON_VERSION} erkannt. Installiere Standard-Versionen...\${NC}"
            pip uninstall -y numpy opencv-python opencv-python-headless opencv-contrib-python
            pip install numpy==1.24.3
            pip install opencv-python-headless==4.7.0.72
        fi
        
        # Pillow aktualisieren
        pip install pillow>=10.3.0
        
        echo -e "\${GREEN}Module repariert. Starte Dienst neu...\${NC}"
        sudo systemctl restart drehteller360.service
        ;;
    install-headless)
        echo -e "\${BLUE}Installiere headless-Version von OpenCV...\${NC}"
        
        # Aktiviere virtuelle Umgebung
        source myenv/bin/activate
        
        # Python-Version ermitteln
        PYTHON_VERSION=\$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        
        # Warnhinweis
        echo -e "\${YELLOW}Deinstalliere bestehende OpenCV-Versionen...\${NC}"
        pip uninstall -y opencv-python opencv-contrib-python
        
        if [[ "\$PYTHON_VERSION" == "3.12" ]]; then
            echo -e "\${YELLOW}Python 3.12 erkannt. Installiere kompatible headless-Version...\${NC}"
            pip install opencv-python-headless==4.11.0.86
        else
            echo -e "\${YELLOW}Python \${PYTHON_VERSION} erkannt. Installiere Standard headless-Version...\${NC}"
            pip install opencv-python-headless==4.7.0.72
        fi
        
        echo -e "\${GREEN}OpenCV headless-Version installiert. Starte Dienst neu...\${NC}"
        sudo systemctl restart drehteller360.service
        ;;
    diagnose)
        echo -e "\${BLUE}Führe Moduldiagnose aus...\${NC}"
        source myenv/bin/activate
        python diagnose_modules.py
        ;;
    *)
        echo -e "\${BLUE}Verwendung: \$0 {start|stop|restart|status|logs|fix-modules|install-headless|diagnose}\${NC}"
        echo
        echo -e "\${YELLOW}Verfügbare Befehle:\${NC}"
        echo -e "  \${GREEN}start\${NC}             - Startet den Dienst"
        echo -e "  \${GREEN}stop\${NC}              - Stoppt den Dienst"
        echo -e "  \${GREEN}restart\${NC}           - Neustart des Dienstes"
        echo -e "  \${GREEN}status\${NC}            - Zeigt den Status"
        echo -e "  \${GREEN}logs\${NC}              - Zeigt die Logs"
        echo -e "  \${GREEN}fix-modules\${NC}       - Repariert NumPy/OpenCV Module"
        echo -e "  \${GREEN}install-headless\${NC}  - Installiert OpenCV headless-Version"
        echo -e "  \${GREEN}diagnose\${NC}          - Führt Diagnose der Module durch"
        exit 1
        ;;
esac
exit 0
EOL

chmod +x "${PROJECT_DIR}/drehteller.sh"
chown $REAL_USER:$REAL_USER "${PROJECT_DIR}/drehteller.sh"

# 8. Diagnose-Skript erstellen
echo -e "\n${GREEN}8. Erstelle Diagnose-Skript...${NC}"

cat > "${PROJECT_DIR}/diagnose_modules.py" << 'EOL'
#!/usr/bin/env python3
"""
Diagnose-Skript für Module-Probleme im 360° Drehteller-System
"""
import sys
import importlib
import traceback

def test_import(module_name):
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "unbekannt")
        print(f"✅ {module_name} erfolgreich importiert (Version: {version})")
        return True
    except ImportError as e:
        print(f"❌ {module_name} konnte nicht importiert werden.")
        print(f"   Fehler: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"⚠️ {module_name} verursacht einen Fehler:")
        print(f"   Fehler: {e}")
        traceback.print_exc()
        return False

def main():
    print(f"Python Version: {sys.version}")
    
    modules_to_check = [
        "numpy", 
        "cv2", 
        "flask", 
        "werkzeug", 
        "PIL", 
        "gphoto2"
    ]
    
    for module in modules_to_check:
        test_import(module)
        print("-" * 40)
    
    # Überprüfe OpenCV mit NumPy Interaktion
    try:
        import numpy as np
        import cv2
        # Teste eine einfache Operation mit beiden Modulen
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print("✅ OpenCV kann erfolgreich mit NumPy arbeiten")
    except Exception as e:
        print("❌ OpenCV kann nicht mit NumPy arbeiten")
        print(f"   Fehler: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
EOL

chmod +x "${PROJECT_DIR}/diagnose_modules.py"
chown $REAL_USER:$REAL_USER "${PROJECT_DIR}/diagnose_modules.py"

# 9. Abschließend nochmal alle Berechtigungen überprüfen
echo -e "\n${GREEN}9. Überprüfe abschließend alle Berechtigungen...${NC}"
find "$PROJECT_DIR/myenv" -type d -exec chmod 755 {} \;
find "$PROJECT_DIR/myenv" -type f -exec chmod 644 {} \;
find "$PROJECT_DIR/myenv/bin" -type f -exec chmod 755 {} \;
chown -R $REAL_USER:$REAL_USER "$PROJECT_DIR/myenv"

# 10. Abschluss
HOST_IP=$(hostname -I | cut -d' ' -f1)
echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}  360° Drehteller-System erfolgreich eingerichtet!  ${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "${YELLOW}Das System wurde gestartet und läuft automatisch beim Systemstart.${NC}"
echo -e "\n${BLUE}Zugriff auf das System:${NC}"
if [[ $setup_nginx == "j" || $setup_nginx == "J" ]]; then
    echo -e "  URL: ${GREEN}http://${HOST_IP}/${NC}"
else
    echo -e "  URL: ${GREEN}http://${HOST_IP}:5000/${NC}"
fi

echo -e "\n${BLUE}Verwaltung des Systems:${NC}"
echo -e "  ${YELLOW}./drehteller.sh start${NC}             - Startet den Dienst"
echo -e "  ${YELLOW}./drehteller.sh stop${NC}              - Stoppt den Dienst"
echo -e "  ${YELLOW}./drehteller.sh restart${NC}           - Neustart des Dienstes"
echo -e "  ${YELLOW}./drehteller.sh status${NC}            - Zeigt den Status"
echo -e "  ${YELLOW}./drehteller.sh logs${NC}              - Zeigt die Logs"
echo -e "  ${YELLOW}./drehteller.sh fix-modules${NC}       - Repariert NumPy/OpenCV Module"
echo -e "  ${YELLOW}./drehteller.sh install-headless${NC}  - Installiert OpenCV headless-Version"
echo -e "  ${YELLOW}./drehteller.sh diagnose${NC}          - Diagnostiziert Modul-Probleme"

echo -e "\n${GREEN}Viel Erfolg mit deinem 360° Drehteller-System!${NC}"
