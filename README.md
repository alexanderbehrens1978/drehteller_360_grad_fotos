# 360° Drehteller Steuerung mit Flask Blueprints

Diese Anwendung steuert einen Arduino-basierten Drehteller für 360°-Produktfotografie und stellt einen Webserver für die Steuerung und Anzeige der Fotos bereit.

## Neue Blueprint-Struktur

Die Anwendung wurde auf eine Blueprint-basierte Struktur umgestellt, um die Wartbarkeit und Skalierbarkeit zu verbessern.

### Vorteile der Blueprint-Struktur

- Bessere Codeorganisation und Modularität
- Getrennte Verantwortlichkeiten für verschiedene Funktionen
- Leichtere Wartung und Erweiterung
- Verbessertes Fehlerhandling
- Mehr Testbarkeit

## Installation

### Voraussetzungen

- Python 3.8 oder höher
- Arduino Uno oder kompatibles Board
- Webcam oder gphoto2-kompatible Kamera
- Relais-Modul für die Motorsteuerung

### Installationsschritte

1. Klone das Repository:
   ```bash
   git clone https://github.com/yourusername/drehteller_360_grad_fotos.git
   cd drehteller_360_grad_fotos
   ```

2. Erstelle eine virtuelle Umgebung und installiere die Abhängigkeiten:
   ```bash
   python -m venv myenv
   source myenv/bin/activate  # Unter Windows: myenv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Lade den Arduino-Sketch hoch:
   ```bash
   ./upload_arduino_sketch.sh
   ```
   Alternativ kann der Sketch (`arduino_drehteller_steuerung.ino`) auch über die Arduino IDE hochgeladen werden.

4. Starte die Anwendung:
   ```bash
   python run.py
   ```

Die Anwendung ist dann unter [http://localhost:5000](http://localhost:5000) verfügbar.

## Konfiguration

Die Anwendung unterstützt sowohl eine vorkonfigurierte Standardkonfiguration als auch eine benutzerdefinierte Konfiguration.

### Konfiguration anpassen

Die Konfiguration kann über die Webschnittstelle unter der Einstellungsseite angepasst werden.

Alternativ kann die Konfigurationsdatei `config.json` manuell bearbeitet werden:

```json
{
    "camera": {
        "device_path": "/dev/video0",
        "type": "webcam",
        "resolution": {
            "width": 1920,
            "height": 1080
        }
    },
    "arduino": {
        "port": "/dev/ttyACM0",
        "baudrate": 9600
    },
    "rotation": {
        "default_degrees": 15,
        "default_interval": 5
    },
    "simulator": {
        "enabled": true
    }
}
```

## Verwendung

### Hauptfunktionen

1. **Projekte verwalten**: Erstelle und verwalte Projekte für verschiedene Produkte.
2. **Drehteller steuern**: Steuere den Drehteller manuell oder automatisch.
3. **360°-Aufnahmen erstellen**: Nehme Fotos in bestimmten Winkelschritten auf.
4. **360°-Viewer anzeigen**: Betrachte die erstellten 360°-Ansichten interaktiv.

### Simulatormodus

Wenn kein Arduino oder keine Kamera verfügbar ist, kann der Simulatormodus aktiviert werden, um die Anwendung zu testen.

## Projektstruktur

```
drehteller_360_grad_fotos/
├── app/                        # Hauptanwendungsverzeichnis
│   ├── __init__.py            # App-Initialisierung
│   ├── config.py              # Konfigurationsklassen
│   ├── models/                # Datenmodelle
│   ├── blueprints/            # Flask-Blueprints
│   ├── utils/                 # Hilfsfunktionen
│   ├── controllers/           # Hardware-Controller
│   └── static/                # Statische Dateien
├── templates/                  # HTML-Templates
├── static/                     # CSS, JS, Bilder
│   ├── css/
│   ├── js/
│   ├── photos/                # Aufgenommene Fotos
│   └── sample_images/         # Beispielbilder für Simulator
├── run.py                      # Start-Skript
└── requirements.txt            # Python-Abhängigkeiten
```

## Blueprints

Die Anwendung verwendet folgende Blueprints:

- `main`: Hauptseiten und grundlegende Funktionen
- `api`: API-Endpunkte für AJAX-Anfragen
- `settings`: Einstellungsverwaltung
- `projects`: Projektverwaltung

## Hardware

### Arduino-Verbindung

Der Arduino steuert ein Relais, das den Drehteller-Motor ein- und ausschaltet. Die Kommunikation erfolgt über die serielle Schnittstelle mit folgenden Befehlen:

- `1`: Motor einschalten
- `0`: Motor ausschalten

### Kamera-Unterstützung

Die Anwendung unterstützt:

- Webcams über OpenCV
- DSLR-Kameras über gphoto2

