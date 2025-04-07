import logging
import requests
import time
from app.utils.config_manager import config_manager

class RGBArduinoController:
    """Controller für die Kommunikation mit dem Arduino, der den RGB-Sensor steuert"""

    def __init__(self):
        """Initialisiert den RGB-Arduino-Controller"""
        self.logger = logging.getLogger(__name__)
        self.ip_address = config_manager.get('rgb_arduino.ip_address', '192.168.188.177')
        self.port = config_manager.get('rgb_arduino.port', 80)
        self.threshold = config_manager.get('rgb_arduino.threshold', 120)
        self.connection_type = config_manager.get('rgb_arduino.connection_type', 'ethernet')
        self.last_update_time = 0
        self.update_interval = 5  # Nur alle 5 Sekunden aktualisieren

    def get_status(self):
        """
        Holt den aktuellen Status des RGB-Sensors
        
        Returns:
            dict: Status-Informationen oder None bei Fehler
        """
        if self.connection_type != 'ethernet':
            self.logger.debug("RGB-Arduino nicht über Ethernet verbunden")
            return None
            
        try:
            url = f"http://{self.ip_address}:{self.port}/status"
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                self.logger.debug("RGB-Sensor-Status erfolgreich abgerufen")
                return response.json()
            else:
                self.logger.error(f"Fehler beim Abrufen des RGB-Sensor-Status: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Fehler bei der Kommunikation mit RGB-Arduino: {str(e)}")
            return None
    
    def update_settings(self, force=False):
        """
        Aktualisiert die Einstellungen auf dem RGB-Arduino
        
        Args:
            force: Wenn True, wird die Aktualisierung erzwungen, auch wenn das Update-Intervall nicht abgelaufen ist
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        # Prüfen, ob das Update-Intervall abgelaufen ist
        current_time = time.time()
        if not force and (current_time - self.last_update_time) < self.update_interval:
            self.logger.debug("Update-Intervall nicht abgelaufen, überspringe Update")
            return True
            
        # Aktualisiere die Einstellungen aus der Konfiguration
        self.ip_address = config_manager.get('rgb_arduino.ip_address', '192.168.188.177')
        self.port = config_manager.get('rgb_arduino.port', 80)
        self.threshold = config_manager.get('rgb_arduino.threshold', 120)
        self.connection_type = config_manager.get('rgb_arduino.connection_type', 'ethernet')
        
        # Wenn RGB-Arduino deaktiviert oder nicht über Ethernet verbunden, nichts tun
        if self.connection_type != 'ethernet':
            self.logger.debug("RGB-Arduino nicht über Ethernet verbunden")
            return True
            
        # Threshold-Wert an RGB-Arduino senden
        try:
            url = f"http://{self.ip_address}:{self.port}?threshold={self.threshold}"
            self.logger.info(f"Sende Threshold-Wert {self.threshold} an RGB-Arduino ({self.ip_address}:{self.port})")
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                self.logger.info(f"Threshold-Wert erfolgreich aktualisiert: {self.threshold}")
                self.last_update_time = current_time
                return True
            else:
                self.logger.error(f"Fehler beim Aktualisieren des Threshold-Werts: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler bei der Kommunikation mit RGB-Arduino: {str(e)}")
            return False
    
    def clear_values(self):
        """
        Setzt die Messwerte des RGB-Sensors zurück
        
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        if self.connection_type != 'ethernet':
            self.logger.debug("RGB-Arduino nicht über Ethernet verbunden")
            return False
            
        try:
            url = f"http://{self.ip_address}:{self.port}?action=clear"
            self.logger.info(f"Sende Clear-Befehl an RGB-Arduino ({self.ip_address}:{self.port})")
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                self.logger.info("RGB-Sensor-Werte erfolgreich zurückgesetzt")
                return True
            else:
                self.logger.error(f"Fehler beim Zurücksetzen der RGB-Sensor-Werte: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler bei der Kommunikation mit RGB-Arduino: {str(e)}")
            return False
    
    def adjust_brightness(self, brightness_value):
        """
        Passt die Helligkeit des RGB-Sensors an
        
        Args:
            brightness_value: Helligkeitswert (0-255)
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        if self.connection_type != 'ethernet':
            self.logger.debug("RGB-Arduino nicht über Ethernet verbunden")
            return False
            
        try:
            url = f"http://{self.ip_address}:{self.port}?brightness={brightness_value}"
            self.logger.info(f"Sende Helligkeitswert {brightness_value} an RGB-Arduino ({self.ip_address}:{self.port})")
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                self.logger.info(f"Helligkeitswert erfolgreich aktualisiert: {brightness_value}")
                return True
            else:
                self.logger.error(f"Fehler beim Aktualisieren des Helligkeitswerts: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler bei der Kommunikation mit RGB-Arduino: {str(e)}")
            return False
    
    def is_black_detected(self):
        """
        Prüft, ob der RGB-Sensor Schwarz erkennt
        
        Returns:
            bool: True wenn Schwarz erkannt wird, False sonst oder bei Fehler
        """
        status = self.get_status()
        if status and 'isBlack' in status:
            return status['isBlack']
        return False

# Globale Instanz des Controllers
rgb_arduino_controller = None

def init_rgb_arduino_controller():
    """Initialisiert den globalen RGB-Arduino-Controller"""
    global rgb_arduino_controller
    if rgb_arduino_controller is None:
        rgb_arduino_controller = RGBArduinoController()
        # Sende die Konfiguration beim Start
        rgb_arduino_controller.update_settings(force=True)
    return rgb_arduino_controller
