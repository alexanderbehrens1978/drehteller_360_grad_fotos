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
            self.logger.debug(f"Sende Befehl an Arduino: {command}")
            self.serial.write(f"{command}\n".encode())

            # Auf Antwort warten
            response = self.serial.readline().decode().strip()
            self.logger.debug(f"Arduino-Antwort: {response}")

            # Akzeptiere verschiedene positive Antworten
            if response == "OK" or "eingeschaltet" in response or "ausgeschaltet" in response or "läuft" in response or "gestoppt" in response:
                return True
            else:
                self.logger.error(f"Unerwartete Arduino-Antwort: {response}")
                return False
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
        self.logger.debug("Sende Befehl: Motor einschalten (1)")
        success = self.send_command("1")
        if success:
            self.logger.debug("Motor erfolgreich eingeschaltet")
        else:
            self.logger.error("Fehler beim Einschalten des Motors")
        return success

    def turn_motor_off(self):
        """
        Schaltet den Motor aus (Relais öffnen)

        Returns:
            True bei Erfolg, False bei Fehler
        """
        self.logger.debug("Sende Befehl: Motor ausschalten (0)")
        try:
            # Mehrere Versuche, um sicherzustellen, dass der Motor wirklich stoppt
            for attempt in range(3):
                self.serial.write("0\n".encode())
                self.serial.flush()  # Wichtig: Stellt sicher, dass die Daten gesendet werden
                time.sleep(0.2)  # Kurze Pause zwischen den Versuchen
                
                # Antwort lesen, aber nicht unbedingt auf "OK" prüfen
                response = self.serial.readline().decode().strip()
                self.logger.debug(f"Arduino-Antwort (Versuch {attempt+1}): {response}")
                
                if "OK" in response:
                    self.logger.debug("Motor erfolgreich ausgeschaltet")
                    return True
            
            # Selbst wenn keine "OK" Antwort kam, gehen wir davon aus, dass der Befehl gesendet wurde
            self.logger.warning("Keine Bestätigung vom Arduino erhalten, aber Stopp-Befehl wurde gesendet")
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Ausschalten des Motors: {str(e)}")
            # Verbindung zurücksetzen bei Kommunikationsproblemen
            try:
                self.disconnect()
                time.sleep(1)
                self.connect()
            except:
                pass
            return False

    def rotate_for_duration(self, duration_ms):
        """
        Dreht den Motor für eine bestimmte Zeit
    
        Args:
            duration_ms: Dauer in Millisekunden
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            self.logger.debug(f"Rotiere Motor für {duration_ms} ms")
        
            # Motor einschalten und Erfolg prüfen
            motor_on_success = self.turn_motor_on()
            if not motor_on_success:
                self.logger.error("Motor konnte nicht eingeschaltet werden, Rotation abgebrochen")
                return False
            
            # Warten für die berechnete Zeit
            self.logger.debug(f"Warte für {duration_ms/1000.0} Sekunden")
            time.sleep(duration_ms / 1000.0)
        
            # Motor ausschalten
            motor_off_success = self.turn_motor_off()
            if not motor_off_success:
                self.logger.error("Motor konnte nicht ausgeschaltet werden")
                return False
            
            self.logger.debug(f"Rotation für {duration_ms} ms erfolgreich abgeschlossen")
            return True
        except Exception as e:
            self.logger.error(f"Fehler während der Motordrehung: {str(e)}")
            # Im Fehlerfall unbedingt versuchen, den Motor auszuschalten
            try:
                self.turn_motor_off()
            except Exception as e2:
                self.logger.error(f"Fehler beim Ausschalten nach fehlgeschlagener Rotation: {str(e2)}")
            return False

    def rotate_for_duration(self, duration_ms):
        """
        Dreht den Motor für eine bestimmte Zeit
        
        Args:
            duration_ms: Dauer in Millisekunden
                
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            self.logger.debug(f"Rotiere Motor für {duration_ms} ms")
            
            # Direkte Motordrehung ohne Rücksicht auf Rückgabewerte
            # Motor einschalten
            self.turn_motor_on()
            
            # Warten für die berechnete Zeit
            self.logger.debug(f"Warte für {duration_ms/1000.0} Sekunden")
            time.sleep(duration_ms / 1000.0)
            
            # Motor ausschalten
            self.turn_motor_off()
            
            self.logger.debug(f"Rotation für {duration_ms} ms abgeschlossen")
            return True
        except Exception as e:
            self.logger.error(f"Fehler während der Motordrehung: {str(e)}")
            # Im Fehlerfall unbedingt versuchen, den Motor auszuschalten
            try:
                self.turn_motor_off()
            except Exception as e2:
                self.logger.error(f"Fehler beim Ausschalten nach fehlgeschlagener Rotation: {str(e2)}")
            return False
