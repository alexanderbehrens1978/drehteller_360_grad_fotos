#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/api/routes.py
Enthält die API-Endpunkte der Anwendung
"""

import os
import json
import logging
from flask import request, jsonify, current_app
from app.blueprints.api import api_bp
from app.utils.config_manager import config_manager
from app import arduino_controller, camera_controller, turntable_controller
from app.utils.device_detector import device_detector
from app.utils.webcam_detection_helper import get_camera_capabilities
from app.utils.viewer_generator import viewer_generator

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
        project_dir = os.path.join('static/projects', project_id)
        metadata_path = os.path.join(project_dir, 'metadata.json')
        
        if not os.path.exists(metadata_path):
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return jsonify(metadata)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Projektdaten: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/projects')
def get_projects():
    """Liefert eine Liste aller verfügbaren Projekte"""
    try:
        projects_dir = 'static/projects'
        projects = []
        
        # Verzeichnisse durchsuchen
        for project_id in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_id)
            
            # Nur Verzeichnisse berücksichtigen
            if os.path.isdir(project_path):
                metadata_path = os.path.join(project_path, 'metadata.json')
                
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
        project_dir = os.path.join('static/projects', project_id)
        
        if not os.path.exists(project_dir):
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        import shutil
        shutil.rmtree(project_dir)
        
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Projekts: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/devices')
def get_devices():
    """Liefert eine Liste aller erkannten Geräte"""
    return jsonify(device_detector.get_devices())

@api_bp.route('/generate_360', methods=['POST'])
def generate_360():
    """Generiert einen 360°-Viewer aus den aufgenommenen Bildern"""
    try:
        # Liste der Fotos nach Zeitstempel sortieren
        photo_dir = 'static/photos'
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
        logger.error(f"Fehler beim Generieren des 360°-Viewers: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route('/camera_capabilities', methods=['GET'])
def camera_capabilities():
    """Gibt die Fähigkeiten der Kamera zurück"""
    try:
        # Kamera-Gerät aus der Konfiguration holen
        camera_device = config_manager.get('camera.device_path', '/dev/video0')
        
        # Kamera-Fähigkeiten abrufen
        capabilities = get_camera_capabilities(camera_device)
        
        return jsonify({
            "status": "success",
            "capabilities": capabilities
        })
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Kamera-Fähigkeiten: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

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
            test_image_path = os.path.join('static/temp', 'camera_test.jpg')
            os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
            
            available = camera_controller.capture_photo(test_image_path)
        except Exception as e:
            logger.error(f"Fehler beim Testen der Kamera: {e}")
    
    return jsonify({
        'available': available,
        'type': camera_type,
        'device': camera_device,
        'resolution': resolution
    })
