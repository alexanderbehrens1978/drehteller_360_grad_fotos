#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/api/routes.py
Enthält die API-Endpunkte der Anwendung
"""

import os
import json
import time
import logging
from flask import request, jsonify, current_app, abort
from app.blueprints.api import api_bp
from app.utils.config_manager import config_manager
from app import arduino_controller, camera_controller, turntable_controller
from app.utils.device_detector import device_detector
from app.utils.webcam_detection_helper import get_camera_capabilities
from app.utils.viewer_generator import viewer_generator
from app.utils.secure_path import secure_filename, secure_join, validate_project_id

# Logger einrichten
logger = logging.getLogger(__name__)

@api_bp.route('/project/<project_id>')
def get_project(project_id):
    """
    Liefert Projektdaten für den 360°-Viewer
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt-ID validieren
        if not validate_project_id(project_id):
            logger.warning(f"Versuch, auf ungültige Projekt-ID zuzugreifen: {project_id}")
            return jsonify({"error": "Ungültige Projekt-ID"}), 400
            
        # Pfadmanager und Projektmanager verwenden
        from app.utils.path_manager import PathManager
        from app.models.project import ProjectManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        
        # Projekt laden
        project = project_manager.get_project(project_id)
        
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Projekt als JSON zurückgeben
        return jsonify(project.to_dict())
    except Exception as e:
        logger.error(f"Fehler beim Laden der Projektdaten: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/projects')
def get_projects():
    """Liefert eine Liste aller verfügbaren Projekte"""
    try:
        static_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'static'))
        projects_dir = os.path.join(static_dir, 'projects')
        projects = []
        
        # Verzeichnisse durchsuchen
        for project_id in os.listdir(projects_dir):
            project_path = secure_join(projects_dir, project_id)
            
            # Nur Verzeichnisse berücksichtigen
            if os.path.isdir(project_path):
                metadata_path = secure_join(project_path, 'metadata.json')
                
                # Prüfen, ob Metadaten existieren
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        
                    # Projekt-ID hinzufügen
                    metadata['id'] = project_id
                    projects.append(metadata)
                else:
                    # Fallback, wenn keine Metadaten existieren
                    images = [f for f in os.listdir(project_path) 
                             if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    projects.append({
                        'id': project_id,
                        'name': f"Projekt {project_id}",
                        'created': os.path.getctime(project_path),
                        'images': images,
                        'image_count': len(images)
                    })
        
        return jsonify(projects)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Projekte: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/project/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Löscht ein Projekt
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt-ID validieren
        if not validate_project_id(project_id):
            logger.warning(f"Versuch, ungültige Projekt-ID zu löschen: {project_id}")
            return jsonify({"error": "Ungültige Projekt-ID"}), 400
            
        # Projektmanager verwenden
        from app.utils.path_manager import PathManager
        from app.models.project import ProjectManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        
        # Projekt löschen
        success = project_manager.delete_project(project_id)
        
        if not success:
            return jsonify({"error": "Projekt konnte nicht gelöscht werden"}), 500
        
        logger.info(f"Projekt {project_id} wurde gelöscht")
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Projekts: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/devices')
def get_devices():
    """Liefert eine Liste aller erkannten Geräte."""
    try:
        devices = device_detector.get_devices()
        logger.debug(f"Erkannte Geräte: {devices}")
        return jsonify(devices)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Geräte: {e}")
        return jsonify({"error": "Fehler beim Abrufen der Geräte", "message": str(e)}), 500

@api_bp.route('/status/arduino')
def api_arduino_status():
    """API-Endpunkt zum Abrufen des Arduino-Status"""
    global arduino_controller
    
    connected = False
    port = config_manager.get('arduino.port')
    baudrate = config_manager.get('arduino.baudrate', 9600)
    
    if arduino_controller:
        connected = arduino_controller.is_connected()
    
    return jsonify({
        'connected': connected,
        'port': port,
        'baudrate': baudrate
    })

@api_bp.route('/status/camera')
def api_camera_status():
    """API-Endpunkt zum Abrufen des Kamera-Status"""
    camera_type = config_manager.get('camera.type', 'webcam')
    camera_device = config_manager.get('camera.device_path', '/dev/video0')
    resolution = config_manager.get('camera.resolution', {})
    
    # Test, ob die Kamera verfügbar ist
    available = False
    
    if camera_controller:
        try:
            static_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'static'))
            temp_dir = os.path.join(static_dir, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            test_image_path = os.path.join(temp_dir, 'camera_test.jpg')
            available = camera_controller.capture_photo(test_image_path)
        except Exception as e:
            logger.error(f"Fehler beim Testen der Kamera: {e}")
    
    return jsonify({
        'available': available,
        'type': camera_type,
        'device': camera_device,
        'resolution': resolution
    })

@api_bp.route('/test/camera', methods=['POST'])
def test_camera():
    """
    Testet eine Kamera mit den angegebenen Einstellungen
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"status": "error", "message": "Keine Daten empfangen"}), 400
            
        camera_type = data.get('type', 'webcam')
        device = data.get('device')
        resolution = data.get('resolution')
        profile = data.get('profile')
        
        if not device:
            return jsonify({"status": "error", "message": "Kein Gerät angegeben"}), 400
            
        # Auflösung verarbeiten
        if isinstance(resolution, str) and 'x' in resolution:
            width, height = map(int, resolution.split('x'))
            resolution = (width, height)
        
        # Kameraprofil laden, falls angegeben
        camera_settings = {}
        if camera_type == 'gphoto2' and profile:
            profiles = config_manager.get('camera.gphoto2_profiles', {})
            if profile in profiles:
                camera_settings = profiles[profile].get('settings', {})
        
        # Temporären Ordner für das Testfoto erstellen
        static_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'static'))
        temp_dir = os.path.join(static_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Dateiname für das Testfoto
        timestamp = int(time.time())
        filename = f'camera_test_{timestamp}.jpg'
        photo_path = os.path.join(temp_dir, filename)
        
        # Kamera initialisieren und Testfoto aufnehmen
        from app.controllers.camera_controller import CameraController
        camera = CameraController(camera_type, device, resolution, camera_settings)
        
        success = camera.capture_photo(photo_path)
        
        if success:
            # Bildpfad für die Antwort
            image_url = f'/static/temp/{filename}'
            
            return jsonify({
                "status": "success",
                "message": "Testfoto erfolgreich aufgenommen",
                "image_url": image_url
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Konnte kein Foto aufnehmen. Überprüfen Sie die Kameraverbindung und -einstellungen."
            }), 500
    except Exception as e:
        logger.error(f"Fehler beim Kameratest: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/camera_capabilities')
def camera_capabilities():
    """Gibt die Fähigkeiten der Kamera zurück"""
    try:
        # Parameter abrufen
        device = request.args.get('device')
        camera_type = request.args.get('type', 'webcam')
        
        if not device:
            return jsonify({
                "status": "error", 
                "message": "Kein Gerät angegeben"
            }), 400
            
        # Kamera-Controller verwenden, um Fähigkeiten abzurufen
        from app.controllers.camera_controller import CameraController
        camera = CameraController(camera_type, device)
        
        capabilities = camera.get_camera_capabilities(device, camera_type)
        
        return jsonify({
            "status": "success",
            "capabilities": capabilities
        })
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Kamera-Fähigkeiten: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Fehler beim Abrufen der Kamera-Fähigkeiten: {str(e)}"
        }), 500

@api_bp.route('/cameras/detect', methods=['GET'])
def detect_cameras():
    """
    Erkennt verfügbare Kameras (Webcams und DSLR)
    """
    try:
        from app.controllers.camera_controller import CameraController
        
        # CameraController-Instanz erstellen
        camera_controller = CameraController()
        
        # Kameras erkennen
        cameras = camera_controller.detect_cameras()
        
        return jsonify({
            "status": "success",
            "cameras": cameras
        })
    except Exception as e:
        logger.error(f"Fehler bei der Kameraerkennung: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Fehler bei der Kameraerkennung: {str(e)}"
        }), 500

@api_bp.route('/project/<project_id>/start_session', methods=['POST'])
def start_project_session(project_id):
    """
    Startet eine neue Fotosession für ein Projekt
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt-ID validieren
        if not validate_project_id(project_id):
            logger.warning(f"Versuch, eine Session für ungültige Projekt-ID zu starten: {project_id}")
            return jsonify({"error": "Ungültige Projekt-ID"}), 400
            
        # Projektmanager verwenden
        from app.utils.path_manager import PathManager
        from app.models.project import ProjectManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        
        # Projekt laden
        project = project_manager.get_project(project_id)
        
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Neue Session starten
        session_id = project.start_session()
        
        logger.info(f"Neue Session für Projekt {project_id} gestartet: {session_id}")
        return jsonify({"status": "success", "session_id": session_id})
    except Exception as e:
        logger.error(f"Fehler beim Starten der Session: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/project/<project_id>/end_session', methods=['POST'])
def end_project_session(project_id):
    """
    Beendet die aktive Fotosession eines Projekts
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt-ID validieren
        if not validate_project_id(project_id):
            logger.warning(f"Versuch, eine Session für ungültige Projekt-ID zu beenden: {project_id}")
            return jsonify({"error": "Ungültige Projekt-ID"}), 400
            
        # Projektmanager verwenden
        from app.utils.path_manager import PathManager
        from app.models.project import ProjectManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        
        # Projekt laden
        project = project_manager.get_project(project_id)
        
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Session beenden
        project.end_session()
        
        logger.info(f"Session für Projekt {project_id} beendet")
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Fehler beim Beenden der Session: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/project/<project_id>/update_position', methods=['POST'])
def update_project_position(project_id):
    """
    Aktualisiert die Position des Drehtellers für ein Projekt
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Daten validieren
        if not request.is_json:
            return jsonify({"error": "Keine JSON-Daten empfangen"}), 400
            
        data = request.json
        if 'position' not in data:
            return jsonify({"error": "Position nicht angegeben"}), 400
            
        try:
            position = int(data['position'])
            if position < 0 or position > 360:
                return jsonify({"error": "Position muss zwischen 0 und 360 Grad liegen"}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Position muss eine ganze Zahl sein"}), 400
            
        # Projekt-ID validieren
        if not validate_project_id(project_id):
            logger.warning(f"Versuch, Position für ungültige Projekt-ID zu aktualisieren: {project_id}")
            return jsonify({"error": "Ungültige Projekt-ID"}), 400
            
        # Projektmanager verwenden
        from app.utils.path_manager import PathManager
        from app.models.project import ProjectManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        
        # Projekt laden
        project = project_manager.get_project(project_id)
        
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Position aktualisieren
        project.update_position(position)
        
        logger.info(f"Position für Projekt {project_id} aktualisiert: {position}°")
        return jsonify({"status": "success", "position": position})
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Position: {e}")
        return jsonify({"error": str(e)}), 500
