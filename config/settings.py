# Datei: config/settings.py
# Modul zur Verwaltung von Anwendungseinstellungen

import os
import json
import logging
from pathlib import Path


class Settings:
    """Klasse zur Verwaltung der Anwendungseinstellungen"""

    def __init__(self, config_file=None):
        """Initialisiert die Einstellungen aus einer Konfigurationsdatei"""
        self.logger = logging.getLogger(__name__)

        # Standardpfad für Konfigurationsdatei
        if config_file is None:
            self.config_dir = os.path.join(os.path.expanduser('~'), '.360-drehteller')
            os.makedirs(self.config_dir, exist_ok=True)
            self.config_file = os.path.join(self.config_dir, 'settings.json')
        else:
            self.config_file = config_file

        # Standardeinstellungen
        self.arduino_port = None
        self.arduino_baudrate = 9600
        self.camera_type = 'webcam'  # 'webcam' oder 'gphoto2'
        self.camera_device = '/dev/video0'
        self.camera_resolution = '1920x1080'
        self.project_dir = os.path.join(os.path.expanduser('~'), 'Drehteller-Projekte')

        # Konfiguration laden, falls vorhanden
        self.load()

    def load(self):
        """Lädt die Einstellungen aus der Konfigurationsdatei"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)

                    # Einstellungen aus der Konfigurationsdatei übernehmen
                    self.arduino_port = config.get('arduino_port', self.arduino_port)
                    self.arduino_baudrate = config.get('arduino_baudrate', self.arduino_baudrate)
                    self.camera_type = config.get('camera_type', self.camera_type)
                    self.camera_device = config.get('camera_device', self.camera_device)
                    self.camera_resolution = config.get('camera_resolution', self.camera_resolution)
                    self.project_dir = config.get('project_dir', self.project_dir)

                    self.logger.info("Einstellungen aus %s geladen", self.config_file)
        except Exception as e:
            self.logger.error("Fehler beim Laden der Einstellungen: %s", str(e))
            # Bei Fehler werden Standardeinstellungen verwendet

    def save(self):
        """Speichert die aktuellen Einstellungen in der Konfigurationsdatei"""
        try:
            # Stellen Sie sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            # Konfiguration in eine Datei schreiben
            with open(self.config_file, 'w') as f:
                config = {
                    'arduino_port': self.arduino_port,
                    'arduino_baudrate': self.arduino_baudrate,
                    'camera_type': self.camera_type,
                    'camera_device': self.camera_device,
                    'camera_resolution': self.camera_resolution,
                    'project_dir': self.project_dir
                }
                json.dump(config, f, indent=4)

            self.logger.info("Einstellungen in %s gespeichert", self.config_file)
            return True
        except Exception as e:
            self.logger.error("Fehler beim Speichern der Einstellungen: %s", str(e))
            return False

    def get_camera_width_height(self):
        """Liefert die Kameraauflösung als Tupel (Breite, Höhe)"""
        try:
            if 'x' in self.camera_resolution:
                width, height = self.camera_resolution.split('x')
                return int(width), int(height)
            else:
                return 1920, 1080  # Standardwerte
        except Exception:
            return 1920, 1080  # Standardwerte bei Fehler