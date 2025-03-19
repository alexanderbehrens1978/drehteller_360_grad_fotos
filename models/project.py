# Datei: models/project.py
# Modul für das Projektdatenmodell und die Projektverwaltung

import os
import json
import time
import uuid
import logging
import shutil
from pathlib import Path


class Project:
    """Klasse zur Darstellung eines Projekts"""

    def __init__(self, id=None, name="Neues Projekt", description="", angle_step=5, path=None):
        """Initialisiert ein Projekt"""
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.angle_step = angle_step
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.sessions = []
        self.path = path or ""

    def add_session(self, session):
        """Fügt eine Fotosession zum Projekt hinzu"""
        self.sessions.append(session)
        self.updated_at = time.time()

    def get_session(self, session_id):
        """Gibt eine Session anhand ihrer ID zurück"""
        for session in self.sessions:
            if session.id == session_id:
                return session
        return None

    def remove_session(self, session_id):
        """Entfernt eine Session aus dem Projekt"""
        for i, session in enumerate(self.sessions):
            if session.id == session_id:
                del self.sessions[i]
                self.updated_at = time.time()
                return True
        return False

    def to_dict(self):
        """Konvertiert das Projekt in ein Dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'angle_step': self.angle_step,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'sessions': [session.to_dict() for session in self.sessions],
            'path': self.path
        }

    @classmethod
    def from_dict(cls, data):
        """Erstellt ein Projekt aus einem Dictionary"""
        from .photo_session import PhotoSession

        project = cls(
            id=data.get('id'),
            name=data.get('name', "Unbenanntes Projekt"),
            description=data.get('description', ""),
            angle_step=data.get('angle_step', 5),
            path=data.get('path', "")
        )

        project.created_at = data.get('created_at', time.time())
        project.updated_at = data.get('updated_at', time.time())

        # Sessions laden
        for session_data in data.get('sessions', []):
            project.sessions.append(PhotoSession.from_dict(session_data))

        return project

    def save(self):
        """Speichert das Projekt"""
        if not self.path:
            return False

        try:
            # Metadaten-Datei speichern
            metadata_path = os.path.join(self.path, "project.json")
            with open(metadata_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=4)

            return True
        except Exception as e:
            logging.error(f"Fehler beim Speichern des Projekts {self.id}: {str(e)}")
            return False


class ProjectManager:
    """Klasse zur Verwaltung von Projekten"""

    def __init__(self, projects_dir):
        """Initialisiert den Projektmanager"""
        self.logger = logging.getLogger(__name__)
        self.projects_dir = projects_dir

        # Stellen Sie sicher, dass das Projektverzeichnis existiert
        os.makedirs(self.projects_dir, exist_ok=True)

    def get_project_path(self, project_id):
        """Gibt den Pfad eines Projekts zurück"""
        return os.path.join(self.projects_dir, project_id)

    def get_all_projects(self):
        """Gibt eine Liste aller Projekte zurück"""
        projects = []

        try:
            # Durchsuche das Projektverzeichnis nach Projektordnern
            for item in os.listdir(self.projects_dir):
                project_path = os.path.join(self.projects_dir, item)

                # Prüfen, ob es sich um ein Verzeichnis handelt
                if os.path.isdir(project_path):
                    # Prüfen, ob eine Projektdatei existiert
                    project_file = os.path.join(project_path, "project.json")
                    if os.path.isfile(project_file):
                        try:
                            with open(project_file, 'r') as f:
                                project_data = json.load(f)
                                project = Project.from_dict(project_data)
                                # Sicherstellen, dass der Pfad korrekt ist
                                project.path = project_path
                                projects.append(project)
                        except Exception as e:
                            self.logger.error(f"Fehler beim Laden des Projekts {item}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Fehler beim Durchsuchen des Projektverzeichnisses: {str(e)}")

        # Sortiere Projekte nach Erstellungsdatum (neueste zuerst)
        return sorted(projects, key=lambda p: p.updated_at, reverse=True)

    def get_project(self, project_id):
        """Gibt ein Projekt anhand seiner ID zurück"""
        project_path = self.get_project_path(project_id)
        project_file = os.path.join(project_path, "project.json")

        if os.path.isfile(project_file):
            try:
                with open(project_file, 'r') as f:
                    project_data = json.load(f)
                    project = Project.from_dict(project_data)
                    # Sicherstellen, dass der Pfad korrekt ist
                    project.path = project_path
                    return project
            except Exception as e:
                self.logger.error(f"Fehler beim Laden des Projekts {project_id}: {str(e)}")

        return None

    def save_project(self, project):
        """Speichert ein Projekt"""
        # Stellen Sie sicher, dass das Projekt eine ID hat
        if not project.id:
            project.id = str(uuid.uuid4())

        # Projektpfad erstellen
        project_path = self.get_project_path(project.id)
        os.makedirs(project_path, exist_ok=True)

        # Sessions-Verzeichnis erstellen
        sessions_path = os.path.join(project_path, "sessions")
        os.makedirs(sessions_path, exist_ok=True)

        # Pfad im Projekt aktualisieren
        project.path = project_path

        # Projekt speichern
        return project.save()

    def delete_project(self, project_id):
        """Löscht ein Projekt"""
        project_path = self.get_project_path(project_id)

        if os.path.isdir(project_path):
            try:
                shutil.rmtree(project_path)
                self.logger.info(f"Projekt {project_id} gelöscht")
                return True
            except Exception as e:
                self.logger.error(f"Fehler beim Löschen des Projekts {project_id}: {str(e)}")

        return False