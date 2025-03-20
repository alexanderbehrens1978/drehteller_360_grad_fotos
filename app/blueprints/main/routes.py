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
from flask import Blueprint

viewer_bp = Blueprint('viewer',__name__)

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
    """
    Führt eine Rotation und/oder Fotoaufnahme durch, je nach Modus:
    - mode=rotate_only: Nur Rotation
    - mode=photo_only: Nur Foto aufnehmen
    - mode=photo_and_rotate: Foto aufnehmen und dann rotieren
    """
    global arduino_controller, camera_controller, turntable_controller
    
    try:
        # Überprüfen des Modus
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
            if degrees < 0 or degrees > 360:
                return jsonify({"error": "Ungültiger Drehwinkel. Muss zwischen 0 und 360 Grad liegen."}), 400
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
        if mode != 'photo_only' and (not arduino_controller or not arduino_controller.is_connected()):
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
        
        # Überprüfe Kamera-Verbindung bei Foto-Modi
        if mode != 'rotate_only' and not camera_controller:
            return jsonify({"error": "Kamera-Controller ist nicht initialisiert."}), 500
        
        # Initialisierungswerte
        photo_path = None
        rel_path = None
        rotation_success = False
        
        # Je nach Modus verschiedene Aktionen ausführen
        
        # 1. Nur Rotation (ohne Foto)
        if mode == 'rotate_only':
            logger.debug(f"Führe nur Rotation um {degrees}° aus")
            
            if turntable_controller and turntable_controller.arduino and turntable_controller.arduino.is_connected():
                logger.debug(f"Versuche Rotation über TurntableController, Winkel: {degrees}°")
                rotation_success = turntable_controller.move_degrees(degrees)
                logger.debug(f"TurntableController-Rotation erfolgreich: {rotation_success}")
            
            # Falls nicht erfolgreich, versuche direkt über den Arduino-Controller
            if not rotation_success and arduino_controller and arduino_controller.is_connected():
                logger.debug(f"Versuche direkt über ArduinoController zu drehen, Winkel: {degrees}°")
                # Direkter Fallback: Motor steuern ohne rotate_for_duration
                try:
                    logger.debug("Verwende direkten Fallback für die Motordrehung")
                    # Berechne die Rotationszeit basierend auf 0,8° pro Sekunde
                    rotation_time_ms = int((float(degrees) / 0.8) * 1000)
                    logger.debug(f"Berechnete Rotationszeit: {rotation_time_ms} ms")
                    
                    # Motor einschalten
                    motor_on = arduino_controller.turn_motor_on()
                    logger.debug(f"Motor eingeschaltet: {motor_on}")
                    
                    # Warten für die berechnete Zeit
                    logger.debug(f"Motor für {rotation_time_ms} ms eingeschaltet")
                    time.sleep(rotation_time_ms / 1000.0)
                    
                    # Motor ausschalten
                    motor_off = arduino_controller.turn_motor_off()
                    logger.debug(f"Motor ausgeschaltet: {motor_off}")
                    
                    rotation_success = True
                    logger.debug("Fallback-Rotation erfolgreich")
                except Exception as e:
                    logger.error(f"Fehler bei Fallback-Rotation: {str(e)}")
                    # Extra Error handling
                    try:
                        arduino_controller.turn_motor_off()
                    except:
                        pass
        
        # 2. Nur Foto aufnehmen (ohne Rotation)
        elif mode == 'photo_only':
            logger.debug(f"Nehme nur Foto bei Position {degrees}° auf")
            
            # Foto aufnehmen
            timestamp = int(time.time())
            filename = f'photo_{timestamp}_{degrees}.jpg'
            
            # Verzeichnis für das Projekt erstellen, falls noch nicht vorhanden
            project_images_dir = os.path.join(project.path, 'images')
            os.makedirs(project_images_dir, exist_ok=True)
            
            # Vollständiger Pfad für das Bild
            photo_path = os.path.join(project_images_dir, filename)
            
            # Foto aufnehmen
            logger.debug("Nehme Foto auf...")
            camera_success = camera_controller.capture_photo(photo_path)
            
            if not camera_success:
                raise Exception("Kamera konnte kein Foto aufnehmen.")
                
            # Bild zum Projekt hinzufügen mit dem korrekten Winkel
            project.add_image(photo_path, angle=degrees, timestamp=timestamp)
            
            # Relativen Pfad für die Antwort erstellen
            rel_path = f"/projects/image/{project_id}/{filename}"
            logger.debug(f"Relativer Bildpfad für Antwort: {rel_path}")
            
        # 3. Kombinierter Modus: Foto aufnehmen und dann rotieren
        else:  # mode == 'photo_and_rotate' (default)
            logger.debug(f"Führe zuerst Foto bei {degrees}° auf und dann Rotation aus")
            
            # Zuerst das Foto aufnehmen
            timestamp = int(time.time())
            filename = f'photo_{timestamp}_{degrees}.jpg'
            
            # Verzeichnis für das Projekt erstellen, falls noch nicht vorhanden
            project_images_dir = os.path.join(project.path, 'images')
            os.makedirs(project_images_dir, exist_ok=True)
            
            # Vollständiger Pfad für das Bild
            photo_path = os.path.join(project_images_dir, filename)
            
            # Foto aufnehmen
            logger.debug("Nehme Foto auf...")
            camera_success = camera_controller.capture_photo(photo_path)
            
            if not camera_success:
                raise Exception("Kamera konnte kein Foto aufnehmen.")
                
            # Bild zum Projekt hinzufügen mit dem korrekten Winkel
            project.add_image(photo_path, angle=degrees, timestamp=timestamp)
            
            # Relativen Pfad für die Antwort erstellen
            rel_path = f"/projects/image/{project_id}/{filename}"
            logger.debug(f"Relativer Bildpfad für Antwort: {rel_path}")
            
            # Dann die Rotation durchführen
            logger.debug(f"Führe Rotation um {degrees}° aus")
            
            if turntable_controller and turntable_controller.arduino and turntable_controller.arduino.is_connected():
                logger.debug(f"Versuche Rotation über TurntableController, Winkel: {degrees}°")
                rotation_success = turntable_controller.move_degrees(degrees)
                logger.debug(f"TurntableController-Rotation erfolgreich: {rotation_success}")
            
            # Falls nicht erfolgreich, versuche direkt über den Arduino-Controller
            if not rotation_success and arduino_controller and arduino_controller.is_connected():
                logger.debug(f"Versuche direkt über ArduinoController zu drehen, Winkel: {degrees}°")
                try:
                    # Berechne die Rotationszeit basierend auf 0,8° pro Sekunde
                    rotation_time_ms = int((float(degrees) / 0.8) * 1000)
                    logger.debug(f"Berechnete Rotationszeit: {rotation_time_ms} ms")
                    
                    # Motor einschalten
                    motor_on = arduino_controller.turn_motor_on()
                    logger.debug(f"Motor eingeschaltet: {motor_on}")
                    
                    # Warten für die berechnete Zeit
                    logger.debug(f"Motor für {rotation_time_ms} ms eingeschaltet")
                    time.sleep(rotation_time_ms / 1000.0)
                    
                    # Motor ausschalten
                    motor_off = arduino_controller.turn_motor_off()
                    logger.debug(f"Motor ausgeschaltet: {motor_off}")
                    
                    rotation_success = True
                    logger.debug("Fallback-Rotation erfolgreich")
                except Exception as e:
                    logger.error(f"Fehler bei Fallback-Rotation: {str(e)}")
                    try:
                        arduino_controller.turn_motor_off()
                    except:
                        pass
        
        # Log für das Rotation-Ergebnis bei Rotationsmodi
        if mode != 'photo_only':
            if rotation_success:
                logger.info(f"Drehteller erfolgreich um {degrees}° gedreht")
            else:
                logger.warning(f"Drehteller konnte nicht gedreht werden, Winkel: {degrees}°")
        
        # Erfolgsantwort mit verschiedenen Informationen je nach Modus
        return jsonify({
            "status": "success",
            "photo": rel_path,
            "angle": degrees,
            "rotation_success": rotation_success if mode != 'photo_only' else None,
            "mode": mode
        })
        
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
    """Generiert einen 360°-Viewer aus den Projektbildern"""
    try:
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
        
        # Erfolgsantwort mit URL zum Viewer
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

@viewer_bp.route('/')
def viewer_overview():
    """Zeigt eine Übersicht aller Projekte und den 360° Viewer für ein ausgewähltes Projekt"""
    try:
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
            
            # Prüfen, ob Bilder in den Request-Parametern angegeben wurden
            images_param = request.args.get('images')
            if images_param:
                # Wenn Bilder explizit angegeben wurden, diese filtern
                image_paths = images_param.split(',')
                
                # Nur die angegebenen Bilder behalten
                if selected_project and selected_project.images:
                    filtered_images = []
                    for img in selected_project.images:
                        if img['path'] in image_paths:
                            filtered_images.append(img)
                    
                    # Temporäre Kopie des Projekts mit gefilterten Bildern
                    selected_project.images = filtered_images
            
            # Wenn ein Projekt gefunden wurde, direkt zum Viewer
            if selected_project:
                return render_template('viewer/sphere_viewer.html', project=selected_project)
        
        # Ansonsten die Übersichtsseite anzeigen
        return render_template('viewer/overview.html', projects=projects)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Viewer-Übersicht: {str(e)}")
        return render_template('error.html', message=f"Fehler beim Laden der Viewer-Übersicht: {str(e)}"), 500

@main_bp.route('/arduino_test', methods=['GET'])
def test_arduino():
    """Testet die Arduino-Verbindung und die Motorfunktion"""
    if arduino_controller and arduino_controller.is_connected():
        # Motor kurz einschalten
        success = arduino_controller.turn_motor_on()
        time.sleep(1)  # Eine Sekunde warten
        arduino_controller.turn_motor_off()
        
        if success:
            return jsonify({"status": "success", "message": "Arduino verbunden und Motor funktioniert"})
        else:
            return jsonify({"status": "error", "message": "Arduino verbunden, aber Motor reagiert nicht"})
    else:
        return jsonify({"status": "error", "message": "Arduino nicht verbunden"})
