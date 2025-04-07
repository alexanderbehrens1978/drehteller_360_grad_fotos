#!/bin/bash

# Skript zum Upload des RGB-Sensor-Codes
# Aktualisiert am: 2025-04-07

# Pfad zum RGB-Sensor-Sketch
SKETCH_PATH="/d360/dev/rgb_Sensor/rgb_Sensor.ino"

# Prüfen ob der Sketch existiert
if [ ! -f "$SKETCH_PATH" ]; then
    echo "FEHLER: Der RGB-Sensor-Sketch wurde nicht gefunden unter: $SKETCH_PATH"
    exit 1
fi

# Finde das Arduino-Board mit CH341-Treiber (ttyUSB*)
echo "Suche Arduino-Board mit CH341-Treiber..."
ARDUINO_PORT=$(ls /dev/ttyUSB* 2>/dev/null | head -n1)

if [ -z "$ARDUINO_PORT" ]; then
    echo "FEHLER: Kein Arduino-Board gefunden. Bitte stecken Sie das Board an und versuchen Sie es erneut."
    exit 1
fi

echo "Arduino gefunden an Port: $ARDUINO_PORT"

# Kompiliere und lade den Sketch hoch
echo "Kompiliere den RGB-Sensor-Sketch..."
arduino-cli compile --fqbn arduino:avr:uno "$SKETCH_PATH"

if [ $? -ne 0 ]; then
    echo "FEHLER: Kompilierung fehlgeschlagen."
    exit 1
fi

echo "Lade Sketch auf den RGB-Sensor-Arduino hoch (Port: $ARDUINO_PORT)..."
arduino-cli upload -p "$ARDUINO_PORT" --fqbn arduino:avr:uno "$SKETCH_PATH"

if [ $? -eq 0 ]; then
    echo "✓ Upload erfolgreich abgeschlossen!"
else
    echo "FEHLER: Upload fehlgeschlagen."
    exit 1
fi
