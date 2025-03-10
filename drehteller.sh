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
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Dieser Befehl benötigt Administratorrechte.${NC}"
        echo -e "${YELLOW}Bitte mit sudo ausführen: sudo $0 $1${NC}"
        exit 1
    fi
}

case "$1" in
    start)
        check_root
        systemctl start drehteller360.service
        echo -e "${GREEN}360° Drehteller-System gestartet.${NC}"
        ;;
    stop)
        check_root
        systemctl stop drehteller360.service
        echo -e "${GREEN}360° Drehteller-System gestoppt.${NC}"
        ;;
    restart)
        check_root
        systemctl restart drehteller360.service
        echo -e "${GREEN}360° Drehteller-System neugestartet.${NC}"
        ;;
    status)
        systemctl status drehteller360.service
        ;;
    logs)
        journalctl -u drehteller360.service -f
        ;;
    fix-modules)
        echo -e "${BLUE}Führe NumPy/OpenCV-Fix aus...${NC}"
        
        # Aktiviere virtuelle Umgebung
        source myenv/bin/activate
        
        # Python-Version ermitteln
        PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        
        if [[ "$PYTHON_VERSION" == "3.12" ]]; then
            echo -e "${YELLOW}Python 3.12 erkannt. Installiere kompatible Versionen...${NC}"
            pip uninstall -y numpy opencv-python opencv-python-headless opencv-contrib-python
            pip install numpy==2.0.0
            pip install opencv-python==4.11.0.86
            pip install opencv-contrib-python==4.11.0.86
        else
            echo -e "${YELLOW}Python ${PYTHON_VERSION} erkannt. Installiere Standard-Versionen...${NC}"
            pip uninstall -y numpy opencv-python opencv-python-headless opencv-contrib-python
            pip install numpy==1.24.3
            pip install opencv-python-headless==4.7.0.72
        fi
        
        # Pillow aktualisieren
        pip install pillow==10.1.0
        
        echo -e "${GREEN}Module repariert. Starte Dienst neu...${NC}"
        sudo systemctl restart drehteller360.service
        ;;
    install-headless)
        echo -e "${BLUE}Installiere headless-Version von OpenCV...${NC}"
        
        # Aktiviere virtuelle Umgebung
        source myenv/bin/activate
        
        # Python-Version ermitteln
        PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        
        # Warnhinweis
        echo -e "${YELLOW}Deinstalliere bestehende OpenCV-Versionen...${NC}"
        pip uninstall -y opencv-python opencv-contrib-python
        
        if [[ "$PYTHON_VERSION" == "3.12" ]]; then
            echo -e "${YELLOW}Python 3.12 erkannt. Installiere kompatible headless-Version...${NC}"
            pip install opencv-python-headless==4.11.0.86
        else
            echo -e "${YELLOW}Python ${PYTHON_VERSION} erkannt. Installiere Standard headless-Version...${NC}"
            pip install opencv-python-headless==4.7.0.72
        fi
        
        echo -e "${GREEN}OpenCV headless-Version installiert. Starte Dienst neu...${NC}"
        sudo systemctl restart drehteller360.service
        ;;
    diagnose)
        echo -e "${BLUE}Führe Moduldiagnose aus...${NC}"
        source myenv/bin/activate
        python diagnose_modules.py
        ;;
    *)
        echo -e "${BLUE}Verwendung: $0 {start|stop|restart|status|logs|fix-modules|install-headless|diagnose}${NC}"
        echo
        echo -e "${YELLOW}Verfügbare Befehle:${NC}"
        echo -e "  ${GREEN}start${NC}             - Startet den Dienst"
        echo -e "  ${GREEN}stop${NC}              - Stoppt den Dienst"
        echo -e "  ${GREEN}restart${NC}           - Neustart des Dienstes"
        echo -e "  ${GREEN}status${NC}            - Zeigt den Status"
        echo -e "  ${GREEN}logs${NC}              - Zeigt die Logs"
        echo -e "  ${GREEN}fix-modules${NC}       - Repariert NumPy/OpenCV Module"
        echo -e "  ${GREEN}install-headless${NC}  - Installiert OpenCV headless-Version"
        echo -e "  ${GREEN}diagnose${NC}          - Führt Diagnose der Module durch"
        exit 1
        ;;
esac
exit 0
