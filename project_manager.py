# project_manager.py
import os
import json
import time
import shutil
from datetime import datetime


class ProjectManager:
    def __init__(self, base_path='projects'):
        """
        Verwaltet 360°-Projekte

        :param base_path: Basisverzeichnis für Projekte
        """
        self.base_path = base_path

        # Stelle sicher, dass das Projektverzeichnis existiert
        os.makedirs(base_path, exist_ok=True)

    def create_project(self, name, description=None):
        """
        Erstellt ein neues Projekt

        :param name: Projektname
        :param description: Projektbeschreibung (optional)
        :return: Projektverzeichnis
        """
        # Erzeuge einen sicheren Verzeichnisnamen aus dem Projektnamen
        safe_name = "".join([c if c.isalnum() else "_" for c in name])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = f"{safe_name}_{timestamp}"

        # Erstelle Projektverzeichnis und Unterordner
        project_path = os.path.join(self.base_path, project_dir)
        os.makedirs(project_path, exist_ok=True)
        os.makedirs(os.path.join(project_path, 'images'), exist_ok=True)

        # Erstelle Projektmetadaten
        metadata = {
            'name': name,
            'description': description,
            'created': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat(),
            'image_count': 0,
            'rotation_settings': {
                'degrees_per_step': 15,
                'interval_seconds': 5
            }
        }

        # Speichere Metadaten
        with open(os.path.join(project_path, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=4)

        return project_path

    def get_projects(self):
        """
        Gibt alle verfügbaren Projekte zurück

        :return: Liste von Projekten mit Metadaten
        """
        projects = []

        for project_dir in os.listdir(self.base_path):
            project_path = os.path.join(self.base_path, project_dir)
            metadata_path = os.path.join(project_path, 'metadata.json')

            if os.path.isdir(project_path) and os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)

                    # Füge Verzeichnisnamen hinzu
                    metadata['directory'] = project_dir

                    # Zähle Bilder
                    images_path = os.path.join(project_path, 'images')
                    if os.path.exists(images_path):
                        image_files = [f for f in os.listdir(images_path)
                                       if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                        metadata['image_count'] = len(image_files)

                    projects.append(metadata)
                except Exception as e:
                    print(f"Fehler beim Laden von Projekt {project_dir}: {e}")

        # Sortiere nach Erstellungsdatum, neueste zuerst
        projects.sort(key=lambda x: x.get('created', ''), reverse=True)

        return projects

    def get_project(self, project_dir):
        """
        Gibt Metadaten für ein bestimmtes Projekt zurück

        :param project_dir: Projektverzeichnis
        :return: Projektmetadaten
        """
        project_path = os.path.join(self.base_path, project_dir)
        metadata_path = os.path.join(project_path, 'metadata.json')

        if not os.path.exists(metadata_path):
            return None

        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            # Füge Verzeichnisnamen hinzu
            metadata['directory'] = project_dir

            # Zähle Bilder und füge Bilderpfade hinzu
            images_path = os.path.join(project_path, 'images')
            if os.path.exists(images_path):
                image_files = [f for f in os.listdir(images_path)
                               if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                metadata['image_count'] = len(image_files)
                metadata['images'] = sorted(image_files)

            return metadata
        except Exception as e:
            print(f"Fehler beim Laden von Projekt {project_dir}: {e}")
            return None

    def add_image_to_project(self, project_dir, image_path):
        """
        Fügt ein Bild zum Projekt hinzu

        :param project_dir: Projektverzeichnis
        :param image_path: Pfad zum Bild
        :return: Pfad zum kopierten Bild
        """
        project_path = os.path.join(self.base_path, project_dir)
        images_path = os.path.join(project_path, 'images')

        # Stelle sicher, dass das Bildverzeichnis existiert
        os.makedirs(images_path, exist_ok=True)

        # Kopiere das Bild ins Projektverzeichnis
        image_filename = os.path.basename(image_path)
        destination = os.path.join(images_path, image_filename)
        shutil.copy(image_path, destination)

        # Aktualisiere Metadaten
        metadata_path = os.path.join(project_path, 'metadata.json')
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)

                # Aktualisiere Bilderzählung und Änderungsdatum
                metadata['image_count'] = len([f for f in os.listdir(images_path)
                                               if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                metadata['last_modified'] = datetime.now().isoformat()

                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=4)
            except Exception as e:
                print(f"Fehler beim Aktualisieren der Projektmetadaten: {e}")

        return destination

    def delete_project(self, project_dir):
        """
        Löscht ein Projekt

        :param project_dir: Projektverzeichnis
        :return: True bei Erfolg, False bei Fehler
        """
        project_path = os.path.join(self.base_path, project_dir)

        if not os.path.exists(project_path):
            return False

        try:
            shutil.rmtree(project_path)
            return True
        except Exception as e:
            print(f"Fehler beim Löschen des Projekts {project_dir}: {e}")
            return False


# Beispiel für die Verwendung
if __name__ == "__main__":
    manager = ProjectManager()

    # Erstelle ein neues Projekt
    project_path = manager.create_project(
        name="Test Produkt",
        description="Eine 360°-Ansicht eines Testprodukts"
    )

    print(f"Neues Projekt erstellt: {project_path}")

    # Liste alle Projekte auf
    projects = manager.get_projects()
    print(f"Vorhandene Projekte: {len(projects)}")
    for project in projects:
        print(f"- {project['name']} ({project['directory']})")