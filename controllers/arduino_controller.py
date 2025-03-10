# Datei: controllers/arduino_controller.py
# Modul zur Steuerung des Arduino

import time
import logging
import serial
import serial.tools.list_ports


class ArduinoController:
    """Klasse zur Steuerung des Arduino, der den Drehteller antreibt"""

    def __init__(self, port=None, baudrate=9600):
        """Initialisiert die Arduino-Verbindung"""
        self.logger = logging.getLogger(__name__)
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.connected = False

        # Verbindung herstellen, wenn ein Port angegeben wurde
        if port:
            self.connect()

    def connect(self):
        """Stellt eine Verbindung zum Arduino her"""
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)  # Warten auf Arduino-Reset nach Verbindungsaufbau
            self.connected = True
            self.logger.info("Verbindung zum Arduino hergestellt: %s @ %d Baud",
                             self.port, self.baudrate)
            return True
        except Exception as e:
            self.logger.error("Fehler beim Verbinden mit Arduino: %s", str(e))
            self.connected = False
            return False

    def disconnect(self):
        """Trennt die Verbindung zum Arduino"""
        if self.serial and self.connected:
            try:
                self.serial.close()
                self.connected = False
                self.logger.info("Verbindung zum Arduino getrennt")
                return True
            except Exception as e:
                self.logger.error("Fehler beim Trennen der Arduino-Verbindung: %s", str(e))
                return False
        return True  # War nicht verbunden

    def is_connected(self):
        """Prüft, ob die Verbindung zum Arduino hergestellt ist"""
        return self.connected

    def send_command(self, command):
        """Sendet einen Befehl an den Arduino"""
        if not self.connected:
            if not self.connect():
                self.logger.error("Kann Befehl nicht senden: Keine Verbindung zum Arduino")
                return False

        try:
            # Befehl senden
            self.serial.write(f"{command}\n".encode())

            # Auf Antwort warten
            response = self.serial.readline().decode().strip()
            self.logger.debug("Arduino-Antwort: %s", response)

            return response == "OK"
        except Exception as e:
            self.logger.error("Fehler beim Senden des Befehls an Arduino: %s", str(e))
            # Bei Fehler Verbindung trennen und neu verbinden
            self.disconnect()
            return False

    def turn_motor_on(self):
        """Schaltet den Motor ein (Relais schließen)"""
        return self.send_command("1")

    def turn_motor_off(self):
        """Schaltet den Motor aus (Relais öffnen)"""
        return self.send_command("0")

    def rotate_for_duration(self, duration_ms):
        """Dreht den Motor für eine bestimmte Zeit (in Millisekunden)"""
        if not self.turn_motor_on():
            return False

        # Warten für die angegebene Dauer
        time.sleep(duration_ms / 1000.0)

        # Motor ausschalten
        return self.turn_motor_off()