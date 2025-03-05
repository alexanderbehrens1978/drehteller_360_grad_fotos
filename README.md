# 360° Drehteller Fotografie-System

## Projektbeschreibung
Dieses Projekt ist ein vollständiges System zur Erstellung interaktiver 360°-Produktansichten mit einem Computer, Arduino und einer Kamera. Der Arduino steuert einen Drehteller über ein Relais, während die Kamera automatisch Fotos aufnimmt. Die Web-Oberfläche ermöglicht die Steuerung, Konfiguration und Anzeige der 360°-Ansichten.

![image](https://github.com/user-attachments/assets/9b665173-186d-4473-9a0b-8c1d37c44559)

## Voraussetzungen

### Hardware
- Computer mit Linux (empfohlen: Linux Mint, Ubuntu)
- Arduino Uno
- Relais-Modul (für 220V/30W Drehmotor)
- Webcam oder DSLR-Kamera mit USB-Anschluss
- Drehteller mit Schneckengetriebe (0,8° CW Drehgeschwindigkeit, 30W, 220V)

### Software
- Python 3.12+
- pip (Python-Paketmanager)
- Arduino IDE (für die Programmierung des Arduino)
- git (optional, für Versionskontrolle)

## Systemvoraussetzungen

### Erforderliche Systempakete
Installieren Sie vor der Einrichtung folgende Systempakete:

```bash
sudo apt-get update
sudo apt-get install -y \
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
    curl
```

## Installation

### 1. Rechte für Serial ändern

Füge deinen Benutzer zur dialout-Gruppe hinzu
```bash
sudo usermod -a -G dialout dein_benutzername
```

Setze die Berechtigungen für den Serial-Port
```bash
sudo chmod 666 /dev/ttyACM0
```

### 2. Repository klonen
```bash
gh repo clone alexanderbehrens1978/drehteller_360_grad_fotos
cd 360-drehteller
```

### 3. Python-Umgebung einrichten
```bash
# Virtuelle Umgebung erstellen
python3 -m venv myenv

# Virtuelle Umgebung aktivieren
source myenv/bin/activate

# pip aktualisieren
pip install --upgrade pip setuptools wheel

# Abhängigkeiten installieren
pip install -r requirements.txt
```

### 4. Arduino-Sketch hochladen
1. Öffnen Sie die Arduino IDE
2. Öffnen Sie die Datei `arduino/drehteller_controller.ino`
3. Wählen Sie das richtige Board (Arduino Uno) und den richtigen Port
4. Klicken Sie auf "Hochladen"

### 5. Anwendung starten
```bash
# Stellen Sie sicher, dass die virtuelle Umgebung aktiviert ist
python web.py
```

Die Webanwendung ist nun unter http://localhost:5000 erreichbar.

## Erste Schritte

1. Verbinden Sie Arduino und Kamera
2. Öffnen Sie die Einstellungsseite
3. Konfigurieren Sie Arduino-Port und Kameraeinstellungen
4. Erstellen Sie ein neues Projekt
5. Starten Sie eine 360°-Aufnahmesession

## Projektstruktur

```
360-drehteller/
├── web.py                  # Hauptanwendung
├── config_manager.py       # Konfigurationsmanagement
├── device_detector.py      # Geräte-Erkennung
├── arduino/                # Arduino-Sketche
│   └── drehteller_controller.ino
├── static/                 # Statische Dateien
│   ├── photos/             # Aufgenommene Fotos
│   └── projects/           # 360°-Projekt-Dateien
├── templates/              # HTML-Templates
├── requirements.txt        # Python-Abhängigkeiten
└── README.md               # Dieses Dokument
```

## Fehlerbehebung

### Arduino-Verbindung
- Überprüfen Sie den seriellen Port
- Stellen Sie sicher, dass der richtige Arduino-Sketch hochgeladen ist
- Prüfen Sie die Baudrate (Standard: 9600)

### Kamera-Probleme
- Webcams: `v4l2-ctl --list-devices`
- DSLR-Kameras: `gphoto2 --auto-detect`
- Stellen Sie sicher, dass keine andere Anwendung die Kamera blockiert

### Drehteller-Motor
- Überprüfen Sie die Verkabelung des Relais
- Stellen Sie sicher, dass der Motor korrekt angeschlossen ist

## Sicherheitshinweise
- Arbeiten Sie vorsichtig mit 220V-Geräten
- Verwenden Sie Schutzausrüstung
- Trennen Sie die Stromversorgung bei Wartungsarbeiten


Fehler oder Verbesserungsvorschläge? Eröffnen Sie gerne ein Issue im GitHub-Repository!
