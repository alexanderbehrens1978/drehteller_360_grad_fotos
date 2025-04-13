# app/blueprints/settings/routes.py
import json
import logging
from flask import render_template, request, jsonify, redirect, url_for
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
        logger.debug(f"Empfangene Konfiguration: {json.dumps(new_config, indent=2)}")
        
        # Rekursive Aktualisierung der Konfiguration
        def recursive_update(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    recursive_update(target[key], value)
                else:
                    target[key] = value
        
        # Kopie der aktuellen Konfiguration erstellen
        merged_config = config_manager.config.copy()
        
        # Neue Konfiguration rekursiv zusammenführen
        recursive_update(merged_config, new_config)
        
        # Versuchen, die Konfiguration zu speichern
        config_save_success = config_manager.save_config(merged_config)
        
        if config_save_success:
            logger.info(f"Konfiguration erfolgreich gespeichert: {config_manager.config_path}")
            return jsonify({
                "status": "success", 
                "message": "Konfiguration erfolgreich gespeichert",
                "config": merged_config
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Fehler beim Speichern der Konfiguration"
            }), 500
            
    except Exception as e:
        logger.error(f"Allgemeiner Fehler beim Speichern der Konfiguration: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Allgemeiner Fehler: {str(e)}"
        }), 500

@settings_bp.route('/calibrate_hall_sensor', methods=['POST'])
def calibrate_hall_sensor():
    """Kalibriert den Drehteller mit dem Hall-Sensor"""
    try:
        # Prüfen, ob JSON-Daten empfangen wurden
        if not request.is_json:
            return jsonify({
                "status": "error", 
                "message": "Keine JSON-Daten empfangen. Content-Type muss application/json sein."
            }), 400
        
        # JSON-Daten abrufen
        hall_data = request.json
        
        logger.debug(f"Empfangene Hall-Sensor-Konfiguration: {json.dumps(hall_data, indent=2)}")
        
        # Hall-Sensor-Port und Schwellenwert extrahieren
        hall_port = hall_data.get('hall_sensor', {}).get('port', '/dev/ttyACM1')
        hall_threshold = hall_data.get('hall_sensor', {}).get('threshold', 30)
        motor_port = config_manager.config.get('arduino', {}).get('port', '/dev/ttyACM0')
        
        # Aktuelle Konfiguration aktualisieren
        config = config_manager.config.copy()
        if 'hall_sensor' not in config:
            config['hall_sensor'] = {}
        
        config['hall_sensor']['port'] = hall_port
        config['hall_sensor']['threshold'] = hall_threshold
        config_manager.save_config(config)
        
        # Hall-Motor-Controller importieren und initialisieren
        from drehteller360.hall_motor_controller import HallMotorController
        
        try:
            logger.info(f"Initialisiere Hall-Motor-Controller für Kalibrierung. Hall-Port: {hall_port}, Motor-Port: {motor_port}")
            hall_controller = HallMotorController(
                hall_port=hall_port,
                motor_port=motor_port,
                threshold=hall_threshold
            )
            
            # Zuerst zur Heimposition fahren, dann Rotationszeit kalibrieren
            logger.info("Fahre zur Heimposition und kalibriere die Rotationszeit...")
            
            # Zur Heimposition fahren
            home_success = hall_controller.move_to_home_position()
            if not home_success:
                logger.error("Fehler beim Fahren zur Heimposition")
                return jsonify({
                    "status": "error",
                    "message": "Fehler beim Fahren zur Heimposition. Kein Hall-Sensor-Signal gefunden."
                }), 500
            
            # Rotationszeit kalibrieren
            rotation_time_ms = hall_controller.calibrate_rotation_time()
            
            if rotation_time_ms:
                logger.info(f"Kalibrierung erfolgreich: Eine volle Umdrehung dauert {rotation_time_ms}ms")
                return jsonify({
                    "status": "success",
                    "message": f"Drehteller wurde erfolgreich kalibriert. Eine vollständige Umdrehung dauert {rotation_time_ms/1000:.1f} Sekunden.",
                    "rotation_time_ms": rotation_time_ms
                })
            else:
                logger.error("Fehler bei der Kalibrierung der Rotationszeit")
                return jsonify({
                    "status": "error",
                    "message": "Fehler bei der Kalibrierung: Konnte die Rotationszeit nicht messen."
                }), 500
                
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung oder Kalibrierung des Hall-Motor-Controllers: {e}")
            return jsonify({
                "status": "error",
                "message": f"Hardware-Fehler bei der Kalibrierung: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"Allgemeiner Fehler bei der Hall-Sensor-Kalibrierung: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Allgemeiner Fehler: {str(e)}"
        }), 500
