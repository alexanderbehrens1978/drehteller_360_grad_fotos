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
    degrees = int(request.form['degrees'])
    interval = float(request.form.get('interval', 5))  # Default 5 Sekunden, falls nicht angegeben
    
    # Drehteller rotieren
    rotate_teller(degrees)
    
    # Foto mit Zeitstempel aufnehmen
    filename = f'photo_{int(time.time())}_{degrees}.jpg'
    photo_path = take_photo(filename)
    
    # Foto-Pfad relativ zu /static zurückgeben
    if photo_path:
        return f'/static/photos/{os.path.basename(photo_path)}'
    else:
        return 'Error capturing photo', 500

@main_bp.route('/static/photos/<filename>')
def serve_photo(filename):
    """Liefert ein aufgenommenes Foto aus"""
    return send_from_directory('static/photos', filename)

@main_bp.route('/get_config')
def get_config():
    """Gibt die aktuelle Konfiguration zurück"""
    from app.utils.config_manager import config_manager
    return jsonify(config_manager.config)
