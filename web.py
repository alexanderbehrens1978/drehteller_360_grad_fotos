#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web.py
Hauptdatei für die Webserver-Anwendung
"""

from flask import Flask, render_template, request, send_from_directory, jsonify, abort
import os
import json
import time
import string
import serial
import logging
import subprocess

# Logger einrichten
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Import config manager
from config_manager import config_manager

# Import device detector and viewer generator
from device_detector import device_detector
from viewer_generator import viewer_generator

# Sicherheitsfunktionen
def secure_filename(filename):
    """Bereinigt einen Dateinamen und entfernt potenziell gefährliche Zeichen."""
    if not filename:
        return ""
        
    # Extrahiere nur den Dateinamen ohne Pfad
    filename = os.path.basename(filename)
    
    # Erlaube alphanumerische Zeichen und bestimmte Sonderzeichen
    allowed_chars = set(string.ascii_letters + string.digits + '-_.')
    filename = ''.join(c for c in filename if c in allowed_chars)
    
    # Stellen Sie sicher, dass der Dateiname nicht leer ist
    if not filename:
        logger.warning("Dateiname wurde zu einer leeren Zeichenfolge bereinigt")
        return "unnamed_file"
        
    return filename

def secure_join(base_path, *paths):
    """Verbindet Pfadsegmente sicher und verhindert Verzeichnistraversierungsangriffe."""
    # Stelle sicher, dass der Basispfad ein absoluter Pfad ist
    base_path = os.path.abspath(base_path)
    
    # Normalisiere alle Pfadsegmente und entferne potenziell gefährliche Teile
    clean_paths = []
    for i, path in enumerate(paths):
        if i == len(paths) - 1 and path:  # Letztes Element könnte ein Dateiname sein
            clean_paths.append(secure_filename(path))
        else:
            # Normalisiere Pfade und entferne '..' und Anführungszeichen
            if path:
                normalized = os.path.normpath(path).replace('..', '').replace('"', '').replace("'", "")
                clean_paths.append(normalized)
    
    # Verbinde den Basispfad mit den bereinigten Pfadsegmenten
    joined_path = os.path.join(base_path, *clean_paths)
    safe_path = os.path.abspath(joined_path)
    
    # Überprüfe, ob der resultierende Pfad innerhalb des Basispfads liegt
    if not safe_path.startswith(base_path):
        logger.warning(f"Versuchter Pfad-Traversal-Angriff verhindert: {joined_path}")
        return base_path
    
    return safe_path

def validate_project_id(project_id):
    """Validiert eine Projekt-ID gegen Traversierungsangriffe."""
    if not project_id or not isinstance(project_id, str):
        return False
        
    # Entferne Leerzeichen am Anfang/Ende
    project_id = project_id.strip()
    
    # Überprüfe auf unerlaubte Zeichen oder Sequenzen
    invalid_sequences = ['..', '/', '\\', '~', '$', '&', '*', '(', ')', '`', "'", '"', '|', '<', '>', ';']
    for seq in invalid_sequences:
        if seq in project_id:
            return False
            
    return len(project_id) > 0

app = Flask(__name__)

# Sicherheits-Header hinzufügen
@app.after_request
def add_security_headers(response):
    """Fügt Sicherheits-Header zu allen Antworten hinzu"""
    # Schutz vor Clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # Aktivieren der XSS-Filterung im Browser
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Verhindern von MIME-Typ-Sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Content-Security-Policy - weniger restriktiv für Entwicklung
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )
    return response

# Arduino connection
def get_arduino_connection():
    """Establish Arduino connection based on configuration"""
    try:
        port = config_manager.get('arduino.port', '/dev/ttyACM0')
        baudrate = config_manager.get('arduino.baudrate', 9600)

        arduino = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for initialization
        return arduino
    except Exception as e:
        logger.error(f"Arduino connection error: {e}")
        return None

# Global Arduino connection
arduino = get_arduino_connection()

def rotate_teller(degrees):
    """Rotate the platform"""
    if arduino is None:
        logger.warning("Arduino not connected!")
        return

    try:
        # Validiere den Drehwinkel
        degrees = float(degrees)
        if degrees <= 0 or degrees > 360:
            logger.warning(f"Ungültiger Drehwinkel: {degrees}")
            return
            
        # Berechnung der Drehzeit basierend auf der Gradzahl (0,8 Grad pro Sekunde)
        rotation_time = degrees / 0.8

        # Relais einschalten (Drehteller starten)
        arduino.write(b'1')  # '1' senden, um das Relais einzuschalten
        time.sleep(rotation_time)  # Warte für die berechnete Zeit
        arduino.write(b'0')  # '0' senden, um das Relais auszuschalten
        logger.info(f"Drehteller um {degrees} Grad gedreht.")
    except ValueError:
        logger.error(f"Ungültiger Drehwinkel-Wert: {degrees}")
    except Exception as e:
        logger.error(f"Fehler beim Drehen des Tellers: {e}")

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/viewer')
def view_360():
    """Zeigt den 360°-Viewer an."""
    return render_template('viewer.html')

@app.route('/projects')
def projects_page():
    """Zeigt die Projektverwaltungsseite an."""
    return render_template('projects.html')

@app.route('/get_config')
def get_config():
    """Retrieve current configuration"""
    return jsonify(config_manager.config)

@app.route('/save_config', methods=['POST'])
def save_config():
    """Save new configuration"""
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
        logger.debug("Empfangene Konfiguration: %s", json.dumps(new_config, indent=2))

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
            with open(config_manager.config_path, 'w') as f:
                json.dump(merged_config, f, indent=4)

            logger.info(f"Konfiguration gespeichert in: {config_manager.config_path}")
            return jsonify({"status": "success"})
        except Exception as config_error:
            logger.error(f"Fehler beim Speichern der Konfiguration: {config_error}")
            return jsonify({
                "status": "error",
                "message": f"Fehler beim Speichern: {str(config_error)}"
            }), 500

    except Exception as e:
        logger.error(f"Allgemeiner Fehler beim Speichern der Konfiguration: {e}")
        return jsonify({
            "status": "error",
            "message": f"Allgemeiner Fehler: {str(e)}"
        }), 500

@app.route('/api/project/<project_id>')
def get_project(project_id):
    """Liefert Projektdaten für den 360°-Viewer."""
    try:
        # Projekt-ID validieren
        if not validate_project_id(project_id):
            logger.warning(f"Versuch, auf ungültige Projekt-ID zuzugreifen: {project_id}")
            return jsonify({"error": "Ungültige Projekt-ID"}), 400
            
        # Sicheren Pfad erstellen
        projects_dir = os.path.abspath('static/projects')
        project_dir = secure_join(projects_dir, project_id)
        metadata_path = secure_join(project_dir, 'metadata.json')

        if not os.path.exists(metadata_path):
            return jsonify({"error": "Projekt nicht gefunden"}), 404

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        return jsonify(metadata)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Projektdaten: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects')
def get_projects():
    """Liefert eine Liste aller verfügbaren Projekte."""
    try:
        projects_dir = os.path.abspath('static/projects')
        projects = []

        # Verzeichnisse durchsuchen
        for project_id in os.listdir(projects_dir):
            # Sicheren Pfad erstellen
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

@app.route('/api/project/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Löscht ein Projekt und alle zugehörigen Bilder."""
    try:
        # Projekt-ID validieren
        if not validate_project_id(project_id):
            logger.warning(f"Versuch, ungültige Projekt-ID zu löschen: {project_id}")
            return jsonify({"error": "Ungültige Projekt-ID"}), 400
            
        # Sicheren Pfad erstellen
        projects_dir = os.path.abspath('static/projects')
        project_dir = secure_join(projects_dir, project_id)
        
        if not os.path.exists(project_dir):
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Metadaten lesen, um Bildinformationen zu erhalten
        metadata_path = secure_join(project_dir, 'metadata.json')
        images_to_delete = []
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Unterverzeichnisse wie sessions/sessions_id/images prüfen
                if 'sessions' in metadata:
                    for session in metadata.get('sessions', []):
                        session_photos = session.get('photos', {})
                        for photo_path in session_photos.values():
                            # Sicherstellen, dass der Pfad innerhalb des Projektverzeichnisses liegt
                            if isinstance(photo_path, str) and os.path.exists(photo_path) and os.path.isfile(photo_path):
                                abs_photo_path = os.path.abspath(photo_path)
                                if abs_photo_path.startswith(project_dir):
                                    images_to_delete.append(abs_photo_path)
            except Exception as metadata_error:
                logger.warning(f"Warnung: Konnte Metadaten nicht lesen: {metadata_error}")
        
        # Verzeichnisstruktur des Projekts durchsuchen
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    file_path = os.path.join(root, file)
                    images_to_delete.append(file_path)
        
        # Zuerst die einzelnen Bilddateien löschen
        for image_path in images_to_delete:
            try:
                if os.path.exists(image_path) and os.path.isfile(image_path):
                    os.remove(image_path)
                    logger.debug(f"Gelöschtes Bild: {image_path}")
            except Exception as image_error:
                logger.warning(f"Warnung: Konnte Bild nicht löschen: {image_error}")
        
        # Dann das gesamte Projektverzeichnis löschen
        import shutil
        shutil.rmtree(project_dir)
        logger.info(f"Projekt {project_id} und alle zugehörigen Dateien wurden gelöscht.")
        
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Projekts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices')
def get_devices():
    """Liefert eine Liste aller erkannten Geräte."""
    try:
        devices = device_detector.get_devices()
        return jsonify(devices)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Geräte: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate_360', methods=['POST'])
def generate_360():
    """Generiert einen 360°-Viewer aus den aufgenommenen Bildern."""
    try:
        # Liste der Fotos nach Zeitstempel sortieren
        photo_dir = os.path.abspath('static/photos')
        photos = sorted([
            secure_filename(f) for f in os.listdir(photo_dir)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ])

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

@app.route('/rotate', methods=['POST'])
def rotate():
    # Eingabevalidierung
    try:
        degrees = float(request.form['degrees'])
        if degrees < 0 or degrees > 360:
            return jsonify({"error": "Ungültiger Drehwinkel. Muss zwischen 0 und 360 Grad liegen."}), 400
    except (KeyError, ValueError) as e:
        logger.error(f"Fehler bei Drehwinkel-Validierung: {e}")
        return jsonify({"error": "Fehlender oder ungültiger Parameter 'degrees'"}), 400
        
    try:
        interval = float(request.form.get('interval', 5))  # Default 5 seconds if not specified
        if interval < 0 or interval > 60:
            return jsonify({"error": "Ungültiges Intervall. Muss zwischen 0 und 60 Sekunden liegen."}), 400
    except ValueError as e:
        logger.error(f"Fehler bei Intervall-Validierung: {e}")
        return jsonify({"error": "Ungültiger Parameter 'interval'"}), 400

    # Rotate platform
    rotate_teller(degrees)

    return jsonify({"status": "success", "message": f"Drehung um {degrees} Grad abgeschlossen"})

@app.route('/static/photos/<filename>')
def serve_photo(filename):
    # Sichere Dateinamensverarbeitung
    safe_filename = secure_filename(filename)
    if not safe_filename or safe_filename != filename:
        logger.warning(f"Versuch, auf potenziell gefährliche Datei zuzugreifen: {filename}")
        abort(404)  # Datei nicht gefunden, wenn der Dateiname verdächtig ist
    
    photos_dir = os.path.abspath('static/photos')
    return send_from_directory(photos_dir, safe_filename)

@app.route('/api/devices')
def api_devices():
    """Liefert eine Liste aller erkannten Geräte."""
    try:
        devices = device_detector.get_devices()
        return jsonify(devices)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Geräte: {e}")
        return jsonify({"error": "Fehler beim Abrufen der Geräte", "message": str(e)}), 500

if __name__ == '__main__':
    # Ensure static directories exist
    os.makedirs('static/photos', exist_ok=True)
    os.makedirs('static/projects', exist_ok=True)

    # Debugger-Nachrichten für Verzeichnisse
    logger.info(f"Statische Verzeichnisse überprüft/erstellt")
    logger.info(f"Fotos-Verzeichnis: {os.path.abspath('static/photos')}")
    logger.info(f"Projekte-Verzeichnis: {os.path.abspath('static/projects')}")
    
    # Aktiviere nur im Entwicklungsmodus den Debug-Modus
    is_development = os.environ.get('FLASK_ENV') == 'development'
    if is_development:
        logger.info("Starte Server im Entwicklungsmodus mit aktiviertem Debug")
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        logger.info("Starte Server im Produktionsmodus ohne Debug")
        app.run(host='0.0.0.0', port=5000, debug=False)
