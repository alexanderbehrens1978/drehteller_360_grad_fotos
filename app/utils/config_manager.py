import os
import json
import logging

class ConfigManager:
    DEFAULT_CONFIG = {
        'camera': {
            'device_path': '/dev/video0',
            'type': 'webcam',  # or 'gphoto2'
            'resolution': {
                'width': 1280,
                'height': 720
            }
        },
        'gphoto2_profiles': {
            # Format: "Kameramodell": {Einstellungen}
            "Canon EOS 1200D": {
                "name": "Canon EOS 1200D",
                "settings": {
                    "/main/capturesettings/shutterspeed": "1/60",
                    "/main/imgsettings/imageformat": "Large Fine JPEG",
                    "/main/capturesettings/drivemode": "Single",
                    "/main/capturesettings/focusmode": "AI Focus",
                    "/main/capturesettings/autoexposuremode": "P"
                }
            },
            "Nikon D5600": {
                "name": "Nikon D5600",
                "settings": {
                    "/main/capturesettings/shutterspeed": "1/60",
                    "/main/imgsettings/imageformat": "JPEG Fine",
                    "/main/capturesettings/exposurecompensation": "0",
                    "/main/capturesettings/f-number": "8"
                }
            }
        },
        'arduino': {
            'port': '/dev/ttyACM0',
            'baudrate': 9600
        },
        'rotation': {
            'default_degrees': 15,
            'default_interval': 5
        }
    }

    def __init__(self, config_path=None):
        """Initialize configuration manager
        
        :param config_path: Path to the configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine the project directory
        self.project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # If no config path provided, use a default in the project directory
        if config_path is None:
            config_path = os.path.join(self.project_dir, 'config.json')

        self.config_path = config_path
        self.config = self.load_config()
        self.logger.debug(f"ConfigManager initialisiert mit Konfigurationspfad: {self.config_path}")

    def _merge_configs(self, default_config, user_config):
        """Führt zwei Konfigurationen zusammen
        
        Args:
            default_config: Standardkonfiguration
            user_config: Benutzerkonfiguration
            
        Returns:
            Zusammengeführte Konfiguration
        """
        result = default_config.copy()
        
        for key, value in user_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Rekursiv zusammenführen, wenn beide Werte Dictionaries sind
                result[key] = self._merge_configs(result[key], value)
            else:
                # Sonst den Wert aus der Benutzerkonfiguration übernehmen
                result[key] = value
                
        return result

    def load_config(self):
        """Lädt die Konfiguration aus der Datei oder erstellt die Standardkonfiguration
        
        Returns:
            Konfiguration als Dictionary
        """
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            # Versuche, bestehende Konfiguration zu laden
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Mit Standardkonfiguration zusammenführen, um sicherzustellen,
                    # dass alle Schlüssel existieren
                    merged_config = self._merge_configs(self.DEFAULT_CONFIG, config)
                    self.logger.debug("Konfiguration aus Datei geladen und zusammengeführt")
                    return merged_config
            else:
                # Standardkonfiguration erstellen
                config = self.DEFAULT_CONFIG.copy()
                self.save_config(config)
                self.logger.info("Standardkonfiguration erstellt und gespeichert")
                return config
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Konfiguration: {str(e)}")
            # Bei Fehlern Standardkonfiguration verwenden
            try:
                self.save_config(self.DEFAULT_CONFIG)
            except Exception as save_error:
                self.logger.error(f"Fehler beim Speichern der Standardkonfiguration: {str(save_error)}")
            return self.DEFAULT_CONFIG.copy()

    def save_config(self, new_config=None):
        """Speichert die Konfiguration in der Datei
        
        Args:
            new_config: Neue Konfiguration (optional)
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Verwende die angegebene Konfiguration oder die aktuelle
            config_to_save = new_config if new_config is not None else self.config

            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            # Konfiguration speichern
            with open(self.config_path, 'w') as f:
                json.dump(config_to_save, f, indent=4)

            # Aktuelle Konfiguration aktualisieren
            if new_config is not None:
                self.config = new_config.copy()
                
            self.logger.debug("Konfiguration erfolgreich gespeichert")
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Konfiguration: {str(e)}")
            return False

    def get(self, key, default=None):
        """Gibt einen Konfigurationswert zurück
        
        Args:
            key: Durch Punkte getrennter Schlüssel (z.B. 'camera.device_path')
            default: Standardwert, falls Schlüssel nicht gefunden (optional)
            
        Returns:
            Konfigurationswert oder Standardwert
        """
        try:
            # Schlüssel in Teile aufteilen
            parts = key.split('.')

            # Durch verschachteltes Dictionary navigieren
            value = self.config
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    return default

            return value
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen des Konfigurationswerts: {str(e)}")
            return default


# Globale Instanz des ConfigManager erstellen
config_manager = ConfigManager()
