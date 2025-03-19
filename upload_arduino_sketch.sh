#!/bin/bash
# upload_arduino_sketch.sh

# Farbcodes für Terminal-Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Arduino Drehteller Sketch Upload Tool${NC}"
echo "======================================"

# Überprüfen, ob Arduino CLI installiert ist
if ! command -v arduino-cli &> /dev/null
then
    echo -e "${YELLOW}Arduino CLI ist nicht installiert. Installiere Arduino CLI...${NC}"

    # Arduino CLI mit dem angegebenen Befehl installieren
    curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh

    # Füge den Pfad zur PATH-Variable hinzu, um arduino-cli direkt nutzen zu können
    export PATH=$PATH:$HOME/bin

    # Überprüfe, ob die Installation erfolgreich war
    if ! command -v arduino-cli &> /dev/null
    then
        echo -e "${RED}Konnte Arduino CLI nicht installieren.${NC}"
        echo "Bitte installieren Sie Arduino CLI manuell: https://arduino.github.io/arduino-cli/latest/installation/"
        exit 1
    fi
fi

# Aktualisiere den Index und installiere die benötigten Arduino-Plattformen
echo -e "${YELLOW}Aktualisiere Core-Index und installiere Arduino-Plattformen...${NC}"
arduino-cli core update-index
arduino-cli core install arduino:avr              # Für klassische Arduino Boards
arduino-cli core install arduino:renesas_uno      # Für Arduino UNO R4 Boards

# Überprüfen, ob der Arduino angeschlossen ist
echo -e "${YELLOW}Suche nach angeschlossenen Arduino-Boards...${NC}"

# Auch manuell nach seriellen Geräten suchen, falls arduino-cli keine Boards erkennt
BOARD_LIST=$(arduino-cli board list)
if [ -z "$BOARD_LIST" ] || [ "$BOARD_LIST" = "Port         Protocol Type Board Name FQBN Core" ]; then
    echo -e "${YELLOW}Arduino CLI konnte keine Boards erkennen. Überprüfe alternative Methoden...${NC}"

    # Prüfe, ob ACM-Geräte vorhanden sind (üblich für Arduino)
    if ls /dev/ttyACM* 1> /dev/null 2>&1; then
        echo -e "${GREEN}ACM-Geräte gefunden:${NC}"
        ls -l /dev/ttyACM*
        PORT=$(ls /dev/ttyACM* | head -1)
        echo -e "${YELLOW}Verwende $PORT als Arduino-Port${NC}"

        # Prüfe UNO R4 über lsusb
        if lsusb | grep -q "Arduino.*UNO.*R4"; then
            echo -e "${GREEN}Arduino UNO R4 erkannt!${NC}"
            FQBN="arduino:renesas_uno:unor4wifi"
        else
            echo -e "${YELLOW}Arduino-Typ nicht eindeutig erkannt, verwende UNO R3 als Standard${NC}"
            FQBN="arduino:avr:uno"
        fi
    elif ls /dev/ttyUSB* 1> /dev/null 2>&1; then
        echo -e "${GREEN}USB-Geräte gefunden:${NC}"
        ls -l /dev/ttyUSB*
        PORT=$(ls /dev/ttyUSB* | head -1)
        echo -e "${YELLOW}Verwende $PORT als Arduino-Port${NC}"
        FQBN="arduino:avr:uno"  # Standardannahme für USB-Geräte
    else
        echo -e "${RED}Kein Arduino-Board gefunden. Bitte schließen Sie ein Arduino-Board an.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}Verfügbare Boards:${NC}"
    echo "$BOARD_LIST"

    # Versuche, eine vernünftige Vorauswahl zu treffen
    DEFAULT_PORT=$(echo "$BOARD_LIST" | grep -v "Port" | head -1 | awk '{print $1}')
    DEFAULT_FQBN=$(echo "$BOARD_LIST" | grep -v "Port" | head -1 | awk '{print $5}')

    if [ -z "$DEFAULT_PORT" ]; then
        if ls /dev/ttyACM* 1> /dev/null 2>&1; then
            DEFAULT_PORT=$(ls /dev/ttyACM* | head -1)
        elif ls /dev/ttyUSB* 1> /dev/null 2>&1; then
            DEFAULT_PORT=$(ls /dev/ttyUSB* | head -1)
        fi
    fi

    if [ -z "$DEFAULT_FQBN" ]; then
        if lsusb | grep -q "Arduino.*UNO.*R4"; then
            DEFAULT_FQBN="arduino:renesas_uno:unor4wifi"
        else
            DEFAULT_FQBN="arduino:avr:uno"
        fi
    fi
fi

# Erstelle Arduino-Sketch-Verzeichnis und Datei
SKETCH_DIR="arduino_drehteller_steuerung"
mkdir -p "$SKETCH_DIR"

cat > "$SKETCH_DIR/$SKETCH_DIR.ino" << 'EOL'
// arduino_drehteller_steuerung.ino

// Definiere den Pin für das Relais
#define RELAIS_PIN 8

void setup() {
  // Initialisiere die serielle Kommunikation mit 9600 Baud
  Serial.begin(9600);

  // Konfiguriere den Relais-Pin als Ausgang
  pinMode(RELAIS_PIN, OUTPUT);

  // Stelle sicher, dass das Relais zu Beginn ausgeschaltet ist
  digitalWrite(RELAIS_PIN, LOW);

  Serial.println("Arduino Drehteller Steuerung bereit");
}

void loop() {
  // Prüfe, ob Daten verfügbar sind
  if (Serial.available() > 0) {
    // Lese eingehende Daten
    char command = Serial.read();

    // Interpretiere Befehl
    if (command == '1') {
      // Relais einschalten
      digitalWrite(RELAIS_PIN, HIGH);
      Serial.println("Relais eingeschaltet - Drehteller läuft");
    }
    else if (command == '0') {
      // Relais ausschalten
      digitalWrite(RELAIS_PIN, LOW);
      Serial.println("Relais ausgeschaltet - Drehteller gestoppt");
    }
    else {
      // Unbekannter Befehl
      Serial.println("Unbekannter Befehl empfangen. Verwende '1' zum Einschalten und '0' zum Ausschalten.");
    }
  }

  // Kurze Pause, um CPU-Last zu reduzieren
  delay(10);
}
EOL

echo -e "${YELLOW}Arduino-Sketch erstellt in $SKETCH_DIR/$SKETCH_DIR.ino${NC}"

# Frage nach dem Board-Port, wenn noch nicht bestimmt
if [ -z "$PORT" ]; then
    echo -e "${YELLOW}Welcher Port soll für den Upload verwendet werden?${NC}"
    echo "Bitte geben Sie den Port ein (z.B. /dev/ttyACM0 oder COM3): "
    read PORT

    if [ -z "$PORT" ]; then
        echo -e "${RED}Kein Port ausgewählt. Upload abgebrochen.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Verwende Port: $PORT${NC}"
    echo "Möchten Sie einen anderen Port verwenden? (j/N): "
    read CHANGE_PORT

    if [[ "$CHANGE_PORT" == "j" || "$CHANGE_PORT" == "J" ]]; then
        echo "Bitte geben Sie den Port ein (z.B. /dev/ttyACM0 oder COM3): "
        read NEW_PORT
        if [ ! -z "$NEW_PORT" ]; then
            PORT=$NEW_PORT
        fi
    fi
fi

# Frage nach dem Board-Typ, wenn noch nicht bestimmt
if [ -z "$FQBN" ]; then
    echo -e "${YELLOW}Welcher Board-Typ wird verwendet?${NC}"
    echo "1) Arduino UNO R3 (Classic) - arduino:avr:uno"
    echo "2) Arduino UNO R4 WiFi - arduino:renesas_uno:unor4wifi"
    echo "3) Arduino UNO R4 Minima - arduino:renesas_uno:unor4minima"
    echo "4) Arduino Nano - arduino:avr:nano"
    echo "5) Arduino Mega - arduino:avr:mega"
    echo "6) Arduino Leonardo - arduino:avr:leonardo"
    echo "Bitte wählen Sie eine Option (1-6): "
    read BOARD_CHOICE

    case $BOARD_CHOICE in
        1)
            FQBN="arduino:avr:uno"
            ;;
        2)
            FQBN="arduino:renesas_uno:unor4wifi"
            ;;
        3)
            FQBN="arduino:renesas_uno:unor4minima"
            ;;
        4)
            FQBN="arduino:avr:nano"
            ;;
        5)
            FQBN="arduino:avr:mega"
            ;;
        6)
            FQBN="arduino:avr:leonardo"
            ;;
        *)
            FQBN="arduino:avr:uno"
            echo -e "${YELLOW}Keine gültige Auswahl. Verwende Arduino Uno R3 als Standard.${NC}"
            ;;
    esac
else
    echo -e "${YELLOW}Verwende Board-Typ: $FQBN${NC}"
    echo "Möchten Sie einen anderen Board-Typ verwenden? (j/N): "
    read CHANGE_BOARD

    if [[ "$CHANGE_BOARD" == "j" || "$CHANGE_BOARD" == "J" ]]; then
        echo "1) Arduino UNO R3 (Classic) - arduino:avr:uno"
        echo "2) Arduino UNO R4 WiFi - arduino:renesas_uno:unor4wifi"
        echo "3) Arduino UNO R4 Minima - arduino:renesas_uno:unor4minima"
        echo "4) Arduino Nano - arduino:avr:nano"
        echo "5) Arduino Mega - arduino:avr:mega"
        echo "6) Arduino Leonardo - arduino:avr:leonardo"
        echo "Bitte wählen Sie eine Option (1-6): "
        read BOARD_CHOICE

        case $BOARD_CHOICE in
            1)
                FQBN="arduino:avr:uno"
                ;;
            2)
                FQBN="arduino:renesas_uno:unor4wifi"
                ;;
            3)
                FQBN="arduino:renesas_uno:unor4minima"
                ;;
            4)
                FQBN="arduino:avr:nano"
                ;;
            5)
                FQBN="arduino:avr:mega"
                ;;
            6)
                FQBN="arduino:avr:leonardo"
                ;;
        esac
    fi
fi

# Kompiliere den Sketch
echo -e "${YELLOW}Kompiliere Arduino-Sketch...${NC}"
arduino-cli compile --fqbn $FQBN "$SKETCH_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}Kompilierung fehlgeschlagen. Bitte überprüfen Sie den Sketch und die Board-Auswahl.${NC}"
    exit 1
fi

# Upload des Sketches auf den Arduino
echo -e "${YELLOW}Lade Sketch auf den Arduino hoch...${NC}"
echo -e "${YELLOW}Verwende Befehl: arduino-cli upload -p $PORT --fqbn $FQBN \"$SKETCH_DIR\"${NC}"

# Füge Berechtigungen hinzu, falls notwendig
if [ ! -w "$PORT" ]; then
    echo -e "${YELLOW}Portberechtigungen anpassen...${NC}"
    sudo chmod a+rw $PORT
fi

# Upload durchführen
arduino-cli upload -p $PORT --fqbn $FQBN "$SKETCH_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}Upload fehlgeschlagen. Bitte überprüfen Sie die Verbindung zum Arduino und die Board-Auswahl.${NC}"
    echo -e "${YELLOW}Mögliche Lösungen:${NC}"
    echo "1. Stelle sicher, dass der richtige Port ausgewählt ist."
    echo "2. Überprüfe, ob der richtige Board-Typ ausgewählt ist."
    echo "3. Drücke bei Arduino UNO R4 den Reset-Knopf während des Hochladens."
    echo "4. Prüfe die USB-Kabelverbindung oder versuche ein anderes Kabel."
    echo "5. Versuche, das Board neu anzuschließen."
    echo "6. Führe 'sudo chmod a+rw $PORT' aus, um Berechtigungsprobleme zu beheben."
    exit 1
fi

echo -e "${GREEN}Arduino-Sketch erfolgreich hochgeladen!${NC}"
echo "Der Arduino ist nun bereit für die Steuerung des Drehtellers."
echo "Sie können die Funktionalität mit dem folgenden Befehl testen:"
echo "python -c \"import serial, time; s = serial.Serial('$PORT', 9600); time.sleep(2); s.write(b'1'); time.sleep(2); s.write(b'0'); s.close()\""