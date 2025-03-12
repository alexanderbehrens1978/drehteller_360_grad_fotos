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
    return render_template('index.html')

@main_bp.route('/viewer')
def view_360():
    """Zeigt den 360°-Viewer an."""
    return render_template('viewer.html')

@main_bp.route('/rotate', methods=['POST'])
def rotate():
    """Dreht den Teller und nimmt ein Foto auf"""
    try:
        # Parameter aus der Anfrage holen
        degrees = int(request.form['degrees'])
        project_id = request.form.get('project_id')
        
        # Validiere Projekt-ID
        if not project_id:
            return jsonify({"error": "Keine Projekt-ID angegeben"}), 400
            
        from app.utils.secure_path import validate_project_id
        if not validate_project_id(project_id):
            return jsonify({"error": "Ungültige Projekt-ID"}), 400
        
        # Drehteller rotieren
        rotate_teller(degrees)
        
        # Foto mit Zeitstempel aufnehmen und im Projektordner speichern
        timestamp = int(time.time())
        filename = f'photo_{timestamp}_{degrees}.jpg'
        photo_path = take_photo(project_id, filename)
        
        if not photo_path or not os.path.exists(photo_path):
            return jsonify({"error": "Fehler beim Aufnehmen des Fotos"}), 500
            
        # Relativen Pfad zum Foto zurückgeben
        rel_path = os.path.relpath(photo_path, os.path.join(current_app.root_path, '..'))
        rel_path = '/' + rel_path.replace('\\', '/')
        
        logger.info(f"Foto erfolgreich aufgenommen: {rel_path}")
        
        return jsonify({
            "status": "success", 
            "photo": rel_path,
            "angle": degrees
        })
    except Exception as e:
        logger.error(f"Fehler bei der Rotation oder Fotoaufnahme: {e}")
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
