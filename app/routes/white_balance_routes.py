#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/routes/white_balance_routes.py
API-Endpunkte für die Weißabgleich-KI
"""

import os
import logging
import json
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app, send_from_directory
import werkzeug
from app.controllers.camera_controller import CameraController
from app.utils.white_balance_ai import WhiteBalanceAI
from app.models.project import Project
from app.utils.path_manager import PathManager

# Logger einrichten
logger = logging.getLogger(__name__)

# Blueprint für die Weißabgleich-API
white_balance_bp = Blueprint('white_balance', __name__)

# Verzeichnis für temporäre Bilder
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'temp')
os.makedirs(TEMP_DIR, exist_ok=True)

@white_balance_bp.route('/api/white_balance/settings', methods=['GET'])
def get_white_balance_settings():
    """Gibt die aktuellen Weißabgleich-Einstellungen zurück"""
    try:
        white_balance_ai = WhiteBalanceAI()
        
        # Lade Konfiguration
        config_path = white_balance_ai.config_path
        settings = {
            'reference_image': None,
            'reference_image_url': None,
            'enabled': False,
            'strength': 0.8
        }
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Füge gespeicherte Werte hinzu
                settings['enabled'] = config.get('enabled', False)
                settings['strength'] = config.get('strength', 0.8)
                
                if 'reference_image' in config:
                    ref_image = config.get('reference_image')
                    settings['reference_image'] = os.path.basename(ref_image) if ref_image else None
                    
                    # URL für die Vorschau des Referenzbildes
                    if ref_image and os.path.exists(ref_image):
                        temp_preview = os.path.join(TEMP_DIR, os.path.basename(ref_image))
                        if not os.path.exists(temp_preview):
                            # Kopiere das Bild in das temp-Verzeichnis für die Vorschau
                            import shutil
                            shutil.copy2(ref_image, temp_preview)
                        
                        settings['reference_image_url'] = f'/temp/{os.path.basename(ref_image)}'
        
        return jsonify(settings)
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Weißabgleich-Einstellungen: {str(e)}")
        return jsonify({'error': str(e)}), 500

@white_balance_bp.route('/api/white_balance/set_reference', methods=['POST'])
def set_reference_image():
    """Setzt ein hochgeladenes Bild als Referenz für den Weißabgleich"""
    try:
        if 'reference_image' not in request.files:
            return jsonify({'success': False, 'error': 'Kein Bild hochgeladen'}), 400
        
        file = request.files['reference_image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Kein Bild ausgewählt'}), 400
        
        # Sichere Dateiname
        filename = werkzeug.utils.secure_filename(file.filename)
        
        # Speicherpfad im Temp-Verzeichnis
        reference_path = os.path.join(TEMP_DIR, filename)
        
        # Speichern des Bildes
        file.save(reference_path)
        
        # Weißabgleich-Referenz setzen
        white_balance_ai = WhiteBalanceAI()
        success = white_balance_ai.set_reference_image(reference_path)
        
        if success:
            # Speichere den Pfad zum Referenzbild in der Konfiguration
            with open(white_balance_ai.config_path, 'r') as f:
                config = json.load(f)
            
            config['reference_image'] = reference_path
            
            with open(white_balance_ai.config_path, 'w') as f:
                json.dump(config, f)
            
            return jsonify({
                'success': True, 
                'message': 'Referenzbild erfolgreich gesetzt',
                'image_path': reference_path,
                'image_url': f'/temp/{filename}'
            })
        else:
            return jsonify({'success': False, 'error': 'Fehler beim Setzen des Referenzbildes'}), 500
    
    except Exception as e:
        logger.error(f"Fehler beim Setzen des Referenzbildes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@white_balance_bp.route('/api/white_balance/use_project_image/<project_id>', methods=['POST'])
def use_project_image(project_id):
    """Verwendet das erste Bild eines Projekts als Referenz für den Weißabgleich"""
    try:
        # Path Manager für Projektzugriff
        path_manager = PathManager()
        
        # Projektverzeichnis
        project_dir = path_manager.get_project_path(project_id)
        if not os.path.exists(project_dir):
            return jsonify({'success': False, 'error': 'Projektverzeichnis nicht gefunden'}), 404
        
        # Bilder-Verzeichnis
        images_dir = os.path.join(project_dir, 'images')
        if os.path.exists(images_dir) and os.path.isdir(images_dir):
            image_dir_to_search = images_dir
        else:
            image_dir_to_search = project_dir
        
        # Erstes Bild im Projektverzeichnis finden
        image_files = []
        for ext in ['jpg', 'jpeg', 'png']:
            image_files.extend(list(Path(image_dir_to_search).glob(f'*.{ext}')))
            image_files.extend(list(Path(image_dir_to_search).glob(f'*.{ext.upper()}')))
        
        if not image_files:
            return jsonify({'success': False, 'error': 'Keine Bilder im Projekt gefunden'}), 404
        
        # Bilder sortieren und erstes auswählen
        image_files.sort()
        reference_image = str(image_files[0])
        
        # Weißabgleich-Referenz setzen
        white_balance_ai = WhiteBalanceAI()
        success = white_balance_ai.set_reference_image(reference_image)
        
        if success:
            # Konfiguration laden oder erstellen
            config = {}
            if os.path.exists(white_balance_ai.config_path):
                with open(white_balance_ai.config_path, 'r') as f:
                    config = json.load(f)
            
            # Referenzbild-Pfad speichern
            config['reference_image'] = reference_image
            
            # Konfiguration speichern
            with open(white_balance_ai.config_path, 'w') as f:
                json.dump(config, f)
            
            # Kopiere das Bild ins Temp-Verzeichnis für die Vorschau
            temp_filename = os.path.basename(reference_image)
            temp_path = os.path.join(TEMP_DIR, temp_filename)
            
            import shutil
            shutil.copy2(reference_image, temp_path)
            
            return jsonify({
                'success': True, 
                'message': 'Referenzbild erfolgreich gesetzt',
                'image_name': os.path.basename(reference_image),
                'image_url': f'/temp/{temp_filename}'
            })
        else:
            return jsonify({'success': False, 'error': 'Fehler beim Setzen des Referenzbildes'}), 500
    
    except Exception as e:
        logger.error(f"Fehler beim Setzen des Referenzbildes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@white_balance_bp.route('/api/white_balance/correct_project/<project_id>', methods=['POST'])
def correct_project(project_id):
    """Wendet die Weißabgleichkorrektur auf alle Bilder eines Projekts an"""
    try:
        # Stärke der Korrektur aus dem Request lesen
        data = request.json or {}
        strength = float(data.get('strength', 0.8))
        
        # Path Manager für Projektzugriff
        path_manager = PathManager()
        
        # Projektverzeichnis
        project_dir = path_manager.get_project_path(project_id)
        if not os.path.exists(project_dir):
            return jsonify({'success': False, 'error': 'Projektverzeichnis nicht gefunden'}), 404
        
        # Bilder-Verzeichnis
        images_dir = os.path.join(project_dir, 'images')
        if not os.path.exists(images_dir):
            os.makedirs(images_dir)
        
        # Ausgabeordner erstellen (im Projektverzeichnis)
        output_dir = os.path.join(project_dir, 'corrected')
        os.makedirs(output_dir, exist_ok=True)
        
        # White Balance AI initialisieren
        white_balance_ai = WhiteBalanceAI()
        
        # Prüfen, ob ein Referenzbild gesetzt ist
        if not os.path.exists(white_balance_ai.config_path):
            return jsonify({'success': False, 'error': 'Keine Weißabgleich-Konfiguration gefunden'}), 400
        
        with open(white_balance_ai.config_path, 'r') as f:
            config = json.load(f)
        
        if 'reference_image' not in config or not config['reference_image'] or not os.path.exists(config['reference_image']):
            return jsonify({'success': False, 'error': 'Kein Referenzbild für Weißabgleich gesetzt'}), 400
        
        # Alle Bilder im Projektverzeichnis finden
        image_files = []
        for ext in ['jpg', 'jpeg', 'png']:
            image_files.extend(list(Path(images_dir).glob(f'*.{ext}')))
            image_files.extend(list(Path(images_dir).glob(f'*.{ext.upper()}')))
        
        if not image_files:
            return jsonify({'success': False, 'error': 'Keine Bilder im Projekt gefunden'}), 404
        
        # Korrekturmodell vorbereiten
        white_balance_ai.set_reference_image(config['reference_image'])
        
        # Bilder korrigieren
        processed_images = []
        
        for img_path in image_files:
            img_path_str = str(img_path)
            output_path = os.path.join(output_dir, os.path.basename(img_path_str))
            
            # Bild korrigieren
            success = white_balance_ai.correct_image(img_path_str, output_path, strength)
            
            if success:
                processed_images.append(os.path.basename(img_path_str))
        
        # Erfolgsmeldung zurückgeben
        return jsonify({
            'success': True,
            'message': f"{len(processed_images)} Bilder erfolgreich korrigiert",
            'processed_images': processed_images,
            'output_dir': output_dir
        })
    
    except Exception as e:
        logger.error(f"Fehler bei der Weißabgleichkorrektur: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@white_balance_bp.route('/temp/<filename>')
def serve_temp_file(filename):
    """Stellt temporäre Dateien (z.B. Bildvorschauen) zur Verfügung"""
    try:
        return send_from_directory(TEMP_DIR, filename)
    except Exception as e:
        logger.error(f"Fehler beim Bereitstellen der temporären Datei: {str(e)}")
        return jsonify({'error': str(e)}), 404

@white_balance_bp.route('/api/white_balance/save_settings', methods=['POST'])
def save_white_balance_settings():
    """Speichert die Weißabgleich-Einstellungen"""
    try:
        data = request.json
        
        enabled = data.get('enabled', False)
        strength = float(data.get('strength', 0.8))
        
        # White Balance AI initialisieren
        white_balance_ai = WhiteBalanceAI()
        
        # Konfiguration laden oder erstellen
        config = {}
        if os.path.exists(white_balance_ai.config_path):
            with open(white_balance_ai.config_path, 'r') as f:
                config = json.load(f)
        
        # Einstellungen aktualisieren
        config['enabled'] = enabled
        config['strength'] = strength
        
        # Konfiguration speichern
        with open(white_balance_ai.config_path, 'w') as f:
            json.dump(config, f)
        
        return jsonify({
            'success': True,
            'message': 'Weißabgleich-Einstellungen erfolgreich gespeichert'
        })
    
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Weißabgleich-Einstellungen: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
