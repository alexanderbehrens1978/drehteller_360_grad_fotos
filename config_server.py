#!/usr/bin/env python3
"""
Eigenständiger Konfigurationsserver für das 360° Drehteller-System

Dieses Skript startet einen eigenständigen Flask-Server, der die fehlenden
/get_config und /save_config Endpunkte bereitstellt. Außerdem dient er als
Proxy für den Hauptserver.

Starte diesen Server mit einem anderen Port (z.B. 5001) als den Hauptserver.
"""

import os
import json
import sys
import logging
from flask import Flask, jsonify, request, redirect
from flask_cors import CORS

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("config_server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("config_server")

# Konfigurationsdatei-Pfad
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
MAIN_SERVER = 'http://192.168.188.105:5000'  # Der Hauptserver-URL

# Flask-App erstellen
app = Flask(__name__)
CORS(app)  # CORS aktivieren, um Anfragen von anderen Ursprüngen zu erlauben

def load_config():
    """Lädt die Konfiguration aus der Datei"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                return config
        else:
            # Standard-Konfiguration
            default_config = {
                'camera': {
                    'device_path': '/dev/video0',
                    'type': 'webcam',
                    'resolution': {
                        'width': 1280,
                        'height': 720
                    }
                },
                'arduino': {
                    'port': '/dev/ttyACM0',
                    'baudrate': 9600
                },
                'rotation': {
                    'default_degrees': 15,
                    'default_interval': 5
                },
                'simulator': {
                    'enabled': True
                }
            }
            
            # Speichere die Standard-Konfiguration
            with open(CONFIG_PATH, 'w') as f:
                json.dump(default_config, f, indent=4)
            
            return default_config
    except Exception as e:
        logger.error(f"Fehler beim Laden der Konfiguration: {e}")
        return {}

def save_config(config):
    """Speichert die Konfiguration in der Datei"""
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
        return False

# Die fehlenden Routen implementieren
@app.route('/get_config')
def get_config():
    """
    Retrieve current configuration
    """
    config = load_config()
    return jsonify(config)

@app.route('/save_config', methods=['POST'])
def save_config_route():
    """
    Save new configuration
    """
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
        logger.info(f"Empfangene Konfiguration: {json.dumps(new_config, indent=2)}")
        
        # Bestehende Konfiguration laden
        current_config = load_config()
        
        # Konfiguration zusammenführen
        def recursive_update(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    recursive_update(target[key], value)
                else:
                    target[key] = value
        
        recursive_update(current_config, new_config)
        
        # Aktualisierte Konfiguration speichern
        success = save_config(current_config)
        
        if success:
            logger.info(f"Konfiguration gespeichert in: {CONFIG_PATH}")
            return jsonify({"status": "success"})
        else:
            return jsonify({
                "status": "error", 
                "message": "Fehler beim Speichern der Konfiguration"
            }), 500
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Konfiguration: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Fehler beim Speichern: {str(e)}"
        }), 500

# Proxy für alle anderen Anfragen
@app.route('/<path:path>')
def proxy(path):
    """Leitet alle anderen Anfragen an den Hauptserver weiter"""
    return redirect(f"{MAIN_SERVER}/{path}")

@app.route('/')
def index():
    """Startseite, leitet zum Hauptserver weiter"""
    return redirect(MAIN_SERVER)

if __name__ == '__main__':
    # Server starten
    port = 5001  # Anderer Port als der Hauptserver
    logger.info(f"Starte Konfigurationsserver auf Port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True)
