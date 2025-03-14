#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/main/routes.py
Enthält die Hauptrouten der Anwendung
"""

import os
import time
import logging
from flask import render_template, request, send_from_directory, jsonify, current_app
from app.blueprints.main import main_bp
from app.utils.config_manager import config_manager
from app import arduino_controller, camera_controller, turntable_controller
from app.blueprints.main.utils import rotate_teller, take_photo

# Logger einrichten
logger = logging.getLogger(__name__)

@main_bp.route('/')
def index():
    """Hauptseite der Anwendung"""
    # Projekt-ID aus der Anfrage holen (falls vorhanden)
    project_id = request.args.get('project_id')
    project = None
    
    # Wenn eine Projekt-ID angegeben wurde, Projekt laden
    if project_id:
        from app.models.project import ProjectManager
        from app.utils.path_manager import PathManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        project = project_manager.get_project(project_id)
    
    return render_template('index.html', project=project)

@main_bp.route('/viewer')
def view_360():
    """Zeigt den 360°-Viewer an."""
    return render_template('viewer.html')

@main_bp.route('/rotate', methods=['POST'])
def rotate():
    """Dreht den Teller und nimmt ein Foto auf"""
    try:
        # Parameter validieren
        if 'degrees' not in request.form:
            return jsonify({"error": "Parameter 'degrees' fehlt"}), 400
            
        if 'project_id' not in request.form:
            return jsonify({"error": "Parameter 'project_id' fehlt"}), 400
            
        # Parameter extrahieren
        try:
            degrees = int(request.form['degrees'])
            if degrees <= 0 or degrees > 360:
                return jsonify({"error": "Ungültiger Drehwinkel. Muss zwischen 1 und 360 Grad liegen."}), 400
        except ValueError:
            return jsonify({"error": "Ungültiger Drehwinkel. Muss eine Zahl sein."}), 400
            
        project_id = request.form['project_id']
        
        # Projekt-ID validieren
        from app.utils.secure_path import validate_project_id
        if not validate_project_id(project_id):
            return jsonify({"error": "Ungültige Projekt-ID"}), 400
            
        # Projekt laden
        from app.models.project import ProjectManager
        from app.utils.path_manager import PathManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        project = project_manager.get_project(project_id)
        
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Drehteller rotieren
        rotate_teller(degrees)
        
        # Foto mit Zeitstempel aufnehmen
        timestamp = int(time.time())
        filename = f'photo_{timestamp}_{degrees}.jpg'
        photo_path = take_photo(project_id, filename)
        
        if not photo_path:
            return jsonify({"error": "Fehler beim Aufnehmen des Fotos"}), 500
            
        # Foto zum Projekt hinzufügen mit dem korrekten Winkel
        project.add_image(photo_path, angle=degrees, timestamp=timestamp)
        
        # Relativen Pfad für die Antwort erstellen
        from pathlib import Path
        rel_path = '/' + str(Path(photo_path).relative_to(path_manager.base_dir)).replace('\\', '/')
        
        return jsonify({
            "status": "success",
            "photo": rel_path,
            "angle": degrees  # Winkel in der Antwort zurückgeben
        })
    except Exception as e:
        logger.error(f"Fehler bei der Rotation/Fotoaufnahme: {str(e)}")
        return jsonify({"error": str(e)}), 500

@main_bp.route('/static/photos/<filename>')
def serve_photo(filename):
    """Liefert ein aufgenommenes Foto aus"""
    return send_from_directory('static/photos', filename)

@main_bp.route('/get_config')
def get_config():
    """Gibt die aktuelle Konfiguration zurück"""
    from app.utils.config_manager import config_manager
    return jsonify(config_manager.config)
