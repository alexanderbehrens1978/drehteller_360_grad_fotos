#!/bin/bash
# Upload-Skript für das Hall-Sensor Arduino-Sketch
# Dieses Skript lädt das hall_sensor_arduino.ino auf den Arduino hoch, der am USB-Port angeschlossen ist
# Unterstützt CH340/CH341-basierte Boards mit VID 0843:5740

# Farben für die Ausgabe
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Standardwerte
SKETCH_DIR="$(dirname "$(readlink -f "$0")")/hall_sensor_arduino"
ARDUINO_PORT="/dev/ttyUSB0"
ARDUINO_FQBN="arduino:avr:uno"  # Fully Qualified Board Name für Arduino UNO
VENDOR_ID="0843"
PRODUCT_ID="5740"
AUTO_INSTALL=false

# Hilfefunktion
show_help() {
    echo -e "${BLUE}Upload-Skript für Hall-Sensor Arduino-Sketch${NC}"
    echo ""
    echo "Verwendung: $0 [optionen]"
    echo ""
    echo "Optionen:"
    echo "  -p, --port PORT       Serieller Port des Arduino (Standard: ${ARDUINO_PORT})"
    echo "  -b, --board FQBN      FQBN des Arduino-Boards (Standard: ${ARDUINO_FQBN})"
    echo "  -s, --sketch DIR      Verzeichnis der Arduino-Skizze (Standard: ${SKETCH_DIR})"
    echo "  -l, --list-ports      Verfügbare serielle Ports anzeigen"
    echo "  -i, --install         Automatisch benötigte Treiber installieren"
    echo "  -h, --help            Diese Hilfe anzeigen"
    echo ""
    echo "Beispiel:"
    echo "  $0 --port /dev/ttyACM0"
    echo "  $0 --install          # Automatische Treiberinstallation"
    echo ""
}

# Verfügbare Ports anzeigen
list_ports() {
    echo -e "${YELLOW}Verfügbare serielle Ports:${NC}"
    
    # Überprüfen, ob arduino-cli verfügbar ist
    if command -v arduino-cli &> /dev/null; then
        arduino-cli board list
    # Wenn nicht, versuchen wir es mit lsusb und ls /dev/tty*
    else
        echo -e "${YELLOW}Arduino CLI nicht gefunden. Zeige verfügbare USB-Geräte:${NC}"
        lsusb | grep -i "arduino\|ch340\|ftdi\|cp210x" || echo "Keine bekannten Arduino-Geräte gefunden."
        echo -e "\n${YELLOW}Verfügbare serielle Ports:${NC}"
        ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || echo "Keine seriellen Ports gefunden."
    fi
    
    echo ""
}

# Prüft, ob das Board mit VID:PID 0843:5740 angeschlossen ist
check_board_connected() {
    echo -e "${YELLOW}Suche nach Arduino-Board mit VID:PID ${VENDOR_ID}:${PRODUCT_ID}...${NC}"
    
    if lsusb | grep -q "${VENDOR_ID}:${PRODUCT_ID}"; then
        echo -e "${GREEN}Board gefunden: VID:PID ${VENDOR_ID}:${PRODUCT_ID}${NC}"
        return 0
    else
        echo -e "${YELLOW}Board mit VID:PID ${VENDOR_ID}:${PRODUCT_ID} nicht gefunden.${NC}"
        echo -e "Angeschlossene USB-Geräte:"
        lsusb
        return 1
    fi
}

# Installiert die notwendigen Treiber
install_drivers() {
    echo -e "${BLUE}=== Treiberinstallation für CH340/CH341 ====${NC}"
    
    # Prüfen, ob sudo verfügbar ist
    if ! command -v sudo &> /dev/null; then
        echo -e "${RED}Fehler: sudo ist nicht verfügbar. Bitte führen Sie dieses Skript mit Root-Rechten aus.${NC}"
        return 1
    fi
    
    # Prüfen, ob apt verfügbar ist
    if ! command -v apt-get &> /dev/null; then
        echo -e "${RED}Fehler: apt-get ist nicht verfügbar. Bitte installieren Sie die Treiber manuell.${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}1. Installiere Treiberpakete...${NC}"
    
    if sudo apt-get update; then
        # Versuche brltty-x11 zu installieren
        if sudo apt-get install -y brltty-x11; then
            echo -e "${GREEN}✓ brltty-x11 erfolgreich installiert${NC}"
        else
            echo -e "${YELLOW}Warnung: brltty-x11 konnte nicht installiert werden. Versuche libusb...${NC}"
            # Versuche libusb zu installieren
            if sudo apt-get install -y libusb-1.0-0-dev; then
                echo -e "${GREEN}✓ libusb-1.0-0-dev erfolgreich installiert${NC}"
            else
                echo -e "${RED}Fehler: Konnte weder brltty-x11 noch libusb-1.0-0-dev installieren.${NC}"
                return 1
            fi
        fi
    else
        echo -e "${RED}Fehler: apt-get update fehlgeschlagen.${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}2. Füge Benutzer zu dialout und tty Gruppen hinzu...${NC}"
    sudo usermod -a -G dialout $USER
    sudo usermod -a -G tty $USER
    echo -e "${GREEN}✓ Benutzer zu Gruppen hinzugefügt${NC}"
    echo -e "${YELLOW}Hinweis: Sie müssen sich ab- und wieder anmelden, damit die Gruppenänderungen wirksam werden.${NC}"
    
    echo -e "${YELLOW}3. Erstelle udev-Regel für das Board...${NC}"
    local rules_file="/etc/udev/rules.d/99-arduino.rules"
    local rule="SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"${VENDOR_ID}\", ATTRS{idProduct}==\"${PRODUCT_ID}\", MODE=\"0666\", GROUP=\"dialout\""
    
    if echo "$rule" | sudo tee "$rules_file" > /dev/null; then
        echo -e "${GREEN}✓ udev-Regel erstellt: $rules_file${NC}"
    else
        echo -e "${RED}Fehler: Konnte udev-Regel nicht erstellen.${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}4. Lade udev-Regeln neu...${NC}"
    if sudo udevadm control --reload-rules && sudo udevadm trigger; then
        echo -e "${GREEN}✓ udev-Regeln erfolgreich neu geladen${NC}"
    else
        echo -e "${RED}Fehler: Konnte udev-Regeln nicht neu laden.${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Treiberinstallation abgeschlossen!${NC}"
    echo -e "${YELLOW}Hinweis: Falls das Board immer noch nicht erkannt wird, trennen Sie es und schließen Sie es erneut an.${NC}"
    return 0
}

# Parameter verarbeiten
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            ARDUINO_PORT="$2"
            shift 2
            ;;
        -b|--board)
            ARDUINO_FQBN="$2"
            shift 2
            ;;
        -s|--sketch)
            SKETCH_DIR="$2"
            shift 2
            ;;
        -l|--list-ports)
            list_ports
            exit 0
            ;;
        -i|--install)
            AUTO_INSTALL=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unbekannte Option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Hauptprogramm
echo -e "${BLUE}=== Hall-Sensor Arduino-Sketch Upload ===${NC}"

# Board-Erkennung
check_board_connected
BOARD_FOUND=$?

# Wenn Board nicht gefunden und Auto-Install aktiviert
if [ $BOARD_FOUND -ne 0 ] && [ "$AUTO_INSTALL" = true ]; then
    echo -e "${YELLOW}Board nicht gefunden. Starte Treiberinstallation...${NC}"
    install_drivers
    
    # Nach Installation erneut prüfen
    echo -e "${YELLOW}Prüfe erneut auf angeschlossenes Board...${NC}"
    check_board_connected
    BOARD_FOUND=$?
fi

# Wenn Board gefunden oder Auto-Install nicht aktiviert
if [ "$AUTO_INSTALL" = true ] && [ $BOARD_FOUND -ne 0 ]; then
    echo -e "${RED}Board konnte auch nach Treiberinstallation nicht gefunden werden.${NC}"
    echo -e "${YELLOW}Bitte stellen Sie sicher, dass das Board angeschlossen ist und versuchen Sie es erneut.${NC}"
    exit 1
fi

# Prüfen, ob das Sketch-Verzeichnis existiert
if [ ! -d "$SKETCH_DIR" ]; then
    echo -e "${RED}Fehler: Sketch-Verzeichnis '$SKETCH_DIR' nicht gefunden.${NC}"
    exit 1
fi

# Prüfen, ob die INO-Datei existiert
INO_FILE="${SKETCH_DIR}/$(basename "${SKETCH_DIR}").ino"
if [ ! -f "$INO_FILE" ]; then
    echo -e "${RED}Fehler: INO-Datei '$INO_FILE' nicht gefunden.${NC}"
    exit 1
fi

echo -e "${YELLOW}Sketch-Verzeichnis: ${NC}${SKETCH_DIR}"
echo -e "${YELLOW}Arduino Port:       ${NC}${ARDUINO_PORT}"
echo -e "${YELLOW}Arduino Board:      ${NC}${ARDUINO_FQBN}"
echo ""

# Prüfen, ob der Arduino angeschlossen ist
if [ ! -e "$ARDUINO_PORT" ]; then
    echo -e "${RED}Fehler: Arduino-Port '$ARDUINO_PORT' nicht gefunden.${NC}"
    echo -e "${YELLOW}Verfügbare Ports:${NC}"
    list_ports
    
    if [ "$AUTO_INSTALL" = false ]; then
        echo -e "${YELLOW}Möchten Sie die Treiberinstallation starten? (j/n)${NC}"
        read -r response
        if [[ "$response" =~ ^[jJyY]$ ]]; then
            install_drivers
            echo -e "${YELLOW}Bitte trennen Sie das Board und schließen Sie es erneut an.${NC}"
            echo -e "${YELLOW}Starten Sie dann das Skript erneut.${NC}"
        fi
    fi
    exit 1
fi

# Prüfen, ob arduino-cli verfügbar ist
if ! command -v arduino-cli &> /dev/null; then
    echo -e "${RED}Fehler: arduino-cli ist nicht installiert oder nicht im PATH.${NC}"
    echo -e "${YELLOW}Bitte installieren Sie die Arduino CLI: https://arduino.github.io/arduino-cli/latest/installation/${NC}"
    exit 1
fi

echo -e "${YELLOW}Kompiliere und lade Sketch hoch...${NC}"

# Sketch kompilieren und hochladen
arduino-cli compile --fqbn "$ARDUINO_FQBN" "$SKETCH_DIR" && 
arduino-cli upload -p "$ARDUINO_PORT" --fqbn "$ARDUINO_FQBN" "$SKETCH_DIR"

# Ergebnis prüfen
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Upload erfolgreich!${NC}"
    echo -e "${GREEN}Der Hall-Sensor-Sketch wurde erfolgreich auf den Arduino hochgeladen.${NC}"
else
    echo -e "${RED}Fehler beim Hochladen des Sketches.${NC}"
    exit 1
fi

echo -e "\n${BLUE}Möchten Sie den seriellen Monitor starten, um die Ausgabe des Hall-Sensors zu sehen? (j/n)${NC}"
read -r response
if [[ "$response" =~ ^[jJyY]$ ]]; then
    echo -e "${YELLOW}Serieller Monitor gestartet. Drücken Sie Ctrl+C zum Beenden.${NC}"
    arduino-cli monitor -p "$ARDUINO_PORT" || 
    echo -e "${RED}Fehler beim Starten des seriellen Monitors. Verwenden Sie stattdessen: 'arduino-cli monitor -p $ARDUINO_PORT'${NC}"
fi

exit 0
