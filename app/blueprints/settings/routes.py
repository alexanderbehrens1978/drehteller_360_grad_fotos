#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/settings/routes.py
Enthält die Routen für die Einstellungsseite
"""

import json
import logging
from flask import render_template, request, jsonify
from app.blueprints.settings import settings_bp
from app.utils.config_manager import config_manager

# Logger einrichten
logger = logging.getLogger(__name__)

@settings_bp.route('/')
def settings():
    """Zeigt die Einstellungsseite an"""
    return render_template('settings.html')

@settings_bp.route('/get_config')
def get_config():
    """Gibt die aktuelle Konfiguration zurück"""
    return jsonify(config_manager.config)

@settings_bp.route('/save_config', methods=['POST'])
def save_config():
    """Speichert die Konfiguration"""
    try:
        # Prüfen, ob JSON-Daten empfangen wurden
        if not request.is_json:
            logger.error("Keine JSON-Daten empfangen. Content-Type ist: %s", request.content_type)
            return jsonify({
                "status": "error", 
                "message": "Keine JSON-Daten empfangen. Content-Type muss application/json sein."
            }), 400
        
        # JSON-Daten abrufen
        new_config = request.json
        
        if not new_config:
            logger.error("Leere Konfigurationsdaten empfangen")
            return jsonify({
                "status": "error", 
                "message": "Leere Konfigurationsdaten empfangen"
            }), 400
        
        # Konfigurationsdaten ausgeben für Debugging
        logger.debug("Empfangene Konfiguration: %s", json.dumps(new_config, indent=2))
        
        # Kopie der aktuellen Konfiguration erstellen
        merged_config = config_manager.config.copy()
        
        # Neue Konfiguration rekursiv zusammenführen 
        def recursive_update(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    recursive_update(target[key], value)
                else:
                    target[key] = value
        
        recursive_update(merged_config, new_config)
        
        # Versuchen, die Konfiguration zu speichern
        config_save_success = config_manager.save_config(merged_config)
        
        if config_save_success:
            logger.info("Konfiguration erfolgreich gespeichert: %s", config_manager.config_path)
            return jsonify({
                "status": "success", 
                "message": "Konfiguration erfolgreich gespeichert"
            })
        else:
            logger.error("Fehler beim Speichern der Konfiguration")
            return jsonify({
                "status": "error", 
                "message": "Fehler beim Speichern der Konfiguration"
            }), 500
            
    except Exception as e:
        logger.error("Allgemeiner Fehler beim Speichern der Konfiguration: %s", str(e))
        return jsonify({
            "status": "error", 
            "message": f"Allgemeiner Fehler: {str(e)}"
        }), 500
