"""
app/blueprints/viewer/routes.py
Enthält die Routen für den 360° Viewer
"""

import os
import json
import logging
from flask import render_template, request, redirect, url_for, jsonify, abort
from app.blueprints.viewer import viewer_bp
from app.models.project import ProjectManager
from app.utils.path_manager import PathManager
from app.utils.secure_path import validate_project_id

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
                return render_template('viewer/sphere_viewer.html', project=selected_project)
        
        # Ansonsten die Übersichtsseite anzeigen
        return render_template('viewer/overview.html', projects=projects)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Viewer-Übersicht: {str(e)}")
        return render_template('error.html', message=f"Fehler beim Laden der Viewer-Übersicht: {str(e)}"), 500

@viewer_bp.route('/sphere')
def sphere_viewer():
    """Zeigt den 360° Sphere Viewer für ein Projekt"""
    try:
        # Projekt-ID aus URL-Parameter lesen
        project_id = request.args.get('project')
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
        
        return render_template('viewer/sphere_viewer.html', project=project)
    except Exception as e:
        logger.error(f"Fehler beim Laden des Sphere Viewers: {str(e)}")
        return render_template('error.html', message=f"Fehler beim Laden des Sphere Viewers: {str(e)}"), 500

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
        
        # Export-URL erstellen
        base_url = request.host_url.rstrip('/')
        export_url = f"{base_url}/viewer/sphere?project={project_id}"
        
        # Wenn Bilder explizit ausgewählt wurden, diese hinzufügen
        if selected_images:
            export_url += f"&images={','.join(selected_images)}"
        
        # Export-Code-Template
        embed_code = create_embed_code(project, selected_images, base_url)
        
        return jsonify({
            "status": "success",
            "export_url": export_url,
            "embed_code": embed_code
        })
    except Exception as e:
        logger.error(f"Fehler beim Exportieren des Viewers: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def create_embed_code(project, selected_images, base_url):
    """Erstellt den HTML-Embed-Code für den Viewer"""
    # Die tatsächlichen Bilder aus dem Projekt filtern
    image_objects = []
    if selected_images:
        for img in project.images:
            if img['path'] in selected_images:
                image_objects.append(img)
    else:
        image_objects = project.images
    
    # Nach Winkel sortieren
    image_objects.sort(key=lambda x: x.get('angle', 0))
    
    # JavaScript-Teil für die Bilder erstellen
    images_js = []
    for img in image_objects:
        angle = img.get('angle', 0)
        path = img.get('path', '')
        images_js.append(f"""{{
            id: '{angle}',
            name: 'Winkel {angle}°',
            panorama: '{base_url}/projects/image/{project.id}/{path}',
            thumbnail: '{base_url}/projects/image/{project.id}/{path}'
        }}""")
    
    images_block = ",\n        ".join(images_js)
    
    # Vollständigen Embed-Code erstellen
    embed_code = f"""<!-- 360° Panorama Viewer - generiert von Alexander Behrens 360° Drehteller Steuerung -->
<div id="panorama-viewer" style="width: 100%; height: 500px;"></div>

<!-- CSS für den Viewer -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@photo-sphere-viewer/core@5/index.css">

<!-- Import Map für die Module -->
<script type="importmap">
{{
    "imports": {{
        "three": "https://cdn.jsdelivr.net/npm/three/build/three.module.js",
        "@photo-sphere-viewer/core": "https://cdn.jsdelivr.net/npm/@photo-sphere-viewer/core@5/index.module.js",
        "@photo-sphere-viewer/autorotate-plugin": "https://cdn.jsdelivr.net/npm/@photo-sphere-viewer/autorotate-plugin@5/index.module.js",
        "@photo-sphere-viewer/gallery-plugin": "https://cdn.jsdelivr.net/npm/@photo-sphere-viewer/gallery-plugin@5/index.module.js"
    }}
}}
</script>

<!-- JavaScript für den Viewer -->
<script type="module">
    import {{ Viewer }} from '@photo-sphere-viewer/core';
    import {{ AutorotatePlugin }} from '@photo-sphere-viewer/autorotate-plugin';
    import {{ GalleryPlugin }} from '@photo-sphere-viewer/gallery-plugin';
    
    // Bilder aus dem Projekt
    const images = [
        {images_block}
    ];
    
    // Viewer initialisieren
    const viewer = new Viewer({{
        container: 'panorama-viewer',
        panorama: images[0].panorama,
        caption: '{project.name} - ' + images[0].name,
        touchmoveTwoFingers: true,
        mousewheelCtrlKey: true,
        navbar: [
            'autorotate',
            'zoom',
            'gallery',
            'fullscreen'
        ],
        plugins: [
            [AutorotatePlugin, {{
                autorotatePitch: 0,
                autorotateSpeed: '2rpm',
                autorotateDelay: 1000
            }}],
            [GalleryPlugin, {{
                thumbnails: images
            }}]
        ]
    }});
    
    // Auto-Rotation nach dem Laden starten
    viewer.addEventListener('ready', () => {{
        viewer.getPlugin(AutorotatePlugin).start();
    }});
    
    // Bildunterschrift aktualisieren, wenn sich das Bild ändert
    viewer.addEventListener('panorama-loaded', (e) => {{
        const currentImage = images.find(img => img.panorama === e.data.panorama);
        if (currentImage) {{
            viewer.setCaption('{project.name} - ' + currentImage.name);
        }}
    }});
</script>"""

    return embed_code

# Diese Funktion zur Datei /app/blueprints/viewer/routes.py hinzufügen

@viewer_bp.route('/cloudimage')
def cloudimage_viewer():
    """
    Zeigt den CloudImage 360° Viewer für ein Projekt an
    """
    try:
        # Projekt-ID aus URL-Parameter lesen
        project_id = request.args.get('project')
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
        
        return render_template('viewer/cloudimage-viewer.html', project=project)
    except Exception as e:
        logger.error(f"Fehler beim Laden des CloudImage Viewers: {str(e)}")
        return render_template('error.html', message=f"Fehler beim Laden des CloudImage Viewers: {str(e)}"), 500
