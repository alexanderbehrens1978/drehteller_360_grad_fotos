# 360° Drehteller Fotografie-System

![image](https://github.com/user-attachments/assets/9d312c74-db23-406f-ab54-bb992f6d3330)

![image](https://github.com/user-attachments/assets/9056cffa-746e-4e18-bb13-297607d9ed17)

![image](https://github.com/user-attachments/assets/ef5de843-96d4-4e01-a69d-18bf5f79625b)


## Projektbeschreibung
Dieses Projekt ist ein komplettes System zur Erstellung interaktiver 360°-Produktansichten mit einem Computer, Arduino und einer Kamera. Der Arduino steuert einen Drehteller über ein Relais, während die Kamera automatisch Fotos aufnimmt. Die Web-Oberfläche ermöglicht die Steuerung, Konfiguration und Anzeige der 360°-Ansichten.

## Voraussetzungen

### Hardware
- Computer mit Linux Mint (oder anderer Linux-Distribution)
- Arduino Uno
- Relais-Modul oder Solid State Relais (für 220V/30W Drehmotor)
- Webcam oder DSLR-Kamera mit USB-Anschluss
- Drehteller mit Schneckengetriebe (0,8° CW Drehgeschwindigkeit, 30W, 220V)

### Software
- Python 3.8 oder höher (kompatibel mit Python 3.12)
- pip (Python-Paketmanager)
- Arduino IDE (für die Programmierung des Arduino)
- git (optional, für Versionskontrolle)

## Installation

### 1. Repository klonen
```bash
gh repo clone alexanderbehrens1978/drehteller_360_grad_fotos

cd drehteller_360_grad_fotos
```

### 2. Programm einrichten
```bash
# System komplett einrichten (erstellt virtuelle Umgebung und installiert alle Abhängigkeiten)
sudo ./setup_and_autostart.sh
```

Das Setup-Skript erkennt automatisch Ihre Python-Version und installiert die kompatiblen Bibliotheken. 
Es richtet außerdem einen systemd-Service ein, der die Anwendung beim Systemstart startet.

### 3. Optional: Weitere Setup-Optionen

Je nach Bedarf können Sie weitere Konfigurationen vornehmen:

```bash
# Headless-Version von OpenCV installieren (für Server ohne Bildschirm)
./drehteller.sh install-headless

# Module reparieren falls Probleme auftreten
./drehteller.sh fix-modules

# Diagnose der installierten Module
./drehteller.sh diagnose
```

### 4. Arduino-Sketch hochladen
1. Öffnen Sie die Arduino IDE
2. Öffnen Sie die Datei `arduino/turntable_controller.ino`
3. Wählen Sie das richtige Board (Arduino Uno) und den richtigen Port
4. Klicken Sie auf "Hochladen"

## Verwendung des Systems

### Zugriff auf die Webanwendung
Nach erfolgreicher Installation ist die Webanwendung unter folgender URL erreichbar:
- http://IHRE-IP:5000 (wenn Nginx nicht aktiviert wurde)
- http://IHRE-IP (wenn Nginx als Reverse-Proxy aktiviert wurde)

### Verwaltung des Dienstes
Das System bietet ein Hilfsskript für die einfache Verwaltung des Dienstes:

```bash
# Dienst starten
./drehteller.sh start

# Dienst stoppen
./drehteller.sh stop

# Dienst neustarten
./drehteller.sh restart

# Status des Dienstes anzeigen
./drehteller.sh status

# Logs des Dienstes anzeigen
./drehteller.sh logs
```

### Erste Schritte
1. Öffnen Sie die Einstellungsseite und konfigurieren Sie den Arduino-Port und die Kamera
2. Erstellen Sie ein neues Projekt und legen Sie die gewünschten Winkelschritte fest
3. Starten Sie eine neue Aufnahmesession, um 360°-Aufnahmen zu machen
4. Verwenden Sie den 360°-Viewer, um Ihre Aufnahmen zu betrachten

## Projektstruktur

Das Projekt ist in verschiedene Module und Verzeichnisse organisiert, um die Funktionalität sauber zu trennen:

```
drehteller_360_grad_fotos/
├── setup_and_autostart.sh        # Automatisches Setup-Skript
├── drehteller.sh                 # Verwaltungsskript
├── requirements.txt              # Python-Abhängigkeiten
├── web.py                        # Hauptanwendung, startet den Webserver
├── app.py                        # Alternative Startdatei
├── main.py                       # Programmlogik-Einstiegspunkt
├── config.json                   # Konfigurationsdatei
├── config_manager.py             # Konfigurationsverwaltung
├── project_manager.py            # Projektverwaltung
├── webcam_simulator.py           # Webcam-Simulationsmodul
├── device_detector.py            # Geräteerkennungsmodul
├── viewer_generator.py           # Erzeugung des 360°-Viewers
├── git_uploader.py               # Git-Upload-Funktionalität
├── webcam_detection_helper.py    # Hilfsmodul für Webcam-Erkennung
├── sample_images_generator.py    # Erzeugt Beispielbilder
├── generate_placeholder.py       # Erzeugt Platzhalterbilder
├── diagnose_modules.py           # Diagnose der Python-Module
├── upload_arduino_sketch.sh      # Arduino-Sketch-Upload-Skript
├── drehteller360.log             # Log-Datei
│
├── arduino/                      # Arduino-Sketches
│   └── turntable_controller.ino  # Hauptsketch für Drehtellersteuerung
│
├── arduino_drehteller_steuerung/ # Alternative Arduino-Sketches
│   └── arduino_drehteller_steuerung.ino
│
├── bin/                          # Ausführbare Dateien
│   └── arduino-cli               # Arduino Command-Line-Interface
│
├── config/                       # Konfigurationsmodule
│   ├── __init__.py
│   ├── settings.py               # Einstellungsmodul
│   └── __pycache__/
│
├── controllers/                  # Hardware-Steuerung
│   ├── __init__.py
│   ├── arduino_controller.py     # Arduino-Steuerung
│   ├── camera_controller.py      # Kamera-Steuerung
│   ├── turntable_controller.py   # Drehteller-Steuerung
│   └── __pycache__/
│
├── models/                       # Datenmodelle
│   ├── __init__.py
│   ├── project.py                # Projektdaten
│   ├── photo_session.py          # Fotositzungsdaten
│   └── __pycache__/
│
├── utils/                        # Hilfsfunktionen
│   ├── __init__.py
│   ├── arduino_finder.py         # Arduino-Erkennung
│   ├── camera_finder.py          # Kamera-Erkennung
│   ├── image_processor.py        # Bildverarbeitung
│   ├── background_remover.py     # Hintergrundentfernung
│   └── __pycache__/
│
├── utility/                      # Zusätzliche Hilfsskripte
│   ├── dateien-verzeichnisse-auflisten.py
│   ├── test_relais.py
│   └── zeige-alles-an.py
│
├── templates/                    # HTML-Templates
│   ├── base.html                 # Basis-Template
│   ├── index.html                # Hauptseite
│   ├── logs.html                 # Log-Anzeige
│   ├── project_edit.html         # Projektbearbeitung
│   ├── projects.html             # Projektübersicht
│   ├── settings.html             # Einstellungen
│   └── viewer.html               # 360°-Viewer
│
├── static/                       # Statische Dateien
│   ├── placeholder.jpg           # Platzhalterbild
│   ├── css/                      # Stylesheets
│   │   ├── index.css
│   │   ├── main.css
│   │   ├── project_edit.css
│   │   ├── projects.css
│   │   ├── settings.css
│   │   └── viewer.css
│   │
│   ├── js/                       # JavaScript
│   │   ├── index.js
│   │   ├── main.js
│   │   ├── settings.js
│   │   ├── viewer.js
│   │   └── viewer360.js
│   │
│   ├── photos/                   # Aufgenommene Fotos
│   │   └── .gitkeep
│   │
│   ├── projects/                 # Projektdateien
│   │
│   └── sample_images/            # Beispielbilder
│       ├── sample_image_0.jpg
│       ├── sample_image_1.jpg
│       ├── ...
│       └── sample_image_9.jpg
│
└── projects/                     # Projektdaten-Verzeichnis
```

## Funktionen

### Hauptfunktionen
- Responsive Webanwendung: Funktioniert auf PC, Tablet und Smartphone
- Projektverwaltung: Organisieren verschiedener 360°-Aufnahmen
- Automatische Kamera- und Arduino-Erkennung
- Interaktiver 360°-Viewer: Ähnlich professionellen Produktansichten im E-Commerce
- Exportfunktion für eigenständige HTML-Viewer

### Einstellungsmöglichkeiten
- Kameraauswahl (Webcam oder DSLR via gphoto2)
- Kameraauflösung
- Arduino-Port und Baudrate
- Winkelpräzision (5°, 10°, 15°, etc.)

## Fehlerbehebung

### Arduino wird nicht erkannt
- Überprüfen Sie die Verbindung des Arduino mit dem Computer
- Stellen Sie sicher, dass der richtige Arduino-Sketch hochgeladen wurde
- Prüfen Sie in den Einstellungen, ob der richtige Port ausgewählt ist

### Kamera funktioniert nicht
- Bei Webcams: Überprüfen Sie mit `v4l2-ctl --list-devices`
- Bei DSLR-Kameras: Überprüfen Sie mit `gphoto2 --auto-detect`
- Stellen Sie sicher, dass die Kamera nicht von anderen Anwendungen verwendet wird

### Relais/Motor schaltet nicht
- Überprüfen Sie die Verkabelung zwischen Arduino und Relais
- Stellen Sie sicher, dass der Motor korrekt angeschlossen ist
- Testen Sie das Relais mit dem Arduino-Sketch direkt

### Python-Abhängigkeiten und Module
Falls Probleme mit Python-Modulen auftreten:
- Führen Sie `./drehteller.sh diagnose` aus, um die Module zu überprüfen
- Verwenden Sie `./drehteller.sh fix-modules` um die OpenCV und NumPy Versionen zu reparieren
- Bei Python 3.12 werden spezielle Versionen von NumPy und OpenCV verwendet
- Auf Headless-Servern kann mit `./drehteller.sh install-headless` eine GUI-freie Version installiert werden
