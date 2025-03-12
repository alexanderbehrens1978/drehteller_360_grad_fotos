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
import zipfile
import io
import shutil
from flask import render_template, request, jsonify, redirect, url_for, send_from_directory, current_app, send_file, abort
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
        try:
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
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Projekts: {e}")
            return render_template('project_create.html', error=str(e))
    
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

@projects_bp.route('/<project_id>/viewer')
def view_project_360(project_id):
    """
    Zeigt die 360° Ansicht eines Projekts an
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt laden
        project = project_manager.get_project(project_id)
        
        if not project:
            # Wenn das Projekt nicht gefunden wurde, zur Projektliste weiterleiten
            return redirect(url_for('projects.projects_page'))
        
        # Projekt-Daten für JavaScript serialisieren
        project_json = json.dumps(project.to_dict())
        
        # 360° Viewer anzeigen
        return render_template('project_viewer.html', project=project, project_json=project_json)
    except Exception as e:
        logger.error(f"Fehler beim Anzeigen des Projekt-Viewers: {e}")
        return render_template('error.html', message=f"Fehler beim Laden des Viewers: {str(e)}")

@projects_bp.route('/<project_id>/viewers')
def view_project_all_viewers(project_id):
    """
    Zeigt die 360° Ansicht eines Projekts mit allen verfügbaren Viewern an
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt laden
        project = project_manager.get_project(project_id)
        
        if not project:
            # Wenn das Projekt nicht gefunden wurde, zur Projektliste weiterleiten
            return redirect(url_for('projects.projects_page'))
            
        # Projekt-Daten für JavaScript serialisieren
        project_json = json.dumps(project.to_dict())
        
        # Finde die Session mit den meisten Bildern
        best_session = None
        max_photos = 0
        
        for session in project.sessions:
            if len(session.photos) > max_photos:
                max_photos = len(session.photos)
                best_session = session
                
        if not best_session:
            return render_template('error.html', message="Keine Session mit Fotos im Projekt gefunden.")
            
        # Bereite die Bildpfade für die Viewer vor
        image_paths = []
        for angle in sorted([float(a) for a in best_session.photos.keys()]):
            photo_path = best_session.photos[str(angle)]
            if os.path.exists(photo_path):
                rel_path = f"/projects/image/{project.id}/{os.path.relpath(photo_path, project.path)}"
                image_paths.append(rel_path)
        
        # 360° Viewer mit allen Bibliotheken anzeigen
        return render_template('project_all_viewers.html', 
                              project=project, 
                              project_json=project_json,
                              image_paths=image_paths)
    except Exception as e:
        logger.error(f"Fehler beim Anzeigen der Viewer-Vergleichsseite: {e}")
        return render_template('error.html', message=f"Fehler beim Laden der Viewer: {str(e)}")

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
        try:
            # Projektdaten aus dem Formular holen
            project.name = request.form.get('name', project.name)
            project.description = request.form.get('description', project.description)
            project.angle_step = int(request.form.get('angle_step', project.angle_step))
            
            # Projekt speichern
            project_manager.save_project(project)
            
            # Zur Projektseite weiterleiten
            return redirect(url_for('projects.view_project', project_id=project.id))
        except Exception as e:
            logger.error(f"Fehler beim Bearbeiten des Projekts: {e}")
            return render_template('project_edit.html', project=project, error=str(e))
    
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
            # Rotation-Modus aus der Konfiguration holen
            from app.utils.config_manager import config_manager
            rotation_mode = config_manager.get('rotation.mode', 'angle')
            
            if rotation_mode == 'time':
                # Zeit-Modus
                rotation_time_ms = config_manager.get('rotation.time_ms', 5000)
                arduino_controller.rotate_for_duration(rotation_time_ms)
            else:
                # Winkelschritt-Modus
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
            # Fehlermeldung, da kein Kamera-Controller verfügbar ist
            return jsonify({"error": "Kamera-Controller nicht verfügbar"}), 500
        
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

@projects_bp.route('/<project_id>/export', methods=['POST'])
def export_project(project_id):
    """
    Exportiert ein Projekt für externe Verwendung
    
    Args:
        project_id: ID des Projekts
    """
    try:
        # Projekt laden
        project = project_manager.get_project(project_id)
        
        if not project:
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Parameter aus der Anfrage holen
        if not request.is_json:
            return jsonify({"error": "Keine JSON-Daten empfangen"}), 400
            
        data = request.json
        export_format = data.get('format', 'html')
        session_id = data.get('sessionId')
        
        # Viewer-Optionen
        viewers = data.get('viewers', ['default'])
        
        # Session finden
        session = None
        if session_id:
            for s in project.sessions:
                if s.id == session_id:
                    session = s
                    break
        
        if not session and project.sessions:
            # Wenn keine Session angegeben oder gefunden wurde, die erste verwenden
            session = project.sessions[0]
        
        if not session:
            return jsonify({"error": "Keine Session im Projekt gefunden"}), 404
        
        # Exportverzeichnis erstellen
        export_dir = os.path.join(path_manager.temp_dir, f"export_{project_id}_{int(time.time())}")
        os.makedirs(export_dir, exist_ok=True)
        
        # Bilder für den Export vorbereiten
        image_files = []
        for angle, path in session.photos.items():
            if os.path.exists(path):
                dest_path = os.path.join(export_dir, f"image_{int(float(angle)):03d}.jpg")
                shutil.copy(path, dest_path)
                image_files.append(f"image_{int(float(angle)):03d}.jpg")
        
        # Export basierend auf dem Format erstellen
        if export_format == 'html':
            # HTML-Export
            html_file = os.path.join(export_dir, 'index.html')
            
            with open(html_file, 'w') as f:
                # Je nach Viewer-Auswahl verschiedene HTML-Dateien generieren
                if 'pannellum' in viewers:
                    f.write(generate_pannellum_html(project, image_files))
                elif 'photosphere' in viewers:
                    f.write(generate_photosphere_html(project, image_files))
                elif 'marzipano' in viewers:
                    f.write(generate_marzipano_html(project, image_files))
                else:
                    f.write(generate_standalone_html(project, image_files))
            
            # ZIP-Datei erstellen
            zip_filename = f"{project.name.replace(' ', '_')}_360_viewer.zip"
            zip_path = os.path.join(path_manager.temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # HTML-Datei hinzufügen
                zipf.write(html_file, 'index.html')
                
                # Bilder hinzufügen
                for img in image_files:
                    img_path = os.path.join(export_dir, img)
                    zipf.write(img_path, img)
                
                # CSS und JS-Dateien hinzufügen
                if 'default' in viewers:
                    js_content = generate_viewer_js()
                    css_content = generate_viewer_css()
                    
                    zipf.writestr('viewer.js', js_content)
                    zipf.writestr('viewer.css', css_content)
                
                # Viewer-spezifische Dateien hinzufügen
                if 'pannellum' in viewers:
                    zipf.writestr('pannellum.js', generate_pannellum_js())
                
                if 'photosphere' in viewers:
                    zipf.writestr('photo-sphere-viewer.js', generate_photosphere_js())
                
                if 'marzipano' in viewers:
                    zipf.writestr('marzipano.js', generate_marzipano_js())
            
            # Temporäre Dateien bereinigen
            shutil.rmtree(export_dir)
            
            # Download-URL zurückgeben
            return jsonify({
                "status": "success",
                "downloadUrl": f"/projects/download/{zip_filename}"
            })
            
        elif export_format == 'wordpress':
            # WordPress-Export
            shortcode = generate_wordpress_shortcode(project, image_files)
            
            # Datei mit Shortcode erstellen
            shortcode_file = os.path.join(export_dir, f"{project.name.replace(' ', '_')}_wordpress.txt")
            with open(shortcode_file, 'w') as f:
                f.write(shortcode)
            
            # ZIP-Datei mit Bildern und Shortcode erstellen
            zip_filename = f"{project.name.replace(' ', '_')}_wordpress.zip"
            zip_path = os.path.join(path_manager.temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # Shortcode-Datei hinzufügen
                zipf.write(shortcode_file, os.path.basename(shortcode_file))
                
                # Bilder hinzufügen
                for img in image_files:
                    img_path = os.path.join(export_dir, img)
                    zipf.write(img_path, img)
            
            # Temporäre Dateien bereinigen
            shutil.rmtree(export_dir)
            
            # Download-URL zurückgeben
            return jsonify({
                "status": "success",
                "downloadUrl": f"/projects/download/{zip_filename}"
            })
            
        elif export_format in ['shopify', 'prestashop']:
            # Shopify/PrestaShop-Export
            zip_filename = f"{project.name.replace(' ', '_')}_{export_format}.zip"
            zip_path = os.path.join(path_manager.temp_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # HTML-Snippet erstellen
                html_snippet = generate_ecommerce_snippet(project, image_files, export_format)
                zipf.writestr('integration.html', html_snippet)
                
                # JS und CSS hinzufügen
                js_content = generate_viewer_js()
                css_content = generate_viewer_css()
                
                zipf.writestr('viewer.js', js_content)
                zipf.writestr('viewer.css', css_content)
                
                # Bilder hinzufügen
                for img in image_files:
                    img_path = os.path.join(export_dir, img)
                    zipf.write(img_path, f"images/{img}")
                
                # Anleitung hinzufügen
                instructions = generate_integration_instructions(export_format)
                zipf.writestr('README.txt', instructions)
            
            # Temporäre Dateien bereinigen
            shutil.rmtree(export_dir)
            
            # Download-URL zurückgeben
            return jsonify({
                "status": "success",
                "downloadUrl": f"/projects/download/{zip_filename}"
            })
        
        else:
            return jsonify({"error": f"Unbekanntes Export-Format: {export_format}"}), 400
            
    except Exception as e:
        logger.error(f"Fehler beim Exportieren des Projekts: {e}")
        return jsonify({"error": str(e)}), 500

@projects_bp.route('/download/<filename>')
def download_export(filename):
    """
    Lädt eine exportierte Datei herunter
    
    Args:
        filename: Name der zu ladenden Datei
    """
    try:
        return send_from_directory(path_manager.temp_dir, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Fehler beim Herunterladen der Export-Datei: {e}")
        abort(404)

def generate_standalone_html(project, image_files):
    """
    Generiert eine eigenständige HTML-Datei für den 360°-Viewer
    
    Args:
        project: Projekt-Instanz
        image_files: Liste der Bilddateien
        
    Returns:
        HTML-Inhalt als String
    """
    # HTML-Template für eigenständigen Viewer
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project.name} - 360° Ansicht</title>
    <style>
        /* Inline CSS */
        {generate_viewer_css()}
    </style>
</head>
<body>
    <div class="container">
        <h1>{project.name} - 360° Ansicht</h1>
        <p>{project.description}</p>
        
        <div id="image-container" class="position-relative">
            <div id="image-viewer" class="position-relative overflow-hidden">
                <img id="current-image" src="" alt="360° Ansicht" class="img-fluid">
            </div>
            <div class="controls">
                <button id="play-button" class="btn">Play</button>
                <button id="stop-button" class="btn" disabled>Stop</button>
                <button id="zoom-in" class="btn">+</button>
                <button id="zoom-out" class="btn">-</button>
            </div>
        </div>
        
        <footer>
            <p>Version 1.0 | &copy; 2025 Alexander Behrens | <a href="https://www.alexanderbehrens.com" target="_blank">www.alexanderbehrens.com</a></p>
        </footer>
    </div>
    
    <script>
        // Bilddaten als JavaScript-Array
        const imageFiles = {json.dumps(image_files)};
        
        // Inline JavaScript
        {generate_viewer_js()}
    </script>
</body>
</html>"""
    
    return html

def generate_pannellum_html(project, image_files):
    """
    Generiert eine HTML-Datei mit Pannellum Viewer
    
    Args:
        project: Projekt-Instanz
        image_files: Liste der Bilddateien
        
    Returns:
        HTML-Inhalt als String
    """
    # HTML-Template für Pannellum Viewer
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project.name} - 360° Ansicht (Pannellum)</title>
    <link rel="stylesheet" href="https://cdn.pannellum.org/2.5/pannellum.css">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #333;
        }}
        #panorama {{
            width: 100%;
            height: 500px;
        }}
        .controls {{
            margin-top: 10px;
        }}
        .btn {{
            padding: 8px 16px;
            background-color: #4a90e2;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 5px;
        }}
        footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{project.name} - 360° Ansicht</h1>
        <p>{project.description}</p>
        
        <div id="panorama"></div>
        
        <div class="controls">
            <button id="prev-button" class="btn">Vorheriges Bild</button>
            <button id="next-button" class="btn">Nächstes Bild</button>
        </div>
        
        <footer>
            <p>Version 1.0 | &copy; 2025 Alexander Behrens | <a href="https://www.alexanderbehrens.com" target="_blank">www.alexanderbehrens.com</a></p>
        </footer>
    </div>
    
    <script src="https://cdn.pannellum.org/2.5/pannellum.js"></script>
    <script>
        // Bilddaten
        const images = {json.dumps(image_files)};
        let currentImageIndex = 0;
        let viewer = null;
        
        // Viewer initialisieren
        function initViewer() {{
            if (viewer) {{
                viewer.destroy();
            }}
            
            viewer = pannellum.viewer('panorama', {{
                "type": "equirectangular",
                "panorama": images[currentImageIndex],
                "autoLoad": true,
                "showZoomCtrl": true,
                "showFullscreenCtrl": true,
                "compass": false
            }});
        }}
        
        // Buttons einrichten
        document.getElementById('prev-button').addEventListener('click', () => {{
            currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
            initViewer();
        }});
        
        document.getElementById('next-button').addEventListener('click', () => {{
            currentImageIndex = (currentImageIndex + 1) % images.length;
            initViewer();
        }});
        
        // Viewer initialisieren
        if (images.length > 0) {{
            initViewer();
        }}
    </script>
</body>
</html>"""
    
    return html

def generate_photosphere_html(project, image_files):
    """
    Generiert eine HTML-Datei mit Photo Sphere Viewer
    
    Args:
        project: Projekt-Instanz
        image_files: Liste der Bilddateien
        
    Returns:
        HTML-Inhalt als String
    """
    # HTML-Template für Photo Sphere Viewer
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project.name} - 360° Ansicht (Photo Sphere Viewer)</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/photo-sphere-viewer@4/dist/photo-sphere-viewer.min.css">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #333;
        }}
        #viewer {{
            width: 100%;
            height: 500px;
        }}
        .controls {{
            margin-top: 10px;
        }}
        .btn {{
            padding: 8px 16px;
            background-color: #4a90e2;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 5px;
        }}
        footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{project.name} - 360° Ansicht</h1>
        <p>{project.description}</p>
        
        <div id="viewer"></div>
        
        <div class="controls">
            <button id="prev-button" class="btn">Vorheriges Bild</button>
            <button id="next-button" class="btn">Nächstes Bild</button>
        </div>
        
        <footer>
            <p>Version 1.0 | &copy; 2025 Alexander Behrens | <a href="https://www.alexanderbehrens.com" target="_blank">www.alexanderbehrens.com</a></p>
        </footer>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/three/build/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/photo-sphere-viewer@4/dist/photo-sphere-viewer.min.js"></script>
    <script>
        // Bilddaten
        const images = {json.dumps(image_files)};
        let currentImageIndex = 0;
        let viewer = null;
        
        // Viewer initialisieren
        function initViewer() {{
            if (viewer) {{
                viewer.destroy();
            }}
            
            viewer = new PhotoSphereViewer.Viewer({{
                container: document.getElementById('viewer'),
                panorama: images[currentImageIndex],
                navbar: ['autorotate', 'zoom', 'fullscreen'],
                keyboard: {{
                    'ArrowLeft': 'rotateLatitudinal',
                    'ArrowRight': 'rotateLatitudinal',
                    'ArrowUp': 'rotatePolar',
                    'ArrowDown': 'rotatePolar'
                }}
            }});
        }}
        
        // Buttons einrichten
        document.getElementById('prev-button').addEventListener('click', () => {{
            currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
            initViewer();
        }});
        
        document.getElementById('next-button').addEventListener('click', () => {{
            currentImageIndex = (currentImageIndex + 1) % images.length;
            initViewer();
        }});
        
        // Viewer initialisieren
        if (images.length > 0) {{
            initViewer();
        }}
    </script>
</body>
</html>"""
    
    return html

def generate_marzipano_html(project, image_files):
    """
    Generiert eine HTML-Datei mit Marzipano Viewer
    
    Args:
        project: Projekt-Instanz
        image_files: Liste der Bilddateien
        
    Returns:
        HTML-Inhalt als String
    """
    # HTML-Template für Marzipano Viewer
    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project.name} - 360° Ansicht (Marzipano)</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #333;
        }}
        #pano {{
            width: 100%;
            height: 500px;
        }}
        .controls {{
            margin-top: 10px;
        }}
        .btn {{
            padding: 8px 16px;
            background-color: #4a90e2;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 5px;
        }}
        footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{project.name} - 360° Ansicht</h1>
        <p>{project.description}</p>
        
        <div id="pano"></div>
        
        <div class="controls">
            <button id="prev-button" class="btn">Vorheriges Bild</button>
            <button id="next-button" class="btn">Nächstes Bild</button>
        </div>
        
        <footer>
            <p>Version 1.0 | &copy; 2025 Alexander Behrens | <a href="https://www.alexanderbehrens.com" target="_blank">www.alexanderbehrens.com</a></p>
        </footer>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/marzipano@0.10.2/dist/marzipano.min.js"></script>
    <script>
        // Bilddaten
        const images = {json.dumps(image_files)};
        let currentImageIndex = 0;
        let viewer = null;
        let scene = null;
        
        // Viewer initialisieren
        function initViewer() {{
            // Viewer erstellen, wenn noch nicht vorhanden
            if (!viewer) {{
                const viewerOpts = {{
                    controls: {{
                        mouseViewMode: 'drag'
                    }}
                }};
                viewer = new Marzipano.Viewer(document.getElementById('pano'), viewerOpts);
            }}
            
            // Bild laden
            const asset = new Marzipano.ImageUrlSource.fromUrl(images[currentImageIndex]);
            const geometry = new Marzipano.EquirectGeometry([{{ width: 4000 }}]);
            const limiter = Marzipano.RectilinearView.limit.traditional(1024, 100*Math.PI/180);
            const view = new Marzipano.RectilinearView(null, limiter);
            
            // Alte Scene entfernen, falls vorhanden
            if (scene) {{
                scene.destroy();
            }}
            
            // Neue Scene erstellen
            scene = viewer.createScene({{
                source: asset,
                geometry: geometry,
                view: view,
                pinFirstLevel: true
            }});
            
            // Scene anzeigen
            scene.switchTo();
        }}
        
        // Buttons einrichten
        document.getElementById('prev-button').addEventListener('click', () => {{
            currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
            initViewer();
        }});
        
        document.getElementById('next-button').addEventListener('click', () => {{
            currentImageIndex = (currentImageIndex + 1) % images.length;
            initViewer();
        }});
        
        // Viewer initialisieren
        if (images.length > 0) {{
            initViewer();
        }}
    </script>
</body>
</html>"""
    
    return html

def generate_viewer_css():
    """
    Generiert das CSS für den eigenständigen Viewer
    
    Returns:
        CSS-Inhalt als String
    """
    return """
    body {
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 20px;
        background-color: #f5f5f5;
    }
    
    .container {
        max-width: 1200px;
        margin: 0 auto;
        background-color: #fff;
        padding: 20px;
        border-radius: 5px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    h1 {
        color: #333;
    }
    
    #image-viewer {
        width: 100%;
        height: 500px;
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: #f0f0f0;
        position: relative;
        overflow: hidden;
        touch-action: pan-y;
        margin-bottom: 20px;
    }
    
    #current-image {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
        transition: transform 0.1s ease-out;
    }
    
    .controls {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin-top: 10px;
    }
    
    .btn {
        padding: 8px 16px;
        background-color: #4a90e2;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }
    
    .btn:hover {
        background-color: #3a80d2;
    }
    
    .btn:disabled {
        background-color: #cccccc;
        cursor: not-allowed;
    }
    
    #image-viewer.grabbing {
        cursor: grabbing;
    }
    
    #image-viewer.grab {
        cursor: grab;
    }
    
    footer {
        margin-top: 30px;
        text-align: center;
        color: #666;
        font-size: 0.9rem;
    }
    
    @media (max-width: 768px) {
        #image-viewer {
            height: 300px;
        }
    }
    """

def generate_viewer_js():
    """
    Generiert das JavaScript für den eigenständigen Viewer
    
    Returns:
        JavaScript-Inhalt als String
    """
    return """
    // DOM-Elemente
    const imageViewer = document.getElementById('image-viewer');
    const currentImage = document.getElementById('current-image');
    const playButton = document.getElementById('play-button');
    const stopButton = document.getElementById('stop-button');
    const zoomInButton = document.getElementById('zoom-in');
    const zoomOutButton = document.getElementById('zoom-out');
    
    // Viewer-Zustand
    let currentImageIndex = 0;
    let isPlaying = false;
    let playbackInterval = null;
    let zoomLevel = 1;
    let isDragging = false;
    let startX = 0;
    let dragSensitivity = 1;
    
    // Bilder laden
    function loadImage(index) {
        if (index < 0 || index >= imageFiles.length) return;
        
        currentImage.src = imageFiles[index];
        currentImageIndex = index;
        
        // Zoom-Level anwenden
        applyZoom();
    }
    
    // Zoom anwenden
    function applyZoom() {
        currentImage.style.transform = `scale(${zoomLevel})`;
    }
    
    // Wiedergabe starten
    function startPlayback() {
        if (isPlaying) return;
        
        isPlaying = true;
        playButton.disabled = true;
        stopButton.disabled = false;
        
        // Bilder in regelmäßigen Abständen durchschalten
        playbackInterval = setInterval(() => {
            currentImageIndex = (currentImageIndex + 1) % imageFiles.length;
            loadImage(currentImageIndex);
            
            // Wenn wir wieder beim ersten Bild sind, Wiedergabe stoppen
            if (currentImageIndex === 0) {
                stopPlayback();
            }
        }, 500); // 0.5 Sekunden Intervall
    }
    
    // Wiedergabe stoppen
    function stopPlayback() {
        if (!isPlaying) return;
        
        clearInterval(playbackInterval);
        isPlaying = false;
        playButton.disabled = false;
        stopButton.disabled = true;
    }
    
    // Zoomen
    function zoomIn() {
        if (zoomLevel < 3) {
            zoomLevel += 0.2;
            applyZoom();
        }
    }
    
    function zoomOut() {
        if (zoomLevel > 0.5) {
            zoomLevel -= 0.2;
            applyZoom();
        }
    }
    
    // Drehung durch Ziehen
    function handleDrag(dragDistance) {
        const direction = dragDistance > 0 ? -1 : 1;
        const dragThreshold = 20;
        
        const absDistance = Math.abs(dragDistance);
        const imagesToMove = Math.floor(absDistance / dragThreshold);
        
        if (imagesToMove > 0) {
            let newIndex = currentImageIndex + (direction * imagesToMove);
            
            while (newIndex < 0) newIndex += imageFiles.length;
            newIndex = newIndex % imageFiles.length;
            
            if (newIndex !== currentImageIndex) {
                loadImage(newIndex);
                return imagesToMove * dragThreshold * direction;
            }
        }
        
        return 0;
    }
    
    // Event-Listener
    playButton.addEventListener('click', startPlayback);
    stopButton.addEventListener('click', stopPlayback);
    zoomInButton.addEventListener('click', zoomIn);
    zoomOutButton.addEventListener('click', zoomOut);
    
    // Touch- und Maus-Events
    imageViewer.addEventListener('mousedown', e => {
        if (isPlaying) return;
        
        isDragging = true;
        startX = e.clientX;
        imageViewer.classList.add('grabbing');
        e.preventDefault();
    });
    
    imageViewer.addEventListener('touchstart', e => {
        if (isPlaying) return;
        
        isDragging = true;
        startX = e.touches[0].clientX;
        imageViewer.classList.add('grabbing');
    });
    
    window.addEventListener('mousemove', e => {
        if (!isDragging) return;
        
        const dragDistance = e.clientX - startX;
        const consumed = handleDrag(dragDistance);
        startX += consumed;
    });
    
    window.addEventListener('touchmove', e => {
        if (!isDragging) return;
        
        const dragDistance = e.touches[0].clientX - startX;
        const consumed = handleDrag(dragDistance);
        startX += consumed;
        
        e.preventDefault();
    }, { passive: false });
    
    window.addEventListener('mouseup', () => {
        isDragging = false;
        imageViewer.classList.remove('grabbing');
    });
    
    window.addEventListener('touchend', () => {
        isDragging = false;
        imageViewer.classList.remove('grabbing');
    });
    
    // Beim Laden der Seite den Viewer initialisieren
    imageViewer.classList.add('grab');
    loadImage(0);
    """

def generate_pannellum_js():
    """
    Placeholder für Pannellum JS Code
    
    Returns:
        Pannellum JS Code als String
    """
    return """
    // Pannellum JavaScript-Bibliothek
    // In dieser Implementierung wird die CDN-Version verwendet
    """

def generate_photosphere_js():
    """
    Placeholder für Photo Sphere Viewer JS Code
    
    Returns:
        Photo Sphere Viewer JS Code als String
    """
    return """
    // Photo Sphere Viewer JavaScript-Bibliothek
    // In dieser Implementierung wird die CDN-Version verwendet
    """

def generate_marzipano_js():
    """
    Placeholder für Marzipano JS Code
    
    Returns:
        Marzipano JS Code als String
    """
    return """
    // Marzipano JavaScript-Bibliothek
    // In dieser Implementierung wird die CDN-Version verwendet
    """

def generate_wordpress_shortcode(project, image_files):
    """
    Generiert einen WordPress-Shortcode für den 360°-Viewer
    
    Args:
        project: Projekt-Instanz
        image_files: Liste der Bilddateien
        
    Returns:
        Shortcode als String
    """
    # Shortcode-Template
    shortcode = f"""[360_viewer 
  title="{project.name}"
  description="{project.description}"
  images="{','.join(image_files)}"
]"""
    
    # Zusätzliche Anleitung
    instructions = """
=== 360° Viewer Integration für WordPress ===

1. Laden Sie den Inhalt dieser ZIP-Datei in Ihre WordPress Media Library hoch.
2. Installieren Sie das "360° Viewer" Plugin (muss separat installiert werden).
3. Fügen Sie den folgenden Shortcode in Ihren Beitrag oder Ihre Seite ein:

{SHORTCODE}

4. Ersetzen Sie die Bildpfade im Shortcode mit den vollständigen URLs zu den hochgeladenen Bildern.

Version 1.0 | © 2025 Alexander Behrens | www.alexanderbehrens.com
"""
    
    return shortcode + "\n\n" + instructions.format(SHORTCODE=shortcode)

def generate_ecommerce_snippet(project, image_files, platform):
    """
    Generiert ein HTML-Snippet für E-Commerce-Plattformen
    
    Args:
        project: Projekt-Instanz
        image_files: Liste der Bilddateien
        platform: Plattform (shopify oder prestashop)
        
    Returns:
        HTML-Snippet als String
    """
    # Basis-HTML-Snippet
    snippet = f"""<div class="product-360-viewer" id="viewer-{project.id}">
  <h3>{project.name} - 360° Ansicht</h3>
  <div class="viewer-container">
    <div class="image-viewer">
      <img id="current-image-{project.id}" src="images/{image_files[0]}" alt="360° Ansicht">
    </div>
    <div class="controls">
      <button class="play-button">Play</button>
      <button class="stop-button" disabled>Stop</button>
      <button class="zoom-in">+</button>
      <button class="zoom-out">-</button>
    </div>
  </div>
  <div class="footer">
    <p>Version 1.0 | &copy; 2025 Alexander Behrens | <a href="https://www.alexanderbehrens.com" target="_blank">www.alexanderbehrens.com</a></p>
  </div>
</div>

<script>
  // Konfiguration
  const viewer{project.id} = {{
    containerId: 'viewer-{project.id}',
    imageId: 'current-image-{project.id}',
    images: {json.dumps(image_files)},
    imagePath: 'images/'
  }};
  
  // 360° Viewer initialisieren, wenn das Skript geladen ist
  document.addEventListener('DOMContentLoaded', function() {{
    init360Viewer(viewer{project.id});
  }});
</script>
"""
    
    # Plattform-spezifische Anpassungen
    if platform == 'shopify':
        snippet = snippet.replace('<script>', '{% raw %}<script>')
        snippet = snippet.replace('</script>', '</script>{% endraw %}')
    elif platform == 'prestashop':
        snippet = snippet.replace('<script>', '<script type="text/javascript">')
    
    return snippet

def generate_integration_instructions(platform):
    """
    Generiert Installations- und Integrationsanweisungen für die jeweilige Plattform
    
    Args:
        platform: Plattform (shopify oder prestashop)
        
    Returns:
        Anweisungstext als String
    """
    if platform == 'shopify':
        return """
=== 360° Viewer Integration für Shopify ===

Folgen Sie diesen Schritten, um den 360°-Viewer in Ihren Shopify-Shop zu integrieren:

1. Hochladen der Dateien:
   - Erstellen Sie einen neuen Ordner "360-viewer" in Ihrem Shopify-Assets-Verzeichnis.
   - Laden Sie die Dateien "viewer.js" und "viewer.css" in diesen Ordner hoch.
   - Erstellen Sie einen Unterordner "images" und laden Sie alle Bilddateien dort hoch.

2. Einbinden der Skripte:
   - Gehen Sie zu Ihrem Shopify-Admin-Panel > Online Store > Themes.
   - Klicken Sie auf "Actions" > "Edit code" für Ihr aktuelles Theme.
   - Öffnen Sie die Datei "theme.liquid" im Layout-Ordner.
   - Fügen Sie folgende Zeilen vor dem schließenden </head>-Tag ein:
      
      {{ 'viewer.css' | asset_url | stylesheet_tag }}
      {{ 'viewer.js' | asset_url | script_tag }}

3. Integration in eine Produktseite:
   - Öffnen Sie die Produktvorlage (z.B. "product.liquid").
   - Kopieren Sie den HTML-Code aus der Datei "integration.html" und fügen Sie ihn an der gewünschten Stelle ein.
   - Passen Sie die Bildpfade an: Ändern Sie "images/" zu "{{ 'images/' | asset_url }}".

4. Testen:
   - Rufen Sie Ihre Produktseite auf und prüfen Sie, ob der 360°-Viewer korrekt angezeigt wird.
   - Stellen Sie sicher, dass die Bilder geladen werden und die Steuerelemente funktionieren.

Bei Problemen:
- Prüfen Sie die Browser-Konsole auf JavaScript-Fehler.
- Stellen Sie sicher, dass alle Dateipfade korrekt sind.
- Achten Sie darauf, dass der Liquid-Code korrekt formatiert ist.

Version 1.0 | © 2025 Alexander Behrens | www.alexanderbehrens.com
"""
    elif platform == 'prestashop':
        return """
=== 360° Viewer Integration für PrestaShop ===

Folgen Sie diesen Schritten, um den 360°-Viewer in Ihren PrestaShop-Shop zu integrieren:

1. Hochladen der Dateien:
   - Erstellen Sie einen neuen Ordner "360-viewer" im Verzeichnis "themes/[Ihr-Theme]/assets/js".
   - Kopieren Sie die Dateien "viewer.js" und "viewer.css" in diesen Ordner.
   - Erstellen Sie einen Unterordner "images" und kopieren Sie alle Bilddateien dort hinein.

2. Einbinden der Skripte:
   - Bearbeiten Sie die Datei "themes/[Ihr-Theme]/templates/_partials/javascript.tpl".
   - Fügen Sie folgende Zeilen hinzu:
      
      <script type="text/javascript" src="{$urls.theme_assets}js/360-viewer/viewer.js"></script>
      <link rel="stylesheet" href="{$urls.theme_assets}js/360-viewer/viewer.css">

3. Integration in eine Produktseite:
   - Bearbeiten Sie die Datei "themes/[Ihr-Theme]/templates/catalog/product.tpl".
   - Kopieren Sie den HTML-Code aus der Datei "integration.html" und fügen Sie ihn an der gewünschten Stelle ein.
   - Passen Sie die Bildpfade an: Ändern Sie "images/" zu "{$urls.theme_assets}js/360-viewer/images/".

4. Testen:
   - Leeren Sie den PrestaShop-Cache (Advanced Parameters > Performance).
   - Rufen Sie eine Produktseite auf, um zu prüfen, ob der 360°-Viewer korrekt angezeigt wird.

Bei Problemen:
- Aktivieren Sie den Debug-Modus in PrestaShop, um JavaScript-Fehler zu sehen.
- Prüfen Sie, ob die Dateipfade korrekt sind.
- Stellen Sie sicher, dass Ihr Theme die SmartY-Variablen wie {$urls.theme_assets} unterstützt.

Version 1.0 | © 2025 Alexander Behrens | www.alexanderbehrens.com
"""
    else:
        return """
=== 360° Viewer Integration ===

Allgemeine Installationsanleitung:

1. Hochladen der Dateien:
   - Laden Sie alle Dateien in einen öffentlich zugänglichen Ordner Ihres Webservers hoch.
   - Behalten Sie die Ordnerstruktur bei (JS-/CSS-Dateien im Hauptverzeichnis, Bilder im Unterordner "images").

2. Einbinden der Skripte:
   - Fügen Sie folgende Zeilen im <head>-Bereich Ihrer HTML-Seite ein:
      
      <link rel="stylesheet" href="pfad/zum/viewer.css">
      <script src="pfad/zum/viewer.js"></script>

3. Integration des Viewers:
   - Kopieren Sie den HTML-Code aus der Datei "integration.html" an die gewünschte Stelle auf Ihrer Seite.
   - Passen Sie die Bildpfade an, falls nötig.

4. Testen:
   - Rufen Sie die Seite auf und prüfen Sie, ob der 360°-Viewer korrekt angezeigt wird.
   - Stellen Sie sicher, dass die Bilder geladen werden und die Steuerelemente funktionieren.

Bei Problemen:
- Prüfen Sie die Browser-Konsole auf JavaScript-Fehler.
- Stellen Sie sicher, dass alle Dateipfade korrekt sind.

Version 1.0 | © 2025 Alexander Behrens | www.alexanderbehrens.com
"""
