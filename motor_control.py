#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modul zur Steuerung eines einfachen Motors über Arduino.
Bietet Funktionen zum Ein- und Ausschalten des Motors.
"""

import os
import time
import logging
import serial
import threading
from device_detector import device_detector

# Logger konfigurieren
logger = logging.getLogger("drehteller360.motor_control")

class MotorController:
    """Steuert einen einfachen Motor über Arduino."""

    def __init__(self, port=None, baudrate=9600):
        """
        Initialisiert den Motor-Controller.

        Args:
            port: Serieller Port des Arduino (wenn None, wird automatisch erkannt)
            baudrate: Baudrate für die serielle Kommunikation
        """
        self.port = port
        self.baudrate = baudrate
        self.arduino = None
        self.running = False
        self.connected = False
        self.lock = threading.Lock()

    def connect(self):
        """Verbindet mit dem Arduino."""
        if self.connected:
            return True

        try:
            # Wenn kein Port angegeben wurde, versuche einen Arduino zu finden
            if not self.port:
                devices = device_detector.get_devices()
                arduinos = devices['arduinos']
                
                if not arduinos:
                    logger.error("Kein Arduino gefunden")
                    return False
                
                self.port = arduinos[0]['port']
                logger.info(f"Arduino gefunden an Port: {self.port}")
            
            # Verbindung zum Arduino herstellen
            self.arduino = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Warten auf Arduino-Reset nach Verbindungsaufbau
            self.connected = True
            logger.info(f"Verbindung zum Arduino an Port {self.port} hergestellt")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Verbinden mit Arduino: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Trennt die Verbindung zum Arduino."""
        if self.arduino and self.connected:
            try:
                self.stop_motor()  # Motor stoppen vor dem Trennen
                self.arduino.close()
                self.connected = False
                logger.info("Verbindung zum Arduino getrennt")
            except Exception as e:
                logger.error(f"Fehler beim Trennen der Arduino-Verbindung: {e}")

    def start_motor(self):
        """Schaltet den Motor ein."""
        with self.lock:
            if not self.connected and not self.connect():
                logger.error("Motor kann nicht gestartet werden: Keine Verbindung")
                return False
            
            try:
                command = "1\n"  # 1 für Einschalten
                self.arduino.write(command.encode())
                self.arduino.flush()  # Sicherstellen, dass die Daten gesendet werden
                self.running = True
                logger.info("Motor eingeschaltet")
                return True
            except Exception as e:
                logger.error(f"Fehler beim Einschalten des Motors: {e}")
                return False

    def stop_motor(self):
        """Schaltet den Motor aus."""
        with self.lock:
            if not self.connected:
                logger.info("Motor bereits getrennt")
                return True
            
            try:
                command = "0\n"  # 0 für Ausschalten
                self.arduino.write(command.encode())
                self.arduino.flush()  # Sicherstellen, dass die Daten gesendet werden
                self.running = False
                logger.info("Motor ausgeschaltet")
                return True
            except Exception as e:
                logger.error(f"Fehler beim Ausschalten des Motors: {e}")
                return False

    def is_running(self):
        """Gibt zurück, ob der Motor läuft."""
        return self.running and self.connected


# Globale Instanz für die Anwendung
motor_controller = MotorController()
