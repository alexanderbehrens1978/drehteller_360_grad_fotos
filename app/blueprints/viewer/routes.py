"""
app/blueprints/viewer/routes.py
Enthält die Routen für den 360° Viewer
"""

import os
import json
import logging
from flask import render_template, request, redirect, url_for, jsonify, abort, send_file, current_app
from app.blueprints.viewer import viewer_bp
from app.models.project import ProjectManager
from app.utils.path_manager import PathManager
from app.utils.secure_path import validate_project_id
from datetime import datetime

# Logger einrichten
logger = logging.getLogger(__name__)

# Path Manager erstellen
path_manager = PathManager()

# Projekt-Manager erstellen
project_manager = ProjectManager(path_manager.projects_dir)

@viewer_bp.route('/')
def viewer_overview():
    """Zeigt eine Übersicht aller Projekte und den 360° Viewer für ein ausgewähltes Projekt"""
    try:
        # Projekte aus dem ProjectManager laden
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
                return render_template('viewer/cloudimage_viewer.html', project=selected_project)
        
        # Ansonsten die Übersichtsseite anzeigen
        return render_template('viewer/overview.html', projects=projects)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Viewer-Übersicht: {str(e)}")
        return render_template('error.html', message=f"Fehler beim Laden der Viewer-Übersicht: {str(e)}"), 500



@viewer_bp.route('/cloudimage')
def cloudimage_viewer():
    """Zeigt den CloudImage 360° Viewer für ein Projekt"""
    logger.warning("=== CLOUDIMAGE VIEWER ROUTE CALLED ===")
    try:
        # Projekt-ID aus URL-Parameter lesen
        project_id = request.args.get('project')
        print(f"DEBUG: Received project_id={project_id}")  # Debug-Ausgabe
        if not project_id:
            return redirect(url_for('viewer.viewer_overview'))
        
        if not validate_project_id(project_id):
            logger.warning(f"Ungültige Projekt-ID: {project_id}")
            abort(404)
        
        # Projekt laden
        project = project_manager.get_project(project_id)
        if not project:
            return render_template('error.html', message="Projekt nicht gefunden"), 404
        
        # Prüfen, ob spezifische Bilder ausgewählt wurden
        selected_images = request.args.get('images')
        if selected_images:
            image_paths = selected_images.split(',')
            # Nur die angegebenen Bilder behalten
            filtered_images = []
            for img in project.images:
                if img['path'] in image_paths:
                    filtered_images.append(img)
            
            # Temporäre Kopie der Bilder setzen
            project.images = filtered_images
        
        return render_template('viewer/cloudimage_viewer.html', project=project)
    except Exception as e:
        logger.error(f"Fehler beim Laden des CloudImage Viewers: {str(e)}")
        return render_template('error.html', message=f"Fehler beim Laden des CloudImage Viewers: {str(e)}"), 500


def create_embed_code(project, selected_images=None, base_url=None):
    """
    Erstellt einen einbettbaren HTML-Code für den 360° Viewer
    
    Args:
        project: Das Projekt-Objekt
        selected_images: Optional Liste der ausgewählten Bildpfade
        base_url: Die Basis-URL der Anwendung
        
    Returns:
        String mit HTML-Code zum Einbetten des Viewers
    """
    if not base_url:
        base_url = request.host_url.rstrip('/')
    
    # Basis-URL für den Viewer
    viewer_url = f"{base_url}/viewer/cloudimage?project={project.id}"
    
    # Wenn Bilder explizit ausgewählt wurden, diese hinzufügen
    if selected_images:
        viewer_url += f"&images={','.join(selected_images)}"
    
    # CSS und JS URLs
    css_url = f"{base_url}/static/css/styles.css"
    cloudimage_css_url = f"{base_url}/static/css/cloudimage-viewer.css"
    js_url = f"{base_url}/static/js/cloudimage-viewer.js"
    
    # HTML Code zum Einbetten
    embed_code = f"""<!-- 360° Produktansicht - Drehteller Steuerung -->
<div style="width: 100%; max-width: 800px; margin: 0 auto;">
    <iframe 
        src="{viewer_url}&embed=true" 
        style="width: 100%; height: 600px; border: none; overflow: hidden;" 
        title="{project.name} - 360° Ansicht"
        allowfullscreen>
    </iframe>
</div>
<div style="text-align: center; font-size: 12px; margin-top: 5px;">
    Powered by <a href="{base_url}" target="_blank">360° Drehteller Steuerung</a>
</div>"""
    
    return embed_code


@viewer_bp.route('/export', methods=['POST'])
def export_viewer():
    """Exportiert die ausgewählten Bilder für den Viewer"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "Keine Daten empfangen"}), 400
        
        project_id = data.get('project_id')
        selected_images = data.get('selected_images', [])
        
        if not project_id or not validate_project_id(project_id):
            return jsonify({"status": "error", "message": "Ungültige Projekt-ID"}), 400
        
        # Projekt laden
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({"status": "error", "message": "Projekt nicht gefunden"}), 404
        
        # Export-Verzeichnis erstellen
        import tempfile
        import shutil
        import zipfile
        
        # Temporäres Verzeichnis für den Export erstellen
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Unterverzeichnisse erstellen
            os.makedirs(os.path.join(temp_dir, 'images'), exist_ok=True)
            os.makedirs(os.path.join(temp_dir, 'css'), exist_ok=True)
            os.makedirs(os.path.join(temp_dir, 'js'), exist_ok=True)
            
            # CSS und JS Dateien kopieren
            shutil.copy2(os.path.join(current_app.static_folder, 'css', 'cloudimage-viewer.css'), 
                        os.path.join(temp_dir, 'css'))
            shutil.copy2(os.path.join(current_app.static_folder, 'js', 'cloudimage-viewer.js'), 
                        os.path.join(temp_dir, 'js'))
            
            # Bilder kopieren
            images_to_export = selected_images or [img['path'] for img in project.images]
            images_path = os.path.join(current_app.static_folder, 'projects', project.id, 'images')
            
            for img_path in images_to_export:
                full_path = os.path.join(images_path, os.path.basename(img_path))
                if os.path.exists(full_path):
                    shutil.copy2(full_path, os.path.join(temp_dir, 'images'))
            
            # Standalone HTML erstellen
            standalone_html = create_standalone_viewer(project, images_to_export)
            
            # HTML-Datei im temporären Verzeichnis speichern
            with open(os.path.join(temp_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(standalone_html)
            
            # ZIP-Datei erstellen
            zip_filename = os.path.join(temp_dir, f"{project.name}_360_viewer.zip")
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.zip'):
                            continue
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            
            # ZIP-Datei senden
            return send_file(
                zip_filename,
                mimetype='application/zip',
                as_attachment=True,
                download_name=f"{project.name}_360_viewer.zip"
            )
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Exports: {str(e)}")
            # Aufräumen
            shutil.rmtree(temp_dir, ignore_errors=True)
            return jsonify({"status": "error", "message": f"Export-Fehler: {str(e)}"}), 500
        
        finally:
            # Aufräumen (falls noch nicht geschehen)
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        logger.error(f"Fehler beim Exportieren des Viewers: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


def create_standalone_viewer(project, image_paths):
    """
    Erstellt eine eigenständige HTML-Datei für den 360° Viewer
    
    Args:
        project: Das Projekt-Objekt
        image_paths: Liste der Bildpfade
        
    Returns:
        String mit HTML-Code für einen eigenständigen Viewer
    """
    # Relative Pfade für die Ressourcen
    css_path = "css/cloudimage-viewer.css"
    js_path = "js/cloudimage-viewer.js"
    
    # HTML-Template für eigenständigen Viewer
    html_template = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project.name} - 360° Ansicht</title>
    <link rel="stylesheet" href="{css_path}">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        footer {{
            text-align: center;
            margin-top: 30px;
            color: #777;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{project.name}</h1>
            <p>360° Ansicht des Produkts</p>
        </header>
        
        <main>
            <!-- 360° Viewer Container -->
            <div id="viewer-container" class="viewer-container">
                <!-- Bottom Circle Indicator -->
                <div class="bottom-circle"></div>
                
                <div id="viewer" class="cloudimage-360" 
                     data-folder="images/"
                     data-filename-pattern="image_{{index}}.jpg"
                     data-amount="{len(image_paths)}"
                     data-spin-reverse="false"
                     data-full-screen="true"
                     data-magnifier="true"
                     data-ratio="1">
                    <!-- Bilder direkt anzeigen -->
                    {generate_image_tags(image_paths)}
                </div>
                
                <!-- Magnifier-Glas -->
                <div class="img-magnifier-glass" style="display: none; position: absolute; border: 2px solid #ccc; border-radius: 50%; cursor: none; width: 150px; height: 150px; background-repeat: no-repeat;"></div>
                
                <!-- Viewer Steuerelemente -->
                <div class="viewer-controls">
                    <button id="play-btn" class="control-btn" title="Wiedergabe starten/pausieren">
                        <span id="play-icon">▶</span>
                    </button>
                    <button id="fullscreen-btn" class="control-btn" title="Vollbildmodus">
                        <span>⛶</span>
                    </button>
                    <button id="magnifier-btn" class="control-btn" title="Lupe aktivieren">
                        <span>🔍</span>
                    </button>
                </div>
            </div>
        </main>
        
        <footer>
            <p>&copy; {datetime.now().year} 360° Drehteller Steuerung. Alle Rechte vorbehalten.</p>
        </footer>
    </div>
    
    <script src="{js_path}"></script>
</body>
</html>"""
    
    return html_template


def generate_image_tags(image_paths):
    """Generiert HTML-Tags für die Bilder"""
    image_tags = []
    for i, img_path in enumerate(image_paths):
        is_first = i == 0
        display_style = "" if is_first else "display: none;"
        active_class = "active" if is_first else ""
        
        img_tag = f"""<img class="product-image {active_class}" 
                     src="images/{os.path.basename(img_path)}" 
                     alt="Bild {i+1} von {len(image_paths)}"
                     style="{display_style}">"""
        image_tags.append(img_tag)
    
    return "\n                    ".join(image_tags)


@viewer_bp.route('/settings', methods=['POST'])
def save_settings():
    """Speichert Viewer-Einstellungen für ein Projekt"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "Keine Daten empfangen"}), 400
        
        project_id = data.get('project_id')
        settings_name = data.get('name')
        settings = data.get('settings')
        
        if not project_id or not validate_project_id(project_id) or not settings_name or not settings:
            return jsonify({"status": "error", "message": "Ungültige Daten"}), 400
        
        # Projekt laden
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({"status": "error", "message": "Projekt nicht gefunden"}), 404
        
        # Pfad erstellen, falls nicht vorhanden
        settings_dir = os.path.join(path_manager.projects_dir, project_id, 'settings')
        os.makedirs(settings_dir, exist_ok=True)
        
        # Einstellungen speichern
        settings_file = os.path.join(settings_dir, f"{settings_name}.json")
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        
        return jsonify({
            "status": "success",
            "message": f"Einstellungen '{settings_name}' gespeichert"
        })
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Einstellungen: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@viewer_bp.route('/settings/<project_id>', methods=['GET'])
def get_settings_list(project_id):
    """Gibt eine Liste aller gespeicherten Einstellungen für ein Projekt zurück"""
    try:
        if not validate_project_id(project_id):
            return jsonify({"status": "error", "message": "Ungültige Projekt-ID"}), 400
        
        # Projekt laden
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({"status": "error", "message": "Projekt nicht gefunden"}), 404
        
        # Einstellungen-Verzeichnis
        settings_dir = os.path.join(path_manager.projects_dir, project_id, 'settings')
        
        # Wenn Verzeichnis nicht existiert, leere Liste zurückgeben
        if not os.path.exists(settings_dir):
            return jsonify({
                "status": "success",
                "settings": []
            })
        
        # Liste der gespeicherten Einstellungen erstellen
        settings_files = [f for f in os.listdir(settings_dir) if f.endswith('.json')]
        settings_list = []
        
        for filename in settings_files:
            settings_name = os.path.splitext(filename)[0]
            settings_path = os.path.join(settings_dir, filename)
            
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings_data = json.load(f)
                
                # Füge zur Liste hinzu
                settings_list.append({
                    "name": settings_name,
                    "data": settings_data
                })
            except Exception as e:
                logger.warning(f"Fehler beim Laden der Einstellungen '{settings_name}': {str(e)}")
        
        return jsonify({
            "status": "success",
            "settings": settings_list
        })
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Einstellungen: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@viewer_bp.route('/settings/<project_id>/<settings_name>', methods=['GET'])
def get_settings(project_id, settings_name):
    """Lädt bestimmte Einstellungen für ein Projekt"""
    try:
        if not validate_project_id(project_id):
            return jsonify({"status": "error", "message": "Ungültige Projekt-ID"}), 400
        
        # Einstellungsdatei
        settings_file = os.path.join(path_manager.projects_dir, project_id, 'settings', f"{settings_name}.json")
        
        if not os.path.exists(settings_file):
            return jsonify({"status": "error", "message": f"Einstellungen '{settings_name}' nicht gefunden"}), 404
        
        # Einstellungen laden
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        return jsonify({
            "status": "success",
            "name": settings_name,
            "settings": settings
        })
    except Exception as e:
        logger.error(f"Fehler beim Laden der Einstellungen: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@viewer_bp.route('/settings/<project_id>/<settings_name>', methods=['DELETE'])
def delete_settings(project_id, settings_name):
    """Löscht bestimmte Einstellungen für ein Projekt"""
    try:
        if not validate_project_id(project_id):
            return jsonify({"status": "error", "message": "Ungültige Projekt-ID"}), 400
        
        # Einstellungsdatei
        settings_file = os.path.join(path_manager.projects_dir, project_id, 'settings', f"{settings_name}.json")
        
        if not os.path.exists(settings_file):
            return jsonify({"status": "error", "message": f"Einstellungen '{settings_name}' nicht gefunden"}), 404
        
        # Einstellungen löschen
        os.remove(settings_file)
        
        return jsonify({
            "status": "success",
            "message": f"Einstellungen '{settings_name}' gelöscht"
        })
    except Exception as e:
        logger.error(f"Fehler beim Löschen der Einstellungen: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
