# app/config.py: Verbesserte Konfigurationsklasse
import os
import secrets
from pathlib import Path

class Config:
    """Zentrale Konfigurationsklasse mit Pfadverwaltung"""
    
    # Grundlegende Verzeichnisse
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_DIR = BASE_DIR / 'static'
    PHOTOS_DIR = STATIC_DIR / 'photos'
    PROJECTS_DIR = STATIC_DIR / 'projects'
    TEMP_DIR = STATIC_DIR / 'temp'
    
    # Sicherheitseinstellungen
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    
    # Standardkonfigurationen
    DEFAULT_ROTATION_DEGREES = 15
    DEFAULT_ROTATION_INTERVAL = 5
    DEFAULT_CAMERA_TYPE = 'webcam'
    DEFAULT_RESOLUTION = {
        'width': 1920,
        'height': 1080
    }
    
    def __init__(self):
        """Initialisiere Verzeichnisse"""
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Stelle sicher, dass alle erforderlichen Verzeichnisse existieren"""
        for directory in [
            self.STATIC_DIR,
            self.PHOTOS_DIR,
            self.PROJECTS_DIR,
            self.TEMP_DIR
        ]:
            directory.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_photos_path(cls, filename=None):
        """Generiere vollständigen Pfad zu Fotos"""
        return str(cls.PHOTOS_DIR / filename) if filename else str(cls.PHOTOS_DIR)
    
    @classmethod
    def get_project_path(cls, project_id=None):
        """Generiere vollständigen Pfad zu Projekten"""
        return str(cls.PROJECTS_DIR / project_id) if project_id else str(cls.PROJECTS_DIR)

# Verschiedene Umgebungskonfigurationen
class DevelopmentConfig(Config):
    """Entwicklungsumgebung-Konfiguration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Produktionsumgebung-Konfiguration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testumgebung-Konfiguration"""
    DEBUG = True
    TESTING = True
