# Datei: app/blueprints/projects/routes.py
import os
import json
import time
import logging
import uuid
import re
from flask import (
    render_template, request, jsonify, 
    redirect, url_for, send_from_directory, abort
)
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

def sanitize_project_image_path(image_path):
    """
    Bereinigt und normalisiert den Bildpfad
    
    Args:
        image_path: Ursprünglicher Bildpfad
    
    Returns:
        Bereinigter Bildpfad
    """
    # Entferne mehrfache aufeinanderfolgende statische Verzeichnisse
    image_path = re.sub(r'^(static/)*', '', image_path)
    
    # Entferne Dopplungen von Projektpfaden
    image_path = re.sub(r'^(projects/)+', '', image_path)
    
    # Entferne führende Projekt-ID-Dopplungen
    parts = image_path.split('/')
    if len(parts) > 2 and parts[0] == parts[1]:
        image_path = '/'.join(parts[1:])
    
    return image_path

@projects_bp.route('/')
def projects_page():
    """Zeigt die Projektverwaltungsseite an"""
    try:
        # Alle Projekte laden
        projects = project_manager.get_all_projects()
        return render_template('projects/index.html', projects=projects)
    except Exception as e:
        logger.error(f"Fehler bei der Projektliste: {e}")
        return render_template('error.html', message=f"Fehler beim Laden der Projekte: {str(e)}"), 500

@projects_bp.route('/create', methods=['GET', 'POST'])
def create_project():
    """Erstellt ein neues Projekt"""
    if request.method == 'POST':
        try:
            # Projektdaten aus dem Formular holen
            name = request.form.get('name', f"Projekt {time.strftime('%Y-%m-%d %H:%M:%S')}")
            description = request.form.get('description', '')
            angle_step = int(request.form.get('angle_step', 15))
            
            # Neues Projekt erstellen
            project = Project(
                name=name,
                description=description,
                angle_step=angle_step
            )
            
            # Projekt speichern
            project_manager.save_project(project)
            
            # Zur Projektseite weiterleiten
            return redirect(url_for('projects.view_project', project_id=project.id))
        except Exception as e:
            logger.error(f"Fehler bei der Projekterstellung: {e}")
            return render_template('error.html', message=f"Fehler bei der Projekterstellung: {str(e)}"), 500
    
    # Formular zum Erstellen eines Projekts anzeigen
    return render_template('projects/create.html')

@projects_bp.route('/<project_id>')
def view_project(project_id):
    """
    Zeigt ein Projekt an
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt laden
        project = project_manager.get_project(project_id)
        
        if not project:
            # Wenn das Projekt nicht gefunden wurde, zur Projektliste weiterleiten
            logger.warning(f"Projekt nicht gefunden: {project_id}")
            return redirect(url_for('projects.projects_page'))
        
        # Alle Bilder für das Projekt sammeln
        project_images = []
        for session in project.sessions:
            for angle, photo_path in session.photos.items():
                # Stelle sicher, dass der Pfad relativ ist
                try:
                    # Versuche, einen relativen Pfad zu erstellen
                    relative_path = os.path.relpath(
                        photo_path, 
                        start=os.path.join(path_manager.base_dir, 'static')
                    )
                    
                    # Korrigiere Pfad-Separator
                    relative_path = relative_path.replace(os.sep, '/')
                    
                    project_images.append({
                        'angle': angle,
                        'path': relative_path
                    })
                except Exception as path_error:
                    logger.warning(f"Fehler bei Bildpfadverarbeitung: {path_error}")
        
        # Projekt anzeigen
        return render_template('projects/view.html', 
                               project=project, 
                               images=project_images)
    except Exception as e:
        logger.error(f"Fehler beim Anzeigen des Projekts {project_id}: {e}")
        return render_template('error.html', 
                               message=f"Fehler beim Anzeigen des Projekts: {str(e)}"), 500

@projects_bp.route('/image/<path:image_path>')
def serve_project_image(image_path):
    """
    Liefert ein Projektbild aus
    
    Args:
        image_path: Relativer Pfad zum Bild
    """
    try:
        # Bereinige den Bildpfad
        clean_image_path = sanitize_project_image_path(image_path)
        
        # Basis-Verzeichnis für statische Dateien
        static_dir = os.path.join(path_manager.base_dir, 'static')
        
        # Vollständiger Pfad zur Bilddatei
        full_path = os.path.normpath(os.path.join(static_dir, clean_image_path))
        
        # Sicherheitsüberprüfung: Stelle sicher, dass der Pfad innerhalb des statischen Verzeichnisses liegt
        if not full_path.startswith(static_dir):
            logger.warning(f"Ungültiger Bildpfad angefordert: {full_path}")
            abort(403)  # Verboten
        
        # Sicherstellen, dass die Datei existiert
        if not os.path.exists(full_path):
            logger.warning(f"Bild nicht gefunden: {full_path}")
            
            # Versuche alternative Pfade
            alternative_paths = [
                os.path.join(path_manager.base_dir, 'static', 'projects', clean_image_path),
                os.path.join(path_manager.base_dir, 'static', clean_image_path)
            ]
            
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    full_path = alt_path
                    break
            else:
                logger.error(f"Kein alternatives Bild gefunden für: {clean_image_path}")
                abort(404)
        
        # Verzeichnis und Dateiname extrahieren
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        # Bild senden
        return send_from_directory(directory, filename)
    except Exception as e:
        logger.error(f"Fehler beim Bereitstellen des Bildes: {e}")
        return render_template('error.html', 
                               message=f"Fehler beim Laden des Bildes: {str(e)}"), 500

@projects_bp.route('/<project_id>/delete', methods=['GET', 'POST'])
def delete_project(project_id):
    """
    Löscht ein Projekt
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt löschen
        success = project_manager.delete_project(project_id)
        
        if success:
            logger.info(f"Projekt erfolgreich gelöscht: {project_id}")
            return redirect(url_for('projects.projects_page'))
        else:
            logger.warning(f"Projekt konnte nicht gelöscht werden: {project_id}")
            return render_template('error.html', 
                                   message=f"Projekt {project_id} konnte nicht gelöscht werden."), 500
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Projekts {project_id}: {e}")
        return render_template('error.html', 
                               message=f"Fehler beim Löschen des Projekts: {str(e)}"), 500

# Zusätzliche Routen können hier hinzugefügt werden
