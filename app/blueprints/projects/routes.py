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
from flask import render_template, request, jsonify, redirect, url_for, send_from_directory, abort, flash
from app.blueprints.projects import projects_bp
from app.models.project import Project, ProjectManager
from app.models.photo_session import PhotoSession
from app import arduino_controller, camera_controller, turntable_controller
from app.utils.path_manager import PathManager
from app.utils.secure_path import validate_project_id, secure_join, secure_filename

# Logger einrichten
logger = logging.getLogger(__name__)

# Path Manager erstellen
path_manager = PathManager()

# Projekt-Manager erstellen
project_manager = ProjectManager(path_manager.projects_dir)

@projects_bp.route('/')
def projects_page():
    """Zeigt die Projektverwaltungsseite an"""
    try:
        # Alle Projekte laden
        projects = project_manager.get_all_projects()
        return render_template('projects.html', projects=projects)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Projekte: {str(e)}")
        return render_template('error.html', message=f"Fehler beim Laden der Projekte: {str(e)}"), 500


@projects_bp.route('/create', methods=['GET', 'POST'])
def create_project():
    """Erstellt ein neues Projekt"""
    try:
        if request.method == 'POST':
            # Projektdaten aus dem Formular holen und validieren
            name = request.form.get('name', f"Projekt {time.strftime('%Y-%m-%d %H:%M:%S')}")
            description = request.form.get('description', '')
            
            try:
                angle_step = int(request.form.get('angle_step', 15))
                if angle_step <= 0 or angle_step > 360:
                    raise ValueError("Ungültiger Winkelschritt")
            except ValueError:
                logger.error(f"Ungültiger Winkelschritt: {request.form.get('angle_step')}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({"error": "Ungültiger Winkelschritt, bitte eine positive Zahl eingeben."}), 400
                else:
                    return render_template('project_create.html', error="Ungültiger Winkelschritt, bitte eine positive Zahl eingeben."), 400
            
            # Neues Projekt erstellen
            project = Project(
                id=str(uuid.uuid4()),
                name=name,
                description=description,
                angle_step=angle_step
            )
            
            # Projekt speichern
            success = project_manager.save_project(project)
            
            if not success:
                logger.error(f"Projekt konnte nicht gespeichert werden: {project.id}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({"error": "Fehler beim Speichern des Projekts."}), 500
                else:
                    return render_template('project_create.html', error="Fehler beim Speichern des Projekts."), 500
            
            logger.info(f"Neues Projekt erstellt: {project.id} - {project.name}")
            
            # Zur Projektseite weiterleiten
            return redirect(url_for('projects.view_project', project_id=project.id))
        
        # Formular zum Erstellen eines Projekts anzeigen
        return render_template('project_create.html')
    except Exception as e:
        logger.error(f"Fehler beim Erstellen eines Projekts: {str(e)}")
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"error": str(e)}), 500
        else:
            return render_template('project_create.html', error=f"Ein Fehler ist aufgetreten: {str(e)}"), 500
















@projects_bp.route('/<project_id>')
def view_project(project_id):
    """
    Zeigt ein Projekt an
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt-ID validieren
        if not validate_project_id(project_id):
            logger.warning(f"Ungültige Projekt-ID: {project_id}")
            abort(404)
            
        # Projekt laden
        project = project_manager.get_project(project_id)
        
        if not project:
            # Wenn das Projekt nicht gefunden wurde, zur Projektliste weiterleiten
            logger.warning(f"Projekt nicht gefunden: {project_id}")
            flash('Projekt nicht gefunden.', 'error')
            return redirect(url_for('projects.projects_page'))
        
        # Projekt anzeigen
        return render_template('project_view.html', project=project)
    except Exception as e:
        logger.error(f"Fehler beim Anzeigen des Projekts {project_id}: {str(e)}")
        return render_template('error.html', message=f"Fehler beim Anzeigen des Projekts: {str(e)}"), 500

@projects_bp.route('/delete/<project_id>', methods=['POST'])
def delete_project(project_id):
    """Löscht ein Projekt"""
    try:
        # Projekt-ID validieren
        from app.utils.secure_path import validate_project_id
        if not validate_project_id(project_id):
            logger.warning(f"Ungültige Projekt-ID: {project_id}")
            return render_template('error.html', message="Ungültige Projekt-ID"), 400
            
        # Projekt löschen
        from app.models.project import ProjectManager
        from app.utils.path_manager import PathManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        
        success = project_manager.delete_project(project_id)
        
        if success:
            logger.info(f"Projekt {project_id} gelöscht")
            return redirect(url_for('projects.projects_page'))
        else:
            logger.error(f"Fehler beim Löschen des Projekts {project_id}")
            return render_template('error.html', message="Fehler beim Löschen des Projekts"), 500
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Projekts {project_id}: {str(e)}")
        return render_template('error.html', message=f"Fehler beim Löschen des Projekts: {str(e)}"), 500

@projects_bp.route('/image/<project_id>/<path:image_path>')
def get_project_image(project_id, image_path):
    """
    Liefert ein Projektbild
    
    Args:
        project_id: ID des Projekts
        image_path: Pfad zum Bild innerhalb des Projekts
    """
    # ID und Bildpfad validieren
    if not validate_project_id(project_id):
        logger.warning(f"Ungültige Projekt-ID: {project_id}")
        abort(404)
        
    # Den Bildpfad sicher machen
    safe_image_filename = secure_filename(os.path.basename(image_path))
    if not safe_image_filename:
        abort(404)
        
    # Projektverzeichnis im abgesicherten Pfad
    project_dir = project_manager.get_project_path(project_id)
    
    # Sicherstellen, dass das Verzeichnis existiert
    if not os.path.isdir(project_dir):
        abort(404)
    
    # Bildverzeichnis und Dateinamen sicher zusammenführen
    image_dir_path = os.path.dirname(os.path.join(project_dir, image_path))
    
    # Sicherstellen, dass das Bildverzeichnis innerhalb des Projektverzeichnisses liegt
    if not os.path.abspath(image_dir_path).startswith(os.path.abspath(project_dir)):
        abort(404)
    
    return send_from_directory(image_dir_path, safe_image_filename)
