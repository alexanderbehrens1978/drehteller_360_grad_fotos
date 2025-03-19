#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/api/pannellum_routes.py
Routen für die Pannellum-Viewer-Funktionalität
"""

import os
import time
import json
import logging
from flask import jsonify, request, render_template, send_from_directory, current_app, abort
from app.blueprints.api import api_bp
from app.utils.secure_path import validate_project_id
from app.utils.pannellum_generator import pannellum_generator

# Logger einrichten
logger = logging.getLogger(__name__)

@api_bp.route('/pannellum/generate', methods=['POST'])
def generate_pannellum():
    """
    Generiert einen Pannellum-Viewer für ein Projekt
    
    POST-Parameter:
        project_id: ID des Projekts
    """
    try:
        data = request.get_json()
        
        if not data or 'project_id' not in data:
            return jsonify({
                "status": "error",
                "message": "Projekt-ID fehlt"
            }), 400
            
        project_id = data['project_id']
        
        # Projekt-ID validieren
        if not validate_project_id(project_id):
            return jsonify({
                "status": "error",
                "message": "Ungültige Projekt-ID"
            }), 400
            
        # Projekt laden
        from app.models.project import ProjectManager
        from app.utils.path_manager import PathManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        project = project_manager.get_project(project_id)
        
        if not project:
            return jsonify({
                "status": "error",
                "message": "Projekt nicht gefunden"
            }), 404
            
        # Viewer-Verzeichnis erstellen
        viewer_dir = os.path.join(project.path, 'viewer')
        os.makedirs(viewer_dir, exist_ok=True)
        
        # Viewer-Datei erstellen
        viewer_path = os.path.join(viewer_dir, 'index.html')
        result_path = pannellum_generator.generate_viewer_file(project, viewer_path)
        
        if not result_path:
            return jsonify({
                "status": "error",
                "message": "Fehler beim Generieren des Viewers"
            }), 500
            
        # Relative URL zum Viewer für die Antwort
        viewer_url = f"/pannellum/{project_id}/viewer"
        
        # Erfolgreich
        return jsonify({
            "status": "success",
            "message": "Pannellum-Viewer erfolgreich generiert",
            "viewer_url": viewer_url
        })
    except Exception as e:
        logger.error(f"Fehler bei der Pannellum-Generierung: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Fehler bei der Pannellum-Generierung: {str(e)}"
        }), 500

@api_bp.route('/pannellum/export/<project_id>', methods=['GET'])
def export_pannellum(project_id):
    """
    Exportiert den Pannellum-Viewer als ZIP-Datei
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt-ID validieren
        if not validate_project_id(project_id):
            return jsonify({
                "status": "error",
                "message": "Ungültige Projekt-ID"
            }), 400
            
        # Projekt laden
        from app.models.project import ProjectManager
        from app.utils.path_manager import PathManager
        import zipfile
        import io
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        project = project_manager.get_project(project_id)
        
        if not project:
            return jsonify({
                "status": "error",
                "message": "Projekt nicht gefunden"
            }), 404
            
        # Prüfen, ob der Viewer existiert
        viewer_dir = os.path.join(project.path, 'viewer')
        viewer_path = os.path.join(viewer_dir, 'index.html')
        
        if not os.path.exists(viewer_path):
            # Viewer generieren, falls er nicht existiert
            os.makedirs(viewer_dir, exist_ok=True)
            result_path = pannellum_generator.generate_viewer_file(project, viewer_path)
            
            if not result_path:
                return jsonify({
                    "status": "error",
                    "message": "Fehler beim Generieren des Viewers"
                }), 500
        
        # Temporäre ZIP-Datei erstellen
        timestamp = int(time.time())
        zip_filename = f"pannellum_{project_id}_{timestamp}.zip"
        exports_dir = os.path.join(path_manager.static_dir, 'exports')
        os.makedirs(exports_dir, exist_ok=True)
        zip_path = os.path.join(exports_dir, zip_filename)
        
        # Standalone-Viewer erstellen mit integrierten Bildern
        standalone_dir = os.path.join(viewer_dir, 'standalone')
        os.makedirs(standalone_dir, exist_ok=True)
        
        # Bilder in das Standalone-Verzeichnis kopieren
        import shutil
        for img in project.images:
            if isinstance(img, dict) and 'path' in img:
                src_path = os.path.join(project.path, img['path'])
                dst_path = os.path.join(standalone_dir, os.path.basename(img['path']))
                shutil.copy2(src_path, dst_path)
            elif isinstance(img, str):
                src_path = os.path.join(project.path, img)
                dst_path = os.path.join(standalone_dir, os.path.basename(img))
                shutil.copy2(src_path, dst_path)
        
        # Standalone-HTML mit relativen Pfaden erstellen
        standalone_html_path = os.path.join(standalone_dir, 'index.html')
        html = pannellum_generator.generate_viewer_html(project, base_url=".")
        
        with open(standalone_html_path, 'w') as f:
            f.write(html)
        
        # Alles in eine ZIP-Datei packen
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Viewer-Dateien hinzufügen (index.html)
            zipf.write(viewer_path, os.path.join('viewer', 'index.html'))
            
            # Standalone-Ordner mit seinen Inhalten hinzufügen
            for root, dirs, files in os.walk(standalone_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join('standalone', os.path.relpath(file_path, standalone_dir))
                    zipf.write(file_path, arcname)
            
            # README hinzufügen
            readme = f"""# Pannellum 360° Viewer für "{project.name}"

Dieser Export enthält zwei Versionen des 360° Viewers:

1. `viewer/index.html` - Benötigt eine Verbindung zum Webserver
2. `standalone/index.html` - Kann direkt im Browser geöffnet werden (enthält alle Bilder)

## Verwendung
- Öffnen Sie einfach die entsprechende HTML-Datei in einem Webbrowser
- Verwenden Sie die Pfeiltasten oder die Steuerelemente am unteren Bildrand, um zu navigieren
- Drücken Sie die Leertaste oder klicken Sie auf die Schaltfläche "Auto-Rotation", um die automatische Drehung zu starten/stoppen

Exportiert am: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""
            zipf.writestr('README.md', readme)
        
        # URL zur ZIP-Datei zurückgeben
        zip_url = f"/static/exports/{zip_filename}"
        
        return jsonify({
            "status": "success",
            "message": "Pannellum-Viewer erfolgreich exportiert",
            "download_url": zip_url
        })
    except Exception as e:
        logger.error(f"Fehler beim Exportieren des Pannellum-Viewers: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Fehler beim Exportieren des Pannellum-Viewers: {str(e)}"
        }), 500

# Füge diese Routen zum Blueprint hinzu:

# Blueprint für Pannellum
from flask import Blueprint
pannellum_bp = Blueprint('pannellum', __name__, url_prefix='/pannellum')

@pannellum_bp.route('/<project_id>/viewer')
def view_pannellum(project_id):
    """
    Zeigt den Pannellum-Viewer für ein Projekt an
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt-ID validieren
        if not validate_project_id(project_id):
            logger.warning(f"Ungültige Projekt-ID: {project_id}")
            abort(404)
            
        # Projekt laden
        from app.models.project import ProjectManager
        from app.utils.path_manager import PathManager
        
        path_manager = PathManager()
        project_manager = ProjectManager(path_manager.projects_dir)
        project = project_manager.get_project(project_id)
        
        if not project:
            logger.warning(f"Projekt nicht gefunden: {project_id}")
            abort(404)
            
        # Prüfen, ob der Viewer existiert
        viewer_dir = os.path.join(project.path, 'viewer')
        viewer_path = os.path.join(viewer_dir, 'index.html')
        
        if not os.path.exists(viewer_path):
            # Viewer generieren, falls er nicht existiert
            os.makedirs(viewer_dir, exist_ok=True)
            result_path = pannellum_generator.generate_viewer_file(project, viewer_path)
            
            if not result_path:
                logger.error(f"Fehler beim Generieren des Viewers für Projekt {project_id}")
                abort(500)
        
        # HTML-Datei direkt ausliefern
        return send_from_directory(viewer_dir, 'index.html')
    except Exception as e:
        logger.error(f"Fehler beim Anzeigen des Pannellum-Viewers: {str(e)}")
        abort(500)
