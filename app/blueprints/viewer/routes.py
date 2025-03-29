"""
app/blueprints/viewer/routes.py
Enthält die Routen für den 360° Viewer
"""

import os
import json
import logging
from flask import render_template, request, redirect, url_for, jsonify, abort, send_file, g, flash
from app.blueprints.viewer import viewer_bp
from app.models.project import ProjectManager
from app.utils.path_manager import PathManager
from app.utils.secure_path import validate_project_id
from functools import wraps

# Logger einrichten
logger = logging.getLogger(__name__)

# Path Manager erstellen
path_manager = PathManager()

# Projekt-Manager erstellen
project_manager = ProjectManager(path_manager.projects_dir)

def after_this_request(func):
    if not hasattr(g, 'call_after_request'):
        g.call_after_request = []
    g.call_after_request.append(func)
    return func

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




@viewer_bp.route('/export/<project_id>', methods=['GET'])
def export_viewer(project_id):
    """Exportiert den 360° Viewer mit allen Bildern als ZIP-Datei"""
    
    # Validierung der Projekt-ID
    if not validate_project_id(project_id):
        return render_template('error.html', message="Ungültige Projekt-ID"), 400
    
    # Viewer-Einstellungen aus der URL lesen
    viewer_settings = {}
    settings_param = request.args.get('settings')
    if settings_param:
        try:
            import json
            viewer_settings = json.loads(settings_param)
            logger.info(f"Viewer-Einstellungen übernommen: {viewer_settings}")
        except Exception as e:
            logger.error(f"Fehler beim Parsen der Viewer-Einstellungen: {str(e)}")
    
    # Projekt laden
    from app.models.project import ProjectManager
    # Path Manager nutzen, um den korrekten Pfad zu erhalten
    projects_dir = path_manager.projects_dir
    project_manager = ProjectManager(projects_dir)
    
    project = project_manager.get_project(project_id)
    if not project:
        return render_template('error.html', message="Projekt nicht gefunden"), 404

    try:
        # Benötigte Imports
        import tempfile, shutil, zipfile, json, os, time
        from flask import send_file, current_app, redirect, url_for
        
        # Debug-Ausgabe
        logger.info(f"Export für Projekt {project_id} gestartet")
        
        # Temporäres Verzeichnis für den Export erstellen
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Temporäres Verzeichnis erstellt: {temp_dir}")
        
        # Unterverzeichnisse erstellen
        images_dir = os.path.join(temp_dir, 'images')
        js_dir = os.path.join(temp_dir, 'js')
        css_dir = os.path.join(temp_dir, 'css')
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(js_dir, exist_ok=True)
        os.makedirs(css_dir, exist_ok=True)
        
        logger.info(f"Unterverzeichnisse erstellt")

        # Bilder kopieren und Bildliste erstellen
        image_list = []
        logger.info(f"Beginne mit dem Kopieren von {len(project.images)} Bildern")
        
        for i, image in enumerate(project.images):
            # Korrekten Pfad zum Bild ermitteln
            source_path = os.path.join(project.path, image['path'])
            # Umbenennen, um Sequenz sicherzustellen
            dest_filename = f"image-{i+1}.jpg"
            dest_path = os.path.join(images_dir, dest_filename)
            
            logger.info(f"Kopiere Bild {i+1}: {source_path} -> {dest_path}")
            try:
                shutil.copy2(source_path, dest_path)
                # Wichtig: Relativer Pfad mit ./images/ um sicherzustellen, dass der Browser die Bilder findet
                image_list.append(f"./images/{dest_filename}")
            except Exception as img_error:
                logger.error(f"Fehler beim Kopieren von Bild {source_path}: {str(img_error)}")
        
        # JavaScript-Dateien kopieren
        js_source = os.path.join(current_app.root_path, '..', 'static', 'js', 'js-cloudimage-360-view.min.js')
        js_dest = os.path.join(js_dir, 'js-cloudimage-360-view.min.js')
        logger.info(f"Kopiere JS-Datei: {js_source} -> {js_dest}")
        shutil.copy2(js_source, js_dest)

        # CSS-Dateien kopieren (falls vorhanden)
        css_source = os.path.join(current_app.root_path, '..', 'static', 'css', 'cloudimage-viewer.css')
        css_dest = os.path.join(css_dir, 'cloudimage-viewer.css')
        if os.path.exists(css_source):
            logger.info(f"Kopiere CSS-Datei: {css_source} -> {css_dest}")
            shutil.copy2(css_source, css_dest)
        else:
            logger.warning(f"CSS-Datei nicht gefunden: {css_source}")

        # HTML-Template rendern
        logger.info(f"Rendere HTML-Template mit {len(image_list)} Bildern")
        
        # Korrekte Template Variablen vorbereiten
        template_vars = {
            'project': project,
            'image_list': image_list,  # Diese Liste enthält bereits die richtigen relativen Pfade
            'viewer_settings': viewer_settings
        }
        
        html_content = render_template(
            'viewer/export_template.html',
            **template_vars
        )
        html_path = os.path.join(temp_dir, 'index.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"HTML-Datei geschrieben: {html_path}")

        # Stellen Sie sicher, dass das Downloads-Verzeichnis existiert
        downloads_dir = os.path.join(current_app.root_path, '..', 'static', 'downloads')
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir, exist_ok=True)
            logger.info(f"Downloads-Verzeichnis erstellt: {downloads_dir}")

        # Eindeutiger Name für ZIP-Datei mit Zeitstempel
        timestamp = int(time.time())
        safe_name = project.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        zip_filename = f"{safe_name}_{timestamp}_360_viewer.zip"
        zip_path = os.path.join(downloads_dir, zip_filename)
        
        # ZIP-Datei erstellen
        logger.info(f"Erstelle ZIP-Datei: {zip_path}")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Alle Dateien hinzufügen
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, temp_dir)
                    logger.info(f"Füge Datei zur ZIP hinzu: {rel_path}")
                    zipf.write(file_path, rel_path)
        
        logger.info(f"ZIP-Datei fertig erstellt: {zip_path}")
        
        # Temporäres Verzeichnis aufräumen
        try:
            logger.info(f"Lösche temporäres Verzeichnis: {temp_dir}")
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error(f"Fehler beim Aufräumen: {str(e)}")
        
        # Dateigröße berechnen
        filesize = round(os.path.getsize(zip_path) / 1024, 1)  # KB
        
        # URL für den Download
        download_url = f"/static/downloads/{zip_filename}"
        
        # Zur Download-Seite weiterleiten
        logger.info(f"Weiterleitung zur Download-Seite für Projekt {project_id}")
        
        # Relativ zum Blueprint weiterleiten
        return redirect(url_for('.show_downloads', project_id=project_id), code=302)
    except Exception as e:
        # Im Fehlerfall aufräumen
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        
        logger.error(f"Fehler beim Exportieren des Viewers: {str(e)}", exc_info=True)
        return render_template('error.html', message=f"Fehler beim Exportieren des Viewers: {str(e)}"), 500

@viewer_bp.route('/export_viewer', methods=['POST'])
def export_viewer_json():
    """Exportiert den 360°-Viewer für die Einbettung in andere Websites"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"status": "error", "message": "Keine Daten empfangen"}), 400
        
        project_id = data.get('project_id')
        filename = data.get('filename', 'viewer-export')
        options = data.get('options', 'html-only')
        
        if not project_id or not validate_project_id(project_id):
            return jsonify({"status": "error", "message": "Ungültige Projekt-ID"}), 400
        
        # Projekt laden
        project = project_manager.get_project(project_id)
        if not project:
            return jsonify({"status": "error", "message": "Projekt nicht gefunden"}), 404
        
        # Einbettungscode generieren
        image_count = len(project.images) if project.images else 0
        
        embed_code = f"""<!-- CloudImage 360° Viewer -->
<div class="cloudimage-360" 
     data-folder="/static/projects/{project_id}/" 
     data-filename="{{index}}.jpg" 
     data-amount="{image_count}"
     data-bottom-circle="true"
     data-keys="true"
     data-drag-speed="150"
     data-autoplay="true">
</div>
<script src="/static/js/js-cloudimage-360-view.min.js"></script>"""
        
        # Je nach Option unterschiedliche Aktionen ausführen
        result = {
            "status": "success",
            "message": "Export erfolgreich",
            "embed_code": embed_code
        }
        
        if options == 'full-package':
            # Hier könnte der Code zum Erstellen eines Zip-Pakets implementiert werden
            # Da dies komplexer ist, stellen wir zunächst nur den Einbettungscode bereit
            result["message"] = "Einbettungscode wurde generiert. Vollständiges Paket noch nicht implementiert."
            # Sicherstellen, dass kein None-Wert in der Antwort enthalten ist
            result["download_url"] = ""
        
        # Sicherstellen, dass result keine None-Werte enthält
        for key in list(result.keys()):
            if result[key] is None:
                result[key] = ""
                
        return jsonify(result)
    except Exception as e:
        logger.error(f"Fehler beim Exportieren des Viewers: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@viewer_bp.route('/downloads/<project_id>', methods=['GET'])
def show_downloads(project_id):
    """Zeigt eine Liste aller vorherigen Exporte für ein Projekt an"""
    if not validate_project_id(project_id):
        return render_template('error.html', message="Ungültige Projekt-ID"), 400

    # Projekt laden
    project = project_manager.get_project(project_id)
    if not project:
        return render_template('error.html', message="Projekt nicht gefunden"), 404
    
    try:
        import os
        from flask import current_app
        
        # Download-Verzeichnis
        downloads_dir = os.path.join(current_app.root_path, '..', 'static', 'downloads')
        if not os.path.exists(downloads_dir):
            os.makedirs(downloads_dir, exist_ok=True)
        
        # Projektname (für Filter)
        safe_name = project.name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        
        # Alle ZIP-Dateien im Download-Verzeichnis finden, die zu diesem Projekt gehören
        downloads = []
        for filename in os.listdir(downloads_dir):
            if filename.startswith(safe_name) and filename.endswith('_360_viewer.zip'):
                file_path = os.path.join(downloads_dir, filename)
                file_size = round(os.path.getsize(file_path) / 1024, 1)  # KB
                file_date = os.path.getmtime(file_path)
                
                downloads.append({
                    'filename': filename,
                    'size': file_size,
                    'date': file_date,
                    'url': f'/static/downloads/{filename}'
                })
        
        # Nach Datum sortieren (neueste zuerst)
        downloads.sort(key=lambda x: x['date'], reverse=True)
        
        return render_template(
            'viewer/downloads.html',
            project=project,
            downloads=downloads
        )
    
    except Exception as e:
        logger.error(f"Fehler beim Anzeigen der Downloads: {str(e)}", exc_info=True)
        return render_template('error.html', message=f"Fehler beim Anzeigen der Downloads: {str(e)}"), 500

@viewer_bp.route('/delete_export/<project_id>/<filename>', methods=['GET'])
def delete_export(project_id, filename):
    """Löscht einen bestimmten Export"""
    if not validate_project_id(project_id):
        return render_template('error.html', message="Ungültige Projekt-ID"), 400
    
    try:
        logger.info(f"Löschen des Exports: project_id={project_id}, filename={filename}")
        
        # Pfad zur Export-Datei
        downloads_dir = path_manager.get_downloads_dir()
        file_path = os.path.join(downloads_dir, filename)
        
        # Überprüfe, ob die Datei existiert
        if not os.path.exists(file_path):
            logger.warning(f"Datei nicht gefunden: {file_path}")
            return render_template('error.html', message="Die angegebene Datei wurde nicht gefunden"), 404
        
        # Datei löschen
        os.remove(file_path)
        logger.info(f"Export gelöscht: {file_path}")
        
        # Erfolgsmeldung hinzufügen (verwendet Flash-Nachrichten)
        flash('Export wurde erfolgreich gelöscht.', 'success')
        
        # Zurück zur Downloads-Seite
        return redirect(url_for('.show_downloads', project_id=project_id))
        
    except Exception as e:
        logger.error(f"Fehler beim Löschen des Exports: {str(e)}", exc_info=True)
        flash(f"Fehler beim Löschen des Exports: {str(e)}", 'danger')
        return redirect(url_for('.show_downloads', project_id=project_id))
