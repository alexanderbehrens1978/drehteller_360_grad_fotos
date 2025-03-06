from flask import Blueprint, render_template, request, jsonify
import os
import json
import time
import shutil
import traceback
#Debug
# Am Anfang der Datei nach den Imports
print("Lade project_routes.py mit Blueprint project_bp")

project_bp = Blueprint('project', __name__)

@project_bp.route('/projects')
def view_projects():
    """Zeigt die Projektliste an"""
    return render_template('projects.html')

@project_bp.route('/generate_360', methods=['POST'])
def generate_360():
    """Generiert einen 360°-Viewer aus den aufgenommenen Bildern."""
    try:
        print("generate_360 Route wurde aufgerufen")

        # Liste der Fotos nach Zeitstempel sortieren
        photo_dir = 'static/photos'
        photos = sorted([f for f in os.listdir(photo_dir)
                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

        print(f"Gefundene Fotos: {len(photos)}")

        if not photos:
            print("Keine Fotos gefunden")
            return jsonify({"status": "error", "message": "Keine Fotos gefunden"}), 400

        # Optionale Metadaten aus der Anfrage
        metadata = {}
        if request.is_json:
            metadata = request.json
        elif request.form:
            # Unterstütze auch form-data
            metadata = request.form.to_dict()

        print(f"Erhaltene Metadaten: {metadata}")

        # Projekt-Verzeichnis erstellen
        project_id = f"project_{int(time.time())}"
        project_dir = os.path.join('static/projects', project_id)
        os.makedirs(project_dir, exist_ok=True)

        print(f"Projektverzeichnis erstellt: {project_dir}")

        # Fotos in das Projektverzeichnis kopieren
        for i, photo in enumerate(photos):
            source = os.path.join(photo_dir, photo)
            target = os.path.join(project_dir, f"image_{i:03d}.jpg")
            shutil.copy2(source, target)
            print(f"Foto kopiert: {source} -> {target}")

        # Metadaten speichern
        metadata_file = {
            'id': project_id,
            'name': metadata.get('name', f"Projekt {project_id}"),
            'description': metadata.get('description', ''),
            'created': int(time.time()),
            'images': [f"image_{i:03d}.jpg" for i in range(len(photos))]
        }

        metadata_path = os.path.join(project_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata_file, f, indent=2)

        print(f"Metadaten gespeichert: {metadata_path}")

        # Erfolg zurückgeben
        response_data = {
            "status": "success",
            "url": f"/viewer?project={project_id}"
        }
        print(f"Antwort: {response_data}")

        return jsonify(response_data)
    except Exception as e:
        print(f"Fehler bei generate_360: {str(e)}")
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@project_bp.route('/api/project/<project_id>')
def get_project(project_id):
    """Liefert Projektdaten für den 360°-Viewer."""
    try:
        project_dir = os.path.join('static/projects', project_id)
        metadata_path = os.path.join(project_dir, 'metadata.json')

        if not os.path.exists(metadata_path):
            return jsonify({"error": "Projekt nicht gefunden"}), 404

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        return jsonify(metadata)
    except Exception as e:
        print(f"Fehler beim Laden der Projektdaten: {e}")
        return jsonify({"error": str(e)}), 500

@project_bp.route('/projects/list')
def list_projects():
    """Liefert eine Liste aller vorhandenen Projekte."""
    try:
        projects_dir = 'static/projects'
        projects = []

        # Stelle sicher, dass das Verzeichnis existiert
        if not os.path.exists(projects_dir):
            os.makedirs(projects_dir)
            return jsonify(projects)

        # Durchsuche das Projektverzeichnis
        for project_id in os.listdir(projects_dir):
            metadata_path = os.path.join(projects_dir, project_id, 'metadata.json')
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    projects.append(metadata)
                except:
                    # Ignoriere ungültige Projektdateien
                    pass

        # Sortiere Projekte nach Erstellungsdatum (neueste zuerst)
        projects.sort(key=lambda x: x.get('created', 0), reverse=True)

        return jsonify(projects)
    except Exception as e:
        print(f"Fehler beim Auflisten der Projekte: {e}")
        return jsonify({"error": str(e)}), 500

@project_bp.route('/test_project')
def test_project():
    return "Project Blueprint funktioniert!"