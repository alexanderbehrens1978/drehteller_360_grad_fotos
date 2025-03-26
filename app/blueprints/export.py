#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export.py
Blueprint für die Export-Funktionalität für 360-Grad-Ansichten
"""

import os
import logging
from flask import Blueprint, request, jsonify, send_file, current_app, render_template
from app.models.project import ProjectManager
from app.utils.export_utils import create_html_export, create_export_zip

# Logger einrichten
logger = logging.getLogger(__name__)

# Blueprint definieren
export_bp = Blueprint('export', __name__, url_prefix='/export')

@export_bp.route('/html/<project_id>', methods=['GET'])
def export_html(project_id):
    """Exportiert eine 360-Grad-Ansicht als eigenständige HTML-Datei"""
    try:
        # Projekt laden
        project_manager = ProjectManager(os.path.join(current_app.config['BASE_DIR'], 'static', 'projects'))
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Pfad zum Static-Ordner
        static_folder = os.path.join(current_app.config['BASE_DIR'], 'static')
        
        # HTML-Datei erstellen
        html_content = create_html_export(project, static_folder)
        
        # Temporären Pfad für die HTML-Datei erstellen
        export_dir = os.path.join(current_app.config['BASE_DIR'], 'static', 'temp')
        os.makedirs(export_dir, exist_ok=True)
        html_path = os.path.join(export_dir, f"{project_id}_export.html")
        
        # HTML-Datei speichern
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Datei zum Download senden
        return send_file(html_path, as_attachment=True, download_name=f"{project.name}_360_Ansicht.html", 
                        mimetype='text/html')
    
    except Exception as e:
        logger.error(f"Export fehlgeschlagen: {str(e)}")
        return jsonify({"error": f"Export fehlgeschlagen: {str(e)}"}), 500

@export_bp.route('/zip/<project_id>', methods=['GET'])
def export_zip(project_id):
    """Exportiert eine 360-Grad-Ansicht als ZIP-Archiv mit HTML und Bildern"""
    try:
        # Projekt laden
        project_manager = ProjectManager(os.path.join(current_app.config['BASE_DIR'], 'static', 'projects'))
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Pfad zum Static-Ordner
        static_folder = os.path.join(current_app.config['BASE_DIR'], 'static')
        
        # Temporären Pfad für die ZIP-Datei erstellen
        export_dir = os.path.join(current_app.config['BASE_DIR'], 'static', 'temp')
        os.makedirs(export_dir, exist_ok=True)
        
        # ZIP-Datei erstellen
        zip_path = create_export_zip(project, static_folder, export_dir)
        
        # Datei zum Download senden
        return send_file(zip_path, as_attachment=True, download_name=f"{project.name}_360_Ansicht.zip", 
                        mimetype='application/zip')
    
    except Exception as e:
        logger.error(f"Export fehlgeschlagen: {str(e)}")
        return jsonify({"error": f"Export fehlgeschlagen: {str(e)}"}), 500

@export_bp.route('/options/<project_id>', methods=['GET'])
def export_options(project_id):
    """Zeigt die Exportoptionen für ein Projekt an"""
    try:
        # Projekt laden
        project_manager = ProjectManager(os.path.join(current_app.config['BASE_DIR'], 'static', 'projects'))
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Aktuelles Jahr für das Copyright
        import datetime
        current_year = datetime.datetime.now().year
        
        # Exportoptionen anzeigen
        return render_template('export_options.html', project=project, current_year=current_year)
    
    except Exception as e:
        logger.error(f"Fehler beim Laden der Exportoptionen: {str(e)}")
        return jsonify({"error": f"Fehler: {str(e)}"}), 500
