#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/projects/routes.py
Enthält die Routen für die Projektverwaltung
"""

import os
import json
import time
import logging
import uuid
from flask import render_template, request, jsonify, redirect, url_for, send_from_directory
from app.blueprints.projects import projects_bp
from app.models.project import Project, ProjectManager
from app.models.photo_session import PhotoSession
from app import arduino_controller, camera_controller, turntable_controller
from app.utils.path_manager import PathManager

# Logger einrichten
logger = logging.getLogger(__name__)

# Path Manager erstellen
path_manager = PathManager()

# Projekt-Manager erstellen
project_manager = ProjectManager(path_manager.projects_dir)

@projects_bp.route('/')
def projects_page():
    """Zeigt die Projektverwaltungsseite an"""
    return render_template('projects.html')

@projects_bp.route('/create', methods=['GET', 'POST'])
def create_project():
    """Erstellt ein neues Projekt"""
    if request.method == 'POST':
        # Projektdaten aus dem Formular holen
        name = request.form.get('name', f"Projekt {time.strftime('%Y-%m-%d %H:%M:%S')}")
        description = request.form.get('description', '')
        angle_step = int(request.form.get('angle_step', 15))
        
        # Neues Projekt erstellen
        project = Project(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            angle_step=angle_step
        )
        
        # Projekt speichern
        project_manager.save_project(project)
        
        # Zur Projektseite weiterleiten
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    # Formular zum Erstellen eines Projekts anzeigen
    return render_template('project_create.html')

@projects_bp.route('/<project_id>')
def view_project(project_id):
    """
    Zeigt ein Projekt an
    
    Args:
        project_id: ID des Projekts
    """
    # Projekt laden
    project = project_manager.get_project(project_id)
    
    if not project:
        # Wenn das Projekt nicht gefunden wurde, zur Projektliste weiterleiten
        return redirect(url_for('projects.projects_page'))
    
    # Projekt anzeigen
    return render_template('project_view.html', project=project)

@projects_bp.route('/<project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    """
    Bearbeitet ein Projekt
    
    Args:
        project_id: ID des Projekts
    """
    # Projekt laden
    project = project_manager.get_project(project_id)
    
    if not project:
        # Wenn das Projekt nicht gefunden wurde, zur Projektliste weiterleiten
        return redirect(url_for('projects.projects_page'))
    
    if request.method == 'POST':
        # Projektdaten aus dem Formular holen
        project.name = request.form.get('name', project.name)
        project.description = request.form.get('description', project.description)
        project.angle_step = int(request.form.get('angle_step', project.angle_step))
        
        # Projekt speichern
        project_manager.save_project(project)
        
        # Zur Projektseite weiterleiten
        return redirect(url_for('projects.view_project', project_id=project.id))
    
    # Formular zum Bearbeiten des Projekts anzeigen
    return render_template('project_edit.html', project=project)

@projects_bp.route('/<project_id>/capture', methods=['GET', 'POST'])
def capture_session(project_id):
    """
    Startet eine Aufnahmesession für ein Projekt
    
    Args:
        project_id: ID des Projekts
    """
    # Projekt laden
    project = project_manager.get_project(project_id)
    
    if not project:
        # Wenn das Projekt nicht gefunden wurde, zur Projektliste weiterleiten
        return redirect(url_for('projects.projects_page'))
    
    if request.method == 'POST':
        # Prüfen, ob die Controller initialisiert sind
        if not arduino_controller or not arduino_controller.is_connected():
            return render_template('capture.html', project=project, 
                                 error="Arduino ist nicht verbunden.")
        
        if not camera_controller:
            return render_template('capture.html', project=project, 
                                 error="Kamera-Controller ist nicht initialisiert.")
        
        if not turntable_controller:
            return render_template('capture.html', project=project, 
                                 error="Drehteller-Controller ist nicht initialisiert.")
        
        try:
            # Neue Session erstellen
            session_id = str(uuid.uuid4())
            session_name = request.form.get('session_name', f"Session {time.strftime('%Y-%m-%d %H:%M')}")
            
            session = PhotoSession(
                id=session_id,
                name=session_name,
                timestamp=time.time(),
                angle_step=project.angle_step
            )
            
            # Session zum Projekt hinzufügen
            project.add_session(session)
            
            # Session starten
            if turntable_controller.start_session(project, camera_controller):
                # Projekt speichern
                project_manager.save_project(project)
                
                # Zur Projektseite weiterleiten
                return redirect(url_for('projects.view_project', project_id=project.id))
            else:
                return render_template('capture.html', project=project, 
                                     error="Fehler beim Starten der Aufnahmesession.")
                
        except Exception as e:
            logger.error(f"Fehler bei der Aufnahmesession: {e}")
            return render_template('capture.html', project=project, 
                                 error=f"Fehler: {str(e)}")
    
    # Formular zum Starten einer Aufnahmesession anzeigen
    return render_template('capture.html', project=project)

@projects_bp.route('/<project_id>/delete')
def delete_project(project_id):
    """
    Löscht ein Projekt
    
    Args:
        project_id: ID des Projekts
    """
    # Projekt löschen
    project_manager.delete_project(project_id)
    
    # Zur Projektliste weiterleiten
    return redirect(url_for('projects.projects_page'))

@projects_bp.route('/image/<project_id>/<path:image_path>')
def get_project_image(project_id, image_path):
    """
    Liefert ein Projektbild
    
    Args:
        project_id: ID des Projekts
        image_path: Pfad zum Bild innerhalb des Projekts
    """
    project_dir = os.path.join(path_manager.projects_dir, project_id)
    directory = os.path.dirname(os.path.join(project_dir, image_path))
    filename = os.path.basename(image_path)
    
    return send_from_directory(directory, filename)

@projects_bp.route('/<project_id>/add_rotation', methods=['POST'])
def add_rotation_to_project(project_id):
    """
    Fügt eine Rotation zum Projekt hinzu
    
    Args:
        project_id: ID des Projekts
    """
    # Projekt laden
    project = project_manager.get_project(project_id)
    
    if not project:
        return jsonify({"error": "Projekt nicht gefunden"}), 404
    
    try:
        # Drehwinkel aus der Anfrage holen
        degrees = int(request.form.get('degrees', 15))
        
        # Drehteller rotieren
        if arduino_controller and arduino_controller.is_connected():
            arduino_controller.rotate_for_duration(degrees / 0.8 * 1000)  # 0,8 Grad pro Sekunde
        else:
            # Simulierte Rotation
            logger.info(f"Simulierte Rotation: {degrees} Grad")
            
        # Foto aufnehmen
        timestamp = int(time.time())
        filename = f"angle_{degrees:03d}_{timestamp}.jpg"
        photo_path = None
        
        if camera_controller:
            # Speicherpfad für das Foto
            photo_path = os.path.join(path_manager.get_project_path(project_id), "images", filename)
            
            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)
            
            # Foto aufnehmen
            success = camera_controller.capture_photo(photo_path)
            
            if not success:
                return jsonify({"error": "Fehler beim Aufnehmen des Fotos"}), 500
        else:
            # Simuliertes Foto
            from app.utils.webcam_simulator import webcam_simulator
            photo_path = webcam_simulator.capture_photo(filename)
            
            # Kopiere das Foto in das Projektverzeichnis
            import shutil
            target_path = os.path.join(path_manager.get_project_path(project_id), "images", filename)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy(photo_path, target_path)
            photo_path = target_path
        
        # Relativen Pfad zum Foto zurückgeben
        rel_path = os.path.relpath(photo_path, path_manager.base_dir)
        
        return jsonify({
            "status": "success",
            "photo_path": f"/{rel_path.replace(os.sep, '/')}",
            "degrees": degrees
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen einer Rotation: {e}")
        return jsonify({"error": str(e)}), 500
