# 360° Drehteller Steuerung mit Flask Blueprints

Am 12.03.2025 war eine lauffähige Version

Diese Anwendung steuert einen Arduino-basierten Drehteller für 360°-Produktfotografie und stellt einen Webserver für die Steuerung und Anzeige der Fotos bereit.

![image](https://github.com/user-attachments/assets/1002e8a1-6501-4488-9037-c9bfe3c2c7c6)

![image](https://github.com/user-attachments/assets/d2a3dae9-8e4d-444b-9fe7-907211f177e2)

![image](https://github.com/user-attachments/assets/fcafca37-3fb7-457c-8c0b-c64b37069317)

![image](https://github.com/user-attachments/assets/3850bc8c-f79a-42f6-b97c-a1c7f981bec4)

![image](https://github.com/user-attachments/assets/c8f313df-cc5c-426d-af77-736d7288b2d2)


![image](https://github.com/user-attachments/assets/7e92aaea-9f27-4d29-991c-b5b144baa529)

![image](https://github.com/user-attachments/assets/65078908-9dc8-42e0-b8f6-60e6c0e90d1f)



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
   gh repo clone alexanderbehrens1978/drehteller_360_grad_fotos
   cd drehteller_360_grad_fotos
   ```

2. Setup Tool starten
   ```bash
   sudo ./setup_and_autostart.sh
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
    }
}
```

## Verwendung

### Hauptfunktionen

1. **Projekte verwalten**: Erstelle und verwalte Projekte für verschiedene Produkte.
2. **Drehteller steuern**: Steuere den Drehteller manuell oder automatisch.
3. **360°-Aufnahmen erstellen**: Nehme Fotos in bestimmten Winkelschritten auf.
4. **360°-Viewer anzeigen**: Betrachte die erstellten 360°-Ansichten interaktiv.


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
│   └── photos/                 # aufgenommene Bilder 
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

### Befehle zum suchen von Strings in Dateien und Unterverzeichnissen

```bash
grep -rnw "360° Drehteller Steuerung" .
```

### Wenn Fotos erstellt werden, aber der Ardunio sich nicht dreht bzw. einmal dreht.

```bash
sudo lsof /dev/ttyACM0
```

### Problemlösung

- Überprüfen ob die Kamera eingeschaltet ist
- überprüfen ob die USB Stecker alle richtig sitzen.
- Hat die Box Strom
