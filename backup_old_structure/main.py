#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hauptanwendungseinstiegspunkt für die 360° Drehteller-Steuerung.
Startet den Webserver und initialisiert alle benötigten Komponenten.
"""

import os
import sys
import logging
from threading import Thread

# Stelle sicher, dass wir im richtigen Verzeichnis sind
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Initialisiere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("drehteller360.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("drehteller360")

# Stelle sicher, dass die benötigten Verzeichnisse existieren
os.makedirs('static/photos', exist_ok=True)
os.makedirs('static/sample_images', exist_ok=True)
os.makedirs('static/projects', exist_ok=True)

# Importiere erst nach Verzeichnissetup
from web import app
from device_detector import DeviceDetector
from config_manager import config_manager


def check_dependencies():
    """Überprüft, ob alle erforderlichen Abhängigkeiten installiert sind."""
    try:
        import flask
        import cv2
        import serial
        import numpy
        logger.info("Alle erforderlichen Python-Pakete sind installiert.")
        return True
    except ImportError as e:
        logger.error(f"Fehlende Abhängigkeit: {e}")
        print(f"Fehler: {e}. Bitte führen Sie 'pip install -r requirements.txt' aus.")
        return False


if __name__ == "__main__":
    logger.info("Starte 360° Drehteller-Steuerung...")

    if not check_dependencies():
        sys.exit(1)

    # Initialisiere Gerätedetektor im Hintergrund
    device_detector = DeviceDetector()
    detection_thread = Thread(target=device_detector.start_detection, daemon=True)
    detection_thread.start()

    # Starte den Flask-Server
    host = config_manager.get('web.host', '0.0.0.0')
    port = config_manager.get('web.port', 5000)
    debug = config_manager.get('web.debug', True)

    logger.info(f"Webserver wird gestartet auf {host}:{port}")
    app.run(host=host, port=port, debug=debug)