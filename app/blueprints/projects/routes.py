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
        
        # Debug-Logging für jedes Projekt
        for p in projects:
            logger.debug(f"Projekt geladen: {p.id} - {p.name}")
            
        return render_template('projects.html', projects=projects)
    except Exception as e:
        import traceback
        logger.error(f"Fehler beim Laden der Projekte: {str(e)}\n{traceback.format_exc()}")
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
            
            # Aktuelle Tellerposition als Ausgangsposition für das neue Projekt verwenden
            current_position = 0
            if turntable_controller and hasattr(turntable_controller, 'get_position'):
                try:
                    current_position = turntable_controller.get_position()
                    logger.debug(f"Aktuelle Tellerposition für neues Projekt übernommen: {current_position}°")
                except Exception as e:
                    logger.error(f"Fehler beim Abrufen der Tellerposition: {str(e)}")
            
            # Setze die Startposition des Drehtellers für das neue Projekt
            project.current_position = current_position
            
            logger.debug(f"Neues Projekt erstellt: {project.name} (ID: {project.id})")
            
            # Stelle sicher, dass der project_manager korrekt initialisiert ist
            global project_manager
            if not project_manager or not hasattr(project_manager, 'save_project'):
                logger.error("ProjectManager wurde nicht korrekt initialisiert")
                project_manager = ProjectManager(path_manager.projects_dir)
            
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

        # Projekt löschen - verwende die bereits initialisierten Instanzen
        # statt neue zu erstellen, um unerwünschte Seiteneffekte zu vermeiden
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
    try:
        logger.debug(f"Bild angefordert: Projekt={project_id}, Pfad={image_path}")
        
        # ID validieren
        if not validate_project_id(project_id):
            logger.warning(f"Ungültige Projekt-ID: {project_id}")
            abort(404)
            
        # Path Manager holen
        path_manager = PathManager()
        
        # Projektverzeichnis ermitteln
        project_path = path_manager.get_project_path(project_id)
        logger.debug(f"Projektpfad: {project_path}")
        
        # Vollständiger Bildpfad
        if 'images' not in image_path:
            # Falls "images" nicht im Pfad ist, fügen wir es hinzu
            full_image_path = os.path.join(project_path, 'images', image_path)
        else:
            # Falls "images" bereits im Pfad ist
            full_image_path = os.path.join(project_path, image_path)
            
        logger.debug(f"Vollständiger Bildpfad: {full_image_path}")
        
        # Überprüfen, ob die Datei existiert
        if not os.path.exists(full_image_path):
            logger.warning(f"Datei existiert nicht: {full_image_path}")
            # Versuche einen alternativen Pfad
            alt_path = os.path.join(project_path, image_path)
            logger.debug(f"Versuche alternativen Pfad: {alt_path}")
            if os.path.exists(alt_path):
                full_image_path = alt_path
            else:
                abort(404)
            
        # Bild-Verzeichnis und Dateinamen trennen
        image_dir = os.path.dirname(full_image_path)
        image_file = os.path.basename(full_image_path)
        
        logger.debug(f"Sende Datei: Verzeichnis={image_dir}, Datei={image_file}")
        return send_from_directory(image_dir, image_file)
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Bildes: {str(e)}")
        abort(500)

@projects_bp.route('/<project_id>/view360')
def view_360(project_id):
    """Zeigt den 360°-Viewer für ein Projekt an"""
    # Projekt laden
    project = project_manager.get_project(project_id)
    if not project:
        return render_template('error.html', message="Projekt nicht gefunden"), 404
    
    # Weiterleitung zum Viewer
    return redirect(f'/viewer/cloudimage?project={project_id}')
