#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_utils.py
Hilfsfunktionen zum Exportieren von 360-Grad-Ansichten als eigenständige HTML-Dateien
"""

import os
import base64
import mimetypes
import logging
from pathlib import Path
import shutil
import zipfile
import time
import json

logger = logging.getLogger(__name__)

def get_file_as_base64(file_path):
    """Liest eine Datei ein und kodiert sie als Base64"""
    try:
        with open(file_path, 'rb') as file:
            file_content = file.read()
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            base64_encoded = base64.b64encode(file_content).decode('utf-8')
            return f"data:{mime_type};base64,{base64_encoded}"
    except Exception as e:
        logger.error(f"Fehler beim Lesen der Datei {file_path}: {str(e)}")
        return None

def read_file_content(file_path):
    """Liest eine Datei ein und gibt den Inhalt zurück"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logger.error(f"Fehler beim Lesen der Datei {file_path}: {str(e)}")
        return None

def create_html_export(project, static_folder, base_url=None, settings=None):
    """
    Erzeugt eine eigenständige HTML-Datei mit eingebetteten Bildern und JavaScript/CSS
    
    Args:
        project: Das Projekt-Objekt mit den 360-Grad-Bildern
        static_folder: Pfad zum static-Ordner
        base_url: Basis-URL für absolute Pfade (optional)
        settings: Viewer-Einstellungen (optional)
        
    Returns:
        html_content: Der Inhalt der HTML-Datei
    """
    # CSS und JavaScript einlesen
    css_content = read_file_content(os.path.join(static_folder, 'css', 'cloudimage-viewer.css'))
    js_content = read_file_content(os.path.join(static_folder, 'js', 'cloudimage-viewer.js'))
    
    # Basis-CSS für grundlegende Formatierung
    base_css = """
    body, html {
        margin: 0;
        padding: 0;
        font-family: Arial, sans-serif;
        background-color: #f8f8f8;
    }
    .container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 20px;
    }
    header {
        text-align: center;
        margin-bottom: 30px;
    }
    footer {
        text-align: center;
        margin-top: 30px;
        color: #666;
        font-size: 0.8em;
    }
    """
    
    # Bilder als Base64 kodieren
    image_tags = []
    for i, img in enumerate(project.images):
        image_path = os.path.join(static_folder, 'projects', project.id, img['path'])
        base64_image = get_file_as_base64(image_path)
        if base64_image:
            is_first = i == 0
            display_style = "" if is_first else "style=\"display: none;\""
            active_class = "active" if is_first else ""
            image_tags.append(f'<img class="product-image {active_class}" '
                             f'src="{base64_image}" '
                             f'alt="Bild {i+1} von {len(project.images)}" '
                             f'{display_style}>')
    
    # Einstellungen für den Viewer
    settings_json = json.dumps(settings or {})
    
    # HTML-Datei erstellen
    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="project-id" content="{project.id}">
    <title>{project.name} - 360° Ansicht</title>
    <style>
    {base_css}
    {css_content}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{project.name}</h1>
            <p>360° Ansicht Ihres Produkts</p>
        </header>
        
        <main>
            <!-- 360° Viewer Container -->
            <div id="viewer-container" class="viewer-container">
                <!-- Bottom Circle Indicator -->
                <div class="bottom-circle"></div>
                
                <div id="viewer" class="cloudimage-360" 
                     data-filename-pattern="image_{{index}}.jpg"
                     data-amount="{len(project.images)}"
                     data-spin-reverse="false"
                     data-full-screen="true"
                     data-magnifier="true"
                     data-ratio="1">
                    <!-- Bilder direkt einbinden -->
                    {''.join(image_tags)}
                </div>
                
                <!-- Magnifier-Glas -->
                <div class="img-magnifier-glass" style="display: none; position: absolute; border: 2px solid #ccc; border-radius: 50%; cursor: none; width: 150px; height: 150px; background-repeat: no-repeat;"></div>
                
                <!-- Viewer Steuerelemente -->
                <div class="viewer-controls">
                    <button id="play-btn" class="control-btn" title="Wiedergabe starten/pausieren">
                        <span id="play-icon">▶</span>
                    </button>
                    <button id="fullscreen-btn" class="control-btn" title="Vollbild">⛶</button>
                    <button id="magnifier-btn" class="control-btn" title="Lupe">🔍</button>
                </div>
                
                <!-- Unsichtbare Einstellungen (werden vom JavaScript gelesen) -->
                <div id="viewer-settings-data" style="display: none;" data-settings='{settings_json}'></div>
            </div>
        </main>
        
        <footer>
            <p>&copy; {time.strftime('%Y')} 360° Drehteller Steuerung. Alle Rechte vorbehalten.</p>
        </footer>
    </div>
    
    <script>
    window.projectId = "{project.id}";
    // Viewer-Einstellungen laden
    window.viewerSettings = {settings_json};
    {js_content}
    </script>
</body>
</html>"""
    
    return html_content

def create_export_zip(project, static_folder, output_path, settings=None):
    """
    Erstellt ein ZIP-Archiv mit HTML-Datei und den Bildern für den Export
    
    Args:
        project: Das Projekt-Objekt mit den 360-Grad-Bildern
        static_folder: Pfad zum static-Ordner
        output_path: Ausgabepfad für die ZIP-Datei
        settings: Viewer-Einstellungen (optional)
        
    Returns:
        zip_path: Pfad zur erstellten ZIP-Datei
    """
    # Temporäres Verzeichnis erstellen
    temp_dir = os.path.join(output_path, f"{project.id}_export_temp")
    os.makedirs(temp_dir, exist_ok=True)
    
    # Projekt-Verzeichnis (für Bilder)
    project_images_dir = os.path.join(temp_dir, 'images')
    os.makedirs(project_images_dir, exist_ok=True)
    
    # CSS- und JS-Verzeichnisse
    css_dir = os.path.join(temp_dir, 'css')
    js_dir = os.path.join(temp_dir, 'js')
    os.makedirs(css_dir, exist_ok=True)
    os.makedirs(js_dir, exist_ok=True)
    
    # CSS und JavaScript kopieren
    shutil.copy(
        os.path.join(static_folder, 'css', 'cloudimage-viewer.css'),
        os.path.join(css_dir, 'cloudimage-viewer.css')
    )
    shutil.copy(
        os.path.join(static_folder, 'js', 'cloudimage-viewer.js'),
        os.path.join(js_dir, 'cloudimage-viewer.js')
    )
    
    # Bilder kopieren
    for i, img in enumerate(project.images):
        source_path = os.path.join(static_folder, 'projects', project.id, img['path'])
        target_path = os.path.join(project_images_dir, f"image_{i+1}.jpg")
        shutil.copy(source_path, target_path)
    
    # Einstellungen für den Viewer
    settings_json = json.dumps(settings or {})
    
    # HTML-Datei erstellen
    html_content = f"""<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="project-id" content="{project.id}">
    <title>{project.name} - 360° Ansicht</title>
    <link rel="stylesheet" href="css/cloudimage-viewer.css">
    <script src="js/cloudimage-viewer.js" defer></script>
</head>
<body>
    <div class="container">
        <header>
            <h1>{project.name}</h1>
            <p>360° Ansicht Ihres Produkts</p>
        </header>
        
        <main>
            <!-- 360° Viewer Container -->
            <div id="viewer-container" class="viewer-container">
                <!-- Bottom Circle Indicator -->
                <div class="bottom-circle"></div>
                
                <div id="viewer" class="cloudimage-360" 
                     data-folder="images/"
                     data-filename-pattern="image_{{index}}.jpg"
                     data-amount="{len(project.images)}"
                     data-spin-reverse="false"
                     data-full-screen="true"
                     data-magnifier="true"
                     data-ratio="1">
                </div>
                
                <!-- Magnifier-Glas -->
                <div class="img-magnifier-glass" style="display: none; position: absolute; border: 2px solid #ccc; border-radius: 50%; cursor: none; width: 150px; height: 150px; background-repeat: no-repeat;"></div>
                
                <!-- Viewer Steuerelemente -->
                <div class="viewer-controls">
                    <button id="play-btn" class="control-btn" title="Wiedergabe starten/pausieren">
                        <span id="play-icon">▶</span>
                    </button>
                    <button id="fullscreen-btn" class="control-btn" title="Vollbild">⛶</button>
                    <button id="magnifier-btn" class="control-btn" title="Lupe">🔍</button>
                </div>
                
                <!-- Unsichtbare Einstellungen (werden vom JavaScript gelesen) -->
                <div id="viewer-settings-data" style="display: none;" data-settings='{settings_json}'></div>
            </div>
        </main>
        
        <footer>
            <p>&copy; {time.strftime('%Y')} 360° Drehteller Steuerung. Alle Rechte vorbehalten.</p>
        </footer>
    </div>
    
    <script>
        // Setze die Projekt-ID für JavaScript
        window.projectId = "{project.id}";
        // Viewer-Einstellungen laden
        window.viewerSettings = {settings_json};
    </script>
</body>
</html>"""
    
    # HTML-Datei speichern
    with open(os.path.join(temp_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # ZIP-Archiv erstellen
    zip_path = os.path.join(output_path, f"{project.id}_export.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, temp_dir))
    
    # Temporäres Verzeichnis aufräumen
    shutil.rmtree(temp_dir)
    
    return zip_path
