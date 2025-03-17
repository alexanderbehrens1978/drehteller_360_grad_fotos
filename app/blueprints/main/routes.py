#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/main/routes.py
Enthält die Hauptrouten der Anwendung
"""

import os
import json
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
def viewer():
    """Zeigt den 360°-Viewer für ein Projekt an"""
    # Projekt-ID aus Query-Parameter holen
    project_id = request.args.get('project')
    
    if not project_id:
        return render_template('error.html', message="Keine Projekt-ID angegeben"), 400
        
    # Viewer-Template rendern
    return render_template('viewer.html')

@main_bp.route('/rotate', methods=['POST'])
def rotate():
    global arduino_controller
    global camera_controller
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
        
        # Drehteller rotieren - Stellen Sie sicher, dass turntable_controller korrekt initialisiert ist
        if not arduino_controller or not arduino_controller.is_connected():
            # Versuche, die Arduino-Verbindung herzustellen
            from app.utils.config_manager import config_manager
            arduino_port = config_manager.get('arduino.port', '/dev/ttyACM0')
            arduino_baudrate = config_manager.get('arduino.baudrate', 9600)
            
            # Controller neu initialisieren und verbinden
            from app.controllers.arduino_controller import ArduinoController
            arduino_controller = ArduinoController(arduino_port, arduino_baudrate)
            
            # Wenn die Verbindung jetzt immer noch nicht hergestellt werden kann, Fehler melden
            if not arduino_controller.is_connected():
                return jsonify({
                    "status": "warning",
                    "error": "Arduino nicht verbunden. Foto wird aufgenommen, aber der Teller wird nicht gedreht.",
                    "suggestion": "Überprüfen Sie die Arduino-Verbindung in den Einstellungen."
                })
        
        # Drehteller drehen
        try:
            rotate_teller(degrees)
        except Exception as e:
            logger.error(f"Fehler beim Drehen des Tellers: {str(e)}")
            return jsonify({
                "status": "warning",
                "error": f"Fehler beim Drehen des Tellers: {str(e)}",
                "suggestion": "Überprüfen Sie die Arduino-Verbindung und die Stromversorgung des Drehtellers."
            })
        
        # Foto mit Zeitstempel aufnehmen
        timestamp = int(time.time())
        filename = f'photo_{timestamp}_{degrees}.jpg'
        
        # Stelle sicher, dass der Kamera-Controller korrekt initialisiert ist
        if not camera_controller:
            from app.utils.config_manager import config_manager
            from app.controllers.camera_controller import CameraController
            
            camera_type = config_manager.get('camera.type', 'webcam')
            camera_device = config_manager.get('camera.device_path', '/dev/video0')
            resolution = config_manager.get('camera.resolution', {'width': 1280, 'height': 720})
            
            # Kamera-Profil für gphoto2 laden, falls es sich um eine gphoto2-Kamera handelt
            camera_settings = {}
            if camera_type == 'gphoto2':
                # Kameramodell ermitteln
                try:
                    result = subprocess.run(['gphoto2', '--port', camera_device, '--summary'],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          text=True)
                    
                    if result.returncode == 0:
                        camera_model = None
                        for line in result.stdout.split('\n'):
                            if 'Model:' in line:
                                camera_model = line.split('Model:', 1)[1].strip()
                                break
                        
                        if camera_model:
                            # Passendes Profil suchen
                            profiles = config_manager.get('camera.gphoto2_profiles', {})
                            if camera_model in profiles:
                                camera_settings = profiles[camera_model].get('settings', {})
                except Exception as e:
                    logger.error(f"Fehler beim Ermitteln des Kameramodells: {str(e)}")
            
            # Controller initialisieren
            camera_controller = CameraController(camera_type, camera_device, resolution, camera_settings)
        
        # Bild aufnehmen
        try:
            # Verzeichnis für das Projekt erstellen, falls noch nicht vorhanden
            project_images_dir = os.path.join(project.path, 'images')
            os.makedirs(project_images_dir, exist_ok=True)
            
            # Vollständiger Pfad für das Bild
            photo_path = os.path.join(project_images_dir, filename)
            
            # Foto aufnehmen
            success = camera_controller.capture_photo(photo_path)
            
            if not success:
                raise Exception("Kamera konnte kein Foto aufnehmen.")
                
            # Bild zum Projekt hinzufügen mit dem korrekten Winkel
            project.add_image(photo_path, angle=degrees, timestamp=timestamp)
            
            # Relativen Pfad für die Antwort erstellen
            rel_path = os.path.join('/projects/image', project_id, 'images', filename)
            
            return jsonify({
                "status": "success",
                "photo": rel_path,
                "angle": degrees  # Winkel in der Antwort zurückgeben
            })
            
        except Exception as e:
            logger.error(f"Fehler beim Aufnehmen des Fotos: {str(e)}")
            return jsonify({
                "status": "error",
                "error": f"Fehler beim Aufnehmen des Fotos: {str(e)}",
                "suggestion": "Überprüfen Sie die Kamera-Verbindung und -Einstellungen."
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
    try:
        from app.utils.config_manager import config_manager
        return jsonify(config_manager.config)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Konfiguration: {str(e)}")
        return jsonify({"error": str(e)}), 500

@main_bp.route('/save_config', methods=['POST'])
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

@main_bp.route('/generate_360', methods=['POST'])
def generate_360():
    """Generiert einen 360°-Viewer aus den Projektbildern"""
    data = request.get_json()
    
    if not data:
        print("Fehler: request.get_json() gibt None zurück!")
        return jsonify({"error": "Ungültige Anfrage, kein JSON erhalten"}), 400

    print(f"Empfangene Daten: {data}")  # Debug-Ausgabe

    if 'project_id' not in data:
        print("Fehlende project_id!")
        return jsonify({"error": "Fehlende project_id"}), 400

    project_id = data['project_id']
    print(f"Generiere 360°-Viewer für Projekt: {project_id}")

    try:
        # Projekt laden
        from app.models.project import ProjectManager
        from app.utils.path_manager import PathManager
        import shutil
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        project = project_manager.get_project(project_id)
        
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Pfade erstellen
        static_dir = os.path.abspath(os.path.join(current_app.root_path, '..', 'static'))
        projects_dir = os.path.join(static_dir, 'projects')
        project_dir = os.path.join(projects_dir, project_id)
        
        # Verzeichnis erstellen, falls es noch nicht existiert
        os.makedirs(project_dir, exist_ok=True)
        
        # Bildpfade sammeln (nur Dateinamen ohne Pfad)
        image_filenames = []
        for image in project.images:
            # Bildpfad aus dem Projekt extrahieren
            src_path = os.path.join(project.path, image['path'])
            filename = os.path.basename(src_path)
            dst_path = os.path.join(project_dir, filename)
            
            # Bild in das Projektverzeichnis kopieren
            if os.path.exists(src_path) and not os.path.exists(dst_path):
                shutil.copy(src_path, dst_path)
                
            image_filenames.append(filename)
        
        # Metadaten erstellen
        metadata = {
            "name": project.name,
            "created": time.time(),
            "image_count": len(image_filenames),
            "images": image_filenames,
            "description": project.description
        }
        
        # Metadaten speichern
        metadata_path = os.path.join(project_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        return jsonify({
            "status": "success",
            "message": f"360°-Viewer für {project.name} wurde erfolgreich generiert",
            "url": f"/viewer?project={project_id}"
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Generieren des 360°-Viewers: {str(e)}")
        return jsonify({
            "error": f"Fehler beim Generieren des 360°-Viewers: {str(e)}"
        }), 500
