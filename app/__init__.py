#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/__init__.py
Initialisiert die Flask-Anwendung und registriert alle Blueprints.
"""

import os
import logging
from flask import Flask
from app.utils.config_manager import config_manager
from app.controllers.arduino_controller import ArduinoController
from app.controllers.camera_controller import CameraController
from app.controllers.turntable_controller import TurntableController
from app.utils.path_manager import PathManager

# Gemeinsam genutzte Controller-Instanzen
arduino_controller = None
camera_controller = None
turntable_controller = None

# Gemeinsam genutzte Hilfsprogramme
path_manager = PathManager()

def create_app(config_name=None):
    """
    Erstellt und konfiguriert die Flask-Anwendung
    
    Args:
        config_name: Name der Konfiguration ('development', 'production', 'testing')
    
    Returns:
        Flask-App-Instanz
    """
    app = Flask(__name__, 
                static_folder="../static",
                static_url_path='/static',
                template_folder="../templates")
    
    # Konfiguration laden
    app.config.from_object('app.config.DevelopmentConfig')
    if config_name == 'production':
        app.config.from_object('app.config.ProductionConfig')
        # Debug-Modus in Produktion deaktivieren
        app.config['DEBUG'] = False
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
    
    # Globale Routen direkt auf Anwendungsebene registrieren
    register_global_routes(app)
    
    return app

def create_directories():
    """Stellt sicher, dass alle erforderlichen Verzeichnisse existieren"""
    path_manager.ensure_directories()
    
    # Dokumentationsverzeichnis erstellen
    doc_dir = os.path.join(path_manager.base_dir, 'doc')
    os.makedirs(doc_dir, exist_ok=True)

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
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # File Handler
    file_handler = logging.FileHandler('drehteller360.log')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(log_formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(log_formatter)
    
    # Root Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
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

def register_global_routes(app):
    """Registriert globale Routen direkt auf Anwendungsebene"""
    from app.utils.config_manager import config_manager
    from app.utils.viewer_generator import viewer_generator
    from flask import request, jsonify
    import os
    
    @app.route('/get_config')
    def get_config():
        """Gibt die aktuelle Konfiguration zurück"""
        return jsonify(config_manager.config)
    
    @app.route('/save_config', methods=['POST'])
    def save_config():
        """Speichert die Konfiguration"""
        try:
            # Prüfen, ob JSON-Daten empfangen wurden
            if not request.is_json:
                return jsonify({
                    "status": "error",
                    "message": "Keine JSON-Daten empfangen. Content-Type muss application/json sein."
                }), 400

            # JSON-Daten abrufen
            new_config = request.json

            if not new_config:
                return jsonify({
                    "status": "error",
                    "message": "Leere Konfigurationsdaten empfangen"
                }), 400

            # Konfigurationsdaten ausgeben für Debugging
            app.logger.debug(f"Empfangene Konfiguration: {new_config}")

            # Versuchen, die Konfiguration zu speichern
            try:
                # Konfiguration mit bestehender Konfiguration zusammenführen
                merged_config = {}

                # Erst die bestehende Konfiguration kopieren
                for key, value in config_manager.config.items():
                    merged_config[key] = value

                # Dann die neue Konfiguration einarbeiten (rekursiv)
                def recursive_update(target, source):
                    for key, value in source.items():
                        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                            recursive_update(target[key], value)
                        else:
                            target[key] = value

                recursive_update(merged_config, new_config)

                # Aktualisierte Konfiguration speichern
                config_manager.config = merged_config

                # In Datei speichern
                config_manager.save_config(merged_config)

                app.logger.debug(f"Konfiguration gespeichert in: {config_manager.config_path}")
                return jsonify({"status": "success"})
            except Exception as config_error:
                app.logger.error(f"Fehler beim Speichern der Konfiguration: {config_error}")
                return jsonify({
                    "status": "error",
                    "message": f"Fehler beim Speichern: {str(config_error)}"
                }), 500

        except Exception as e:
            app.logger.error(f"Allgemeiner Fehler beim Speichern der Konfiguration: {e}")
            return jsonify({
                "status": "error",
                "message": f"Allgemeiner Fehler: {str(e)}"
            }), 500
            
    @app.route('/generate_360', methods=['POST'])
    def generate_360():
        """Generiert einen 360°-Viewer aus den aufgenommenen Bildern."""
        try:
            # Liste der Fotos nach Zeitstempel sortieren
            photo_dir = os.path.join(app.static_folder, 'photos')
            photos = sorted([f for f in os.listdir(photo_dir)
                            if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

            if not photos:
                return jsonify({"error": "Keine Fotos gefunden"}), 400

            # Optionale Metadaten aus der Anfrage
            metadata = request.get_json() if request.is_json else {}

            # 360°-Viewer generieren
            viewer_url = viewer_generator.generate_viewer(photos, metadata)

            if viewer_url:
                return jsonify({"status": "success", "url": viewer_url})
            else:
                return jsonify({"error": "Fehler beim Generieren des Viewers"}), 500
        except Exception as e:
            app.logger.error(f"Fehler beim Generieren des 360°-Viewers: {e}")
            return jsonify({"error": str(e)}), 500
