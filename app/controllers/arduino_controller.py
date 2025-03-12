#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/controllers/arduino_controller.py
Controller für die Arduino-Kommunikation
"""

import time
import logging
import serial
import serial.tools.list_ports

# Logger einrichten
logger = logging.getLogger(__name__)

class ArduinoController:
    """Controller für die Kommunikation mit dem Arduino, der den Drehteller steuert"""

    def __init__(self, port=None, baudrate=9600):
        """
        Initialisiert die Arduino-Verbindung
        
        Args:
            port: Serieller Port (optional)
            baudrate: Baudrate (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False

        # Verbindung herstellen, wenn ein Port angegeben wurde
        if port:
            self.connect()
            
        self.logger.debug(f"ArduinoController initialisiert: Port={self.port}, Baudrate={self.baudrate}")

    def connect(self):
        """
        Stellt eine Verbindung zum Arduino her
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)  # Warten auf Arduino-Reset nach Verbindungsaufbau
            self.connected = True
            self.logger.info(f"Verbindung zum Arduino hergestellt: {self.port} @ {self.baudrate} Baud")
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Verbinden mit Arduino: {str(e)}")
            self.connected = False
            return False

    def disconnect(self):
        """
        Trennt die Verbindung zum Arduino
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if self.serial and self.connected:
            try:
                self.serial.close()
                self.connected = False
                self.logger.info("Verbindung zum Arduino getrennt")
                return True
            except Exception as e:
                self.logger.error(f"Fehler beim Trennen der Arduino-Verbindung: {str(e)}")
                return False
        return True  # War nicht verbunden

    def is_connected(self):
        """
        Prüft, ob die Verbindung zum Arduino hergestellt ist
        
        Returns:
            True wenn verbunden, sonst False
        """
        return self.connected

    def send_command(self, command):
        """
        Sendet einen Befehl an den Arduino
        
        Args:
            command: Zu sendender Befehl
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self.connected:
            if not self.connect():
                self.logger.error("Kann Befehl nicht senden: Keine Verbindung zum Arduino")
                return False

        try:
            # Befehl senden
            self.serial.write(f"{command}\n".encode())

            # Auf Antwort warten
            response = self.serial.readline().decode().strip()
            self.logger.debug(f"Arduino-Antwort: {response}")

            return response == "OK"
        except Exception as e:
            self.logger.error(f"Fehler beim Senden des Befehls an Arduino: {str(e)}")
            # Bei Fehler Verbindung trennen und neu verbinden
            self.disconnect()
            return False

    def turn_motor_on(self):
        """
        Schaltet den Motor ein (Relais schließen)
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        success = self.send_command("1")
        if success:
            self.logger.debug("Motor eingeschaltet")
        return success

    def turn_motor_off(self):
        """
        Schaltet den Motor aus (Relais öffnen)
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        success = self.send_command("0")
        if success:
            self.logger.debug("Motor ausgeschaltet")
        return success


def rotate_for_duration(self, duration_ms):
    """
    Dreht den Motor für eine bestimmte Zeit
    
    Args:
        duration_ms: Dauer in Millisekunden
        
    Returns:
        True bei Erfolg, False bei Fehler
    """
    # Validierung der Eingabe
    try:
        duration_ms = float(duration_ms)
        if duration_ms <= 0 or duration_ms > 60000:  # Maximal 1 Minute
            self.logger.error(f"Ungültige Drehzeit: {duration_ms} ms")
            return False
    except (TypeError, ValueError):
        self.logger.error(f"Ungültiger Wert für Drehzeit: {duration_ms}")
        return False
    
    if not self.turn_motor_on():
        return False

    # Warten für die angegebene Dauer
    time.sleep(duration_ms / 1000.0)

    # Motor ausschalten
    success = self.turn_motor_off()
    if success:
        self.logger.debug(f"Motor für {duration_ms} ms gedreht")
    return success



