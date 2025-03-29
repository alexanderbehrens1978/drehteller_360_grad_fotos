#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/__init__.py
Initialisiert die Flask-Anwendung und registriert alle Blueprints.
"""

import logging
from flask import Flask, g
from app.utils.config_manager import config_manager
from app.controllers.arduino_controller import ArduinoController
from app.controllers.camera_controller import CameraController
from app.controllers.turntable_controller import TurntableController
from app.utils.path_manager import PathManager

# Gemeinsam genutzte Controller-Instanzen
arduino_controller = None
camera_controller = None
turntable_controller = None

logging.basicConfig(
    filename='/d360/dev/logs/app.log',
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s',
    datefmt='%d.%m.%Y %H:%M:%S'
)



# Gemeinsam genutzte Hilfsprogramme
path_manager = PathManager()

def create_app(config_name=None):
    """
    Erstellt und konfiguriert die Flask-Anwendung
    
    Args:
        config_name: Name der Konfiguration ('development', 'production', 'testing')
    
    Returns:
        Flask-App-Instanz
    static_folder="../static"
    """
    app = Flask(__name__, 
                static_folder="../static",
                static_url_path='/static',
                template_folder="../templates")
    
    # Konfiguration laden
    app.config.from_object('app.config.DevelopmentConfig')
    if config_name == 'production':
        app.config.from_object('app.config.ProductionConfig')
    elif config_name == 'testing':
        app.config.from_object('app.config.TestingConfig')
    
    # Stelle sicher, dass Verzeichnisse existieren
    create_directories()
    
    # Controller initialisieren
    initialize_controllers()
    
    # Logging konfigurieren
    configure_logging(app)
    
    # Blueprints registrieren
    register_blueprints(app)
    
    @app.template_filter('datetime')
    def format_datetime(timestamp):
        """Formatiert einen Zeitstempel als lesbares Datum"""
        from datetime import datetime
        if timestamp is None:
            return ""
        try:
            date = datetime.fromtimestamp(timestamp)
            return date.strftime('%d.%m.%Y %H:%M')
        except Exception:
            return "Ungültiges Datum"

    @app.after_request
    def call_after_request_functions(response):
        """Führt alle nach einem Request registrierten Funktionen aus"""
        if hasattr(g, 'call_after_request'):
            for func in g.call_after_request:
                response = func(response)
        return response

    # Sicherheits-Header hinzufügen
    @app.after_request
    def add_security_headers(response):
        """Fügt Sicherheits-Header zu allen Antworten hinzu"""
        # Schutz vor Clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        # Aktivieren der XSS-Filterung im Browser
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Verhindern von MIME-Typ-Sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # Content-Security-Policy - weniger restriktiv für Entwicklung
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        return response
    
    return app

def create_directories():
    """Stellt sicher, dass alle erforderlichen Verzeichnisse existieren"""
    path_manager.ensure_directories()

def initialize_controllers():
    """Initialisiert die gemeinsam genutzten Controller"""
    global arduino_controller, camera_controller, turntable_controller
    
    try:
        # Arduino Controller
        port = config_manager.get('arduino.port')
        baudrate = config_manager.get('arduino.baudrate', 9600)
        if port:
            arduino_controller = ArduinoController(port, baudrate)
        
        # Kamera Controller
        camera_type = config_manager.get('camera.type', 'webcam')
        camera_device = config_manager.get('camera.device_path', '/dev/video0')
        resolution = config_manager.get('camera.resolution')
        camera_controller = CameraController(camera_type, camera_device, resolution)
        
        # Drehteller Controller (nutzt den Arduino Controller)
        turntable_controller = TurntableController(arduino_controller, 
                                                 config_manager.get('rotation.default_degrees', 15))
    except Exception as e:
        logging.error(f"Fehler bei der Controller-Initialisierung: {str(e)}")

def configure_logging(app):
    """Konfiguriert das Logging für die App"""
    log_level = logging.DEBUG if app.config['DEBUG'] else logging.INFO
    log_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    
    # File Handler - auf den korrekten Pfad geändert
    file_handler = logging.FileHandler('/d360/dev/logs/app.log')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_formatter)
    
    # Root Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Alle bestehenden Handler entfernen um Doppeleinträge zu vermeiden
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Neue Handler hinzufügen
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # App Logger konfigurieren
    app.logger.setLevel(log_level)

def register_blueprints(app):
    """Registriert alle Blueprints bei der App"""
    # Blueprint für Hauptseiten
    from app.blueprints.main import main_bp
    app.register_blueprint(main_bp)
    
    # Blueprint für API-Endpunkte
    from app.blueprints.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Blueprint für Einstellungen
    from app.blueprints.settings import settings_bp
    app.register_blueprint(settings_bp, url_prefix='/settings')
    
    # Blueprint für Projektverwaltung
    from app.blueprints.projects import projects_bp
    app.register_blueprint(projects_bp, url_prefix='/projects')
    
    # Blueprint für den 360° Viewer
    from app.blueprints.viewer import viewer_bp
    app.register_blueprint(viewer_bp, url_prefix='/viewer')
