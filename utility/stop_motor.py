#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stop_motor.py
Script zum Stoppen des Motors für den 360° Drehteller
"""

import os
import sys
import time
import logging
import argparse

# Füge das Projektverzeichnis zum Python-Pfad hinzu
project_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_dir)

from app.controllers.arduino_controller import ArduinoController

# Logger einrichten
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("stop_motor")

def main():
    """Hauptfunktion zum Stoppen des Motors"""
    # Argumente verarbeiten
    parser = argparse.ArgumentParser(description='Motor für den 360° Drehteller stoppen')
    parser.add_argument('-p', '--port', default='/dev/ttyACM0', help='Arduino Port (Standard: /dev/ttyACM0)')
    parser.add_argument('-b', '--baudrate', type=int, default=9600, help='Baudrate (Standard: 9600)')
    args = parser.parse_args()

    logger.info(f"Verbinde zum Arduino auf Port {args.port} mit Baudrate {args.baudrate}")

    # Arduino-Controller initialisieren
    arduino = ArduinoController(port=args.port, baudrate=args.baudrate)
    
    # Prüfe, ob Verbindung erfolgreich
    if not arduino.is_connected():
        logger.error("Konnte keine Verbindung zum Arduino herstellen. Bitte Port überprüfen.")
        return 1
    
    logger.info("Arduino verbunden. Stoppe Motor...")
    
    # Motor ausschalten
    if arduino.turn_motor_off():
        logger.info("Motor erfolgreich gestoppt")
        return 0
    else:
        logger.error("Fehler beim Stoppen des Motors")
        return 1

if __name__ == "__main__":
    sys.exit(main())
