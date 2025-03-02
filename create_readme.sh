bashCopy#!/bin/bash
# create_readme.sh

cat > README.md << 'EOL'
# 360° Drehteller Fotografie-System

## Projektbeschreibung
Dieses Projekt ist ein vollständiges System zur Erstellung interaktiver 360°-Produktansichten mit einem Raspberry Pi, Arduino und einer Kamera. Es bietet eine responsive Weboberfläche zur Steuerung eines motorisierten Drehtellers, der eine Plattform über ein Schneckengetriebe dreht, während automatisch Fotos aufgenommen werden.

Die Anwendung ermöglicht es, professionelle 360°-Produktansichten zu erstellen, ähnlich denen, die in modernen E-Commerce-Plattformen verwendet werden.

## Funktionen

- **Motorgesteuerte Plattform**: Steuerung eines 220V/30W Drehtellers (0,8° pro Sekunde) über Arduino und Relais
- **Automatische Fotoaufnahme**: Unterstützung für Webcams und DSLR-Kameras (via gphoto2)
- **Responsive Benutzeroberfläche**: Funktioniert auf Desktop, Tablet und Smartphone
- **Projektverwaltung**: Organisiert verschiedene 360°-Produkt-Aufnahmen
- **Interaktiver 360°-Viewer**: Mit Auto-Rotation und Mouse/Touch Drag-Funktion
- **Konfigurierbare Einstellungen**: Einstellbare Schrittwinkel, Foto-Intervalle und Kamera-Auflösung

## Voraussetzungen

### Hardware
- Raspberry Pi 4 (mit Raspbian OS)
- Arduino Uno (R3 oder R4)
- Relais-Modul (für 220V/30W Drehmotor)
- Webcam oder DSLR-Kamera mit USB-Anschluss
- Schneckengetriebe-Drehteller (0,8° CW Drehgeschwindigkeit)

### Software
- Python 3.8+
- Flask
- OpenCV
- Arduino IDE oder Arduino CLI

## Installation

### Automatische Installation

Das Projekt enthält Skripte zur automatischen Installation und Einrichtung:

1. Klone das Repository:
```bash
git clone https://github.com/[USERNAME]/360-drehteller.git
cd 360-drehteller

Führe das Setup-Skript aus (dies richtet alles ein, inklusive Autostart):

bashCopysudo ./setup_and_autostart.sh
Das Skript erledigt:

Installation aller Abhängigkeiten
Einrichtung einer virtuellen Python-Umgebung
Erstellung des Autostart-Services
Konfiguration von Nginx (optional)
Erstellung der Verzeichnisstruktur


Übertrage den Arduino-Code:

bashCopy./upload_arduino_sketch.sh
Manuelle Installation
Alternativ kannst du die einzelnen Komponenten manuell installieren:

System-Abhängigkeiten:

bashCopysudo apt-get update
sudo apt-get install -y python3-venv python3-dev python3-pip python3-opencv fswebcam v4l-utils libatlas-base-dev git

Python-Umgebung:

bashCopypython3 -m venv myenv
source myenv/bin/activate
pip install -r requirements.txt

Arduino-Sketch übertragen (verwende die Arduino IDE oder unser Skript)

Verwendung
Weboberfläche starten
Die Anwendung ist über deinen Webbrowser erreichbar:

Wenn du Nginx eingerichtet hast: http://raspberry-pi-ip/
Ohne Nginx: http://raspberry-pi-ip:5000/

Dienst verwalten
Verwende das Hilfsskript zur Verwaltung des Dienstes:
bashCopy./drehteller.sh start    # Dienst starten
./drehteller.sh stop     # Dienst stoppen
./drehteller.sh restart  # Dienst neustarten
./drehteller.sh status   # Status anzeigen
./drehteller.sh logs     # Logs anzeigen
360° Aufnahme erstellen

Wähle auf der Startseite "360° Projekte verwalten"
Erstelle ein neues Projekt
Konfiguriere die Aufnahmeparameter (Drehwinkel, Intervall)
Starte die 360°-Aufnahme mit "Volle 360° Aufnahme"
Warte, bis die Aufnahme abgeschlossen ist
Öffne die 360°-Ansicht über "360° Ansicht"

Verzeichnisstruktur
Copy360-drehteller/
├── web.py                    # Flask-Hauptanwendung
├── project_manager.py        # Projektverwaltung
├── config_manager.py         # Konfigurationsverwaltung
├── git_uploader.py           # Git-Upload-Tool
├── upload_arduino_sketch.sh  # Arduino-Upload
├── setup_and_autostart.sh    # Automatische Einrichtung
├── drehteller.sh             # Dienstverwaltung
├── templates/                # HTML-Templates
├── static/                   # Statische Assets (CSS, JS, Bilder)
└── projects/                 # Projektdaten
Konfiguration
Die Anwendung kann über die Einstellungsseite im Webinterface konfiguriert werden:

Kameraeinstellungen: Pfad, Auflösung, Typ (Webcam/DSLR)
Arduino-Einstellungen: Port, Baudrate
Rotationseinstellungen: Standardwinkel, Intervall
Simulator-Modus: Für Tests ohne Hardware

Fehlerbehebung
Kamera wird nicht erkannt

Überprüfe die Verbindung zur Kamera
Führe v4l2-ctl --list-devices aus, um verfügbare Kameras zu sehen
Stelle sicher, dass der Benutzer in der video-Gruppe ist: sudo usermod -a -G video $USER

Arduino-Verbindung funktioniert nicht

Überprüfe den seriellen Port in den Einstellungen
Führe ls /dev/tty* aus, um verfügbare Ports zu sehen
Stelle sicher, dass der Benutzer in der dialout-Gruppe ist: sudo usermod -a -G dialout $USER

Drehteller bewegt sich nicht

Überprüfe die Verkabelung zum Relais
Teste das Relais mit dem Skript serial-test.py
Überprüfe die Arduino-Firmware mit dem Arduino IDE Serial Monitor

Weiterentwicklung
Code-Struktur
Die Anwendung verwendet einen modularen Ansatz mit separaten Komponenten für:

Web-Interface (Flask)
Projektverwaltung
Kamerafunktionen
Arduino-Steuerung
360°-Viewer

Jedes Modul ist auf maximal 60 Zeilen Code begrenzt, um Clean Code-Prinzipien zu folgen.
Mögliche Erweiterungen

Integration von Bildbearbeitung für bessere Produktdarstellung
Zusätzliche Beleuchtungssteuerung
Automatische Hintergrundentfernung
Export in verschiedene 360°-Viewer-Formate

Mitwirkende und Lizenz
Dieses Projekt steht unter MIT-Lizenz. Beiträge und Verbesserungen sind willkommen.
Entwickelt von [DEIN NAME]

Bei Fragen oder Problemen öffne ein Issue im GitHub-Repository oder kontaktiere den Entwickler direkt.
EOL
echo "README.md erfolgreich erstellt!"
