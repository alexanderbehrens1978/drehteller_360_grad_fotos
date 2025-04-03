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
def viewer_overview():
    """Zeigt eine Übersicht aller Projekte und den 360° Viewer für ein ausgewähltes Projekt"""
    # Projekte aus dem ProjectManager laden
    from app.models.project import ProjectManager
    from app.utils.path_manager import PathManager
    
    path_manager = PathManager()
    project_manager = ProjectManager(path_manager.projects_dir)
    
    projects = project_manager.get_all_projects()
    
    # Ausgewähltes Projekt (falls vorhanden)
    project_id = request.args.get('project')
    selected_project = None
    
    if project_id:
        selected_project = project_manager.get_project(project_id)
    
    return render_template('viewer_overview.html', 
                          projects=projects,
                          selected_project=selected_project)

@main_bp.route('/rotate', methods=['POST'])
def rotate():
    """Nimmt ein Foto auf und dreht dann den Teller zur nächsten Position
       Alternative: Mit mode=rotate_only wird nur gedreht ohne Foto zu machen"""
    global arduino_controller, camera_controller, turntable_controller
    
    try:
        # Überprüfen des Modus (Foto+Rotation oder nur Rotation)
        mode = request.form.get('mode', 'photo_and_rotate')
        logger.debug(f"Rotations-Modus: {mode}")
        
        # Parameter validieren
        if 'degrees' not in request.form:
            return jsonify({"error": "Parameter 'degrees' fehlt"}), 400
            
        if 'project_id' not in request.form:
            return jsonify({"error": "Parameter 'project_id' fehlt"}), 400
            
        # Parameter extrahieren
        try:
            degrees = int(request.form['degrees'])
            # Im photo_only-Modus erlauben wir auch 0 Grad
            if mode == 'photo_only':
                if degrees < 0 or degrees > 360:
                    return jsonify({"error": "Ungültiger Drehwinkel. Muss zwischen 0 und 360 Grad liegen."}), 400
            else:
                if degrees <= 0 or degrees > 360:
                    return jsonify({"error": "Ungültiger Drehwinkel. Muss zwischen 1 und 360 Grad liegen."}), 400
        except ValueError:
            return jsonify({"error": "Ungültiger Drehwinkel. Muss eine Zahl sein."}), 400
            
        project_id = request.form['project_id']
        
        # Projekt laden
        from app.models.project import ProjectManager
        from app.utils.path_manager import PathManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        project = project_manager.get_project(project_id)
        
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Überprüfe Arduino-Verbindung
        if not arduino_controller or not arduino_controller.is_connected():
            logger.warning("Arduino ist nicht verbunden!")
            # Versuche erneut zu verbinden
            if arduino_controller:
                arduino_port = config_manager.get('arduino.port')
                arduino_baudrate = config_manager.get('arduino.baudrate', 9600)
                arduino_controller.port = arduino_port
                arduino_controller.baudrate = arduino_baudrate
                connected = arduino_controller.connect()
                if not connected:
                    return jsonify({"error": "Arduino konnte nicht verbunden werden. Bitte überprüfen Sie die Verbindung."}), 500
        
        # 1. Je nach Modus entweder nur ein Foto oder auch die Rotation ausführen
        photo_path = None
        rel_path = None
        
        if mode != 'rotate_only':
            # WICHTIG: Hier die gespeicherte Kameraeinstellung aus der Konfiguration verwenden
            # NICHT den globalen camera_controller, der möglicherweise beim Start initialisiert wurde
            saved_camera_type = config_manager.get('camera.type', 'webcam')
            saved_camera_device = config_manager.get('camera.device_path', '/dev/video0')
            resolution = config_manager.get('camera.resolution')
            
            # Erstelle einen temporären Kamera-Controller mit den aktuellen Einstellungen
            from app.controllers.camera_controller import CameraController
            temp_camera_controller = CameraController(
                camera_type=saved_camera_type,
                device=saved_camera_device,
                resolution=resolution
            )
            
            logger.info(f"Verwende Kamera: Typ={saved_camera_type}, Gerät={saved_camera_device}")
            
            # Foto aufnehmen
            timestamp = int(time.time())
            filename = f'photo_{timestamp}_{degrees}.jpg'
            
            # Verzeichnis für das Projekt erstellen, falls noch nicht vorhanden
            project_images_dir = os.path.join(project.path, 'images')
            os.makedirs(project_images_dir, exist_ok=True)
            
            # Vollständiger Pfad für das Bild
            photo_path = os.path.join(project_images_dir, filename)
            
            # Foto aufnehmen mit dem temporären Kamera-Controller
            logger.debug(f"Nehme Foto mit {saved_camera_type} auf...")
            camera_success = temp_camera_controller.capture_photo(photo_path)
            
            if not camera_success:
                raise Exception(f"Kamera ({saved_camera_type}) konnte kein Foto aufnehmen.")
                
            # Bild zum Projekt hinzufügen mit dem korrekten Winkel
            project.add_image(photo_path, angle=degrees, timestamp=timestamp)
            
            # Relativen Pfad für die Antwort erstellen
            rel_path = f"/projects/image/{project_id}/{filename}"
            logger.debug(f"Relativer Bildpfad für Antwort: {rel_path}")
        
        # 2. Jetzt den Drehteller drehen, wenn der Modus es erlaubt
        rotation_success = False
        
        if mode != 'photo_only':
            logger.debug(f"Drehe Teller um {degrees}°...")
            
            # Versuche über TurntableController zu drehen
            if turntable_controller and turntable_controller.arduino and turntable_controller.arduino.is_connected():
                logger.debug(f"Versuche über TurntableController zu drehen, Winkel: {degrees}°")
                rotation_success = turntable_controller.move_degrees(degrees)
                
                if rotation_success:
                    # Aktualisiere die Position im Projekt
                    new_position = turntable_controller.current_position
                    project.update_position(new_position)
                    logger.debug(f"Position im Projekt aktualisiert: {new_position}°")
                
                logger.debug(f"TurntableController-Rotation erfolgreich: {rotation_success}")
            
            # Falls nicht erfolgreich, versuche direkt über den Arduino-Controller zu drehen
            if not rotation_success and arduino_controller and arduino_controller.is_connected():
                logger.debug(f"Versuche direkt über ArduinoController zu drehen, Winkel: {degrees}°")
                # Berechne die Rotationszeit basierend auf 0,8° pro Sekunde
                rotation_time_ms = int((float(degrees) / 0.8) * 1000)
                logger.debug(f"Berechnete Rotationszeit: {rotation_time_ms} ms")
                
                # Motorbefehl senden
                rotation_success = arduino_controller.send_command(f"MOTOR:{rotation_time_ms}")
                logger.debug(f"ArduinoController-Rotation erfolgreich: {rotation_success}")
                
                if rotation_success:
                    # Wenn kein TurntableController existiert, manuell Position aktualisieren
                    new_position = (project.current_position + degrees) % 360
                    project.update_position(new_position)
                    logger.debug(f"Position im Projekt manuell aktualisiert: {new_position}°")
        
        # Bei reset_position=true wird die Position auf 0 zurückgesetzt (z.B. bei Home-Position)
        if request.form.get('reset_position') == 'true':
            project.update_position(0)
            if turntable_controller:
                turntable_controller.current_position = 0
            logger.debug("Position auf 0° zurückgesetzt (Home-Position)")
        
        # Antwortobjekt zusammenstellen
        response = {
            "status": "success",
            "message": "Aktion erfolgreich ausgeführt",
            "position": project.current_position
        }
        
        if photo_path:
            response["photo"] = rel_path
            response["angle"] = degrees
        
        logger.info(f"Rotation/Foto für Projekt {project_id} erfolgreich: Position {project.current_position}°")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Fehler bei der Foto-Aufnahme/Rotation: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@main_bp.route('/stop_rotation', methods=['POST'])
def stop_rotation():
    """Stoppt die aktuelle Rotation"""
    try:
        if turntable_controller:
            turntable_controller.stop_session()
            logger.info("Rotation wurde gestoppt")
            return jsonify({"status": "success", "message": "Rotation wurde gestoppt"})
        else:
            logger.error("Turntable-Controller ist nicht initialisiert")
            return jsonify({"status": "error", "error": "Turntable-Controller ist nicht initialisiert"}), 500
    except Exception as e:
        logger.error(f"Fehler beim Stoppen der Rotation: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

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
    """Leitet Anfragen an den CloudImage-Viewer weiter"""
    data = request.get_json()
    
    if not data:
        logger.error("Fehler: request.get_json() gibt None zurück!")
        return jsonify({"error": "Ungültige Anfrage, kein JSON erhalten"}), 400

    logger.debug(f"Empfangene Daten: {data}")  # Debug-Ausgabe

    if 'project_id' not in data:
        logger.error("Fehlende project_id!")
        return jsonify({"error": "Fehlende project_id"}), 400

    project_id = data['project_id']
    logger.info(f"Generiere 360°-Viewer für Projekt: {project_id}")

    try:
        # Projekt laden
        from app.models.project import ProjectManager
        from app.utils.path_manager import PathManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        project = project_manager.get_project(project_id)
        
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
            
        # Keine Pannellum-Generierung mehr, direkt zum CloudImage-Viewer weiterleiten
        return jsonify({
            "status": "success",
            "message": f"360°-CloudImage-Viewer für {project.name} ist verfügbar",
            "url": f"/viewer/cloudimage?project={project_id}"
        })
    except Exception as e:
        logger.error(f"Fehler beim Generieren des 360°-Viewers: {str(e)}")
        return jsonify({
            "error": f"Fehler beim Generieren des 360°-Viewers: {str(e)}"
        }), 500
