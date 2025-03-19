#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/models/project.py
Modell für das Projekt und die Projektverwaltung
"""

import os
import json
import time
import uuid
import logging
import string
import shutil
from pathlib import Path
from app.models.photo_session import PhotoSession

# Logger einrichten
logger = logging.getLogger(__name__)

# Sicherheitsfunktionen
def secure_filename(filename):
    """Bereinigt einen Dateinamen und entfernt potenziell gefährliche Zeichen."""
    if filename:
        filename = os.path.basename(filename)
        allowed_chars = set(string.ascii_letters + string.digits + '-_.')
        filename = ''.join(c for c in filename if c in allowed_chars)
    return filename

def secure_join(base_path, *paths):
    """Verbindet Pfadsegmente sicher und verhindert Verzeichnistraversierungsangriffe."""
    base_path = os.path.abspath(base_path)
    safe_path = os.path.abspath(os.path.join(base_path, *[secure_filename(p) if i == len(paths)-1 else p for i, p in enumerate(paths)]))
    
    if not safe_path.startswith(base_path):
        return base_path
        
    return safe_path

class Project:
    """Klasse zur Darstellung eines Projekts"""

    def __init__(self, id=None, name="Neues Projekt", description="", angle_step=5, path=None):
        """
        Initialisiert ein Projekt
        
        Args:
            id: Projekt-ID (optional)
            name: Projektname (optional)
            description: Projektbeschreibung (optional)
            angle_step: Winkelschritt in Grad (optional)
            path: Pfad zum Projektverzeichnis (optional)
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.angle_step = angle_step
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.sessions = []
        self.path = path or ""
        self.images = []
        
        logger.debug(f"Projekt erstellt: {self.name} (ID: {self.id})")

    def add_session(self, session):
        """
        Fügt eine Fotosession zum Projekt hinzu
        
        Args:
            session: PhotoSession-Instanz
        """
        self.sessions.append(session)
        self.updated_at = time.time()
        logger.debug(f"Session {session.id} zum Projekt {self.id} hinzugefügt")

    def get_session(self, session_id):
        """
        Gibt eine Session anhand ihrer ID zurück
        
        Args:
            session_id: Session-ID
            
        Returns:
            PhotoSession-Instanz oder None
        """
        for session in self.sessions:
            if session.id == session_id:
                return session
        return None

    def remove_session(self, session_id):
        """
        Entfernt eine Session aus dem Projekt
        
        Args:
            session_id: Session-ID
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        for i, session in enumerate(self.sessions):
            if session.id == session_id:
                del self.sessions[i]
                self.updated_at = time.time()
                logger.debug(f"Session {session_id} aus Projekt {self.id} entfernt")
                return True
        return False
    
    def add_image(self, image_path, angle=None, timestamp=None):
        """
        Fügt ein Bild zum Projekt hinzu
        
        Args:
            image_path: Pfad zum Bild
            angle: Optional, Winkel bei dem das Bild aufgenommen wurde
            timestamp: Optional, Zeitstempel wann das Bild aufgenommen wurde
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Sicherstellen, dass das Bild existiert
            if not os.path.exists(image_path):
                logger.error(f"Bild existiert nicht: {image_path}")
                return False
                
            # Sicherstellen, dass das Bild-Verzeichnis existiert
            images_dir = os.path.join(self.path, 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            # Bildmetadaten speichern
            image_info = {
                'path': os.path.relpath(image_path, self.path),
                'timestamp': timestamp or time.time(),
                'angle': angle
            }
            
            self.images.append(image_info)
            self.updated_at = time.time()
            
            # Projekt speichern
            self.save()
            
            return True
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Bildes: {str(e)}")
            return False

    def to_dict(self):
        """
        Konvertiert das Projekt in ein Dictionary
        
        Returns:
            Dictionary-Repräsentation des Projekts
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'angle_step': self.angle_step,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'sessions': [session.to_dict() for session in self.sessions],
            'path': self.path,
            'images': self.images
        }

    @classmethod
    def from_dict(cls, data):
        """
        Erstellt ein Projekt aus einem Dictionary
        
        Args:
            data: Dictionary mit Projektdaten
            
        Returns:
            Project-Instanz
        """
        project = cls(
            id=data.get('id'),
            name=data.get('name', "Unbenanntes Projekt"),
            description=data.get('description', ""),
            angle_step=data.get('angle_step', 5),
            path=data.get('path', "")
        )

        project.created_at = data.get('created_at', time.time())
        project.updated_at = data.get('updated_at', time.time())
        project.images = data.get('images', [])

        # Sessions laden
        for session_data in data.get('sessions', []):
            project.sessions.append(PhotoSession.from_dict(session_data))

        return project

    def save(self):
        """
        Speichert das Projekt
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self.path:
            logger.error(f"Kann Projekt {self.id} nicht speichern: Kein Pfad angegeben")
            return False

        try:
            # Sichere Pfadverarbeitung
            project_path = os.path.abspath(self.path)
            
            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(project_path, exist_ok=True)
            
            metadata_path = os.path.join(project_path, "project.json")
            
            # Metadaten-Datei speichern
            with open(metadata_path, 'w') as f:
                json.dump(self.to_dict(), f, indent=4)
                
            logger.debug(f"Projekt {self.id} gespeichert: {metadata_path}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern des Projekts {self.id}: {str(e)}")
            return False


class ProjectManager:
    """Klasse zur Verwaltung von Projekten"""

    def __init__(self, projects_dir):
        """
        Initialisiert den Projektmanager
        
        Args:
            projects_dir: Verzeichnis für Projekte
        """
        self.logger = logging.getLogger(__name__)
        self.projects_dir = projects_dir

        # Stelle sicher, dass das Projektverzeichnis existiert
        os.makedirs(self.projects_dir, exist_ok=True)
        
        self.logger.debug(f"ProjectManager initialisiert: {self.projects_dir}")

    def get_project_path(self, project_id):
        """
        Gibt den Pfad eines Projekts zurück
        
        Args:
            project_id: Projekt-ID
            
        Returns:
            Pfad zum Projekt
        """
        # Sichere Pfadverarbeitung
        if not project_id or '..' in project_id or '/' in project_id or '\\' in project_id:
            return None
            
        return secure_join(self.projects_dir, project_id)

    def get_all_projects(self):
        """
        Gibt eine Liste aller Projekte zurück
        
        Returns:
            Liste von Project-Instanzen
        """
        projects = []

        try:
            # Durchsuche das Projektverzeichnis nach Projektordnern
            for item in os.listdir(self.projects_dir):
                # Sichere Pfadverarbeitung
                project_path = secure_join(self.projects_dir, item)

                # Prüfen, ob es sich um ein Verzeichnis handelt
                if os.path.isdir(project_path):
                    # Prüfen, ob eine Projektdatei existiert
                    project_file = secure_join(project_path, "project.json")
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
        """
        Gibt ein Projekt anhand seiner ID zurück
        
        Args:
            project_id: Projekt-ID
            
        Returns:
            Project-Instanz oder None
        """
        # Sichere Pfadverarbeitung
        if not project_id or '..' in project_id or '/' in project_id or '\\' in project_id:
            return None
            
        project_path = secure_join(self.projects_dir, project_id)
        project_file = secure_join(project_path, "project.json")

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
        """
        Speichert ein Projekt
        
        Args:
            project: Project-Instanz
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Stelle sicher, dass das Projekt eine ID hat
            if not project.id:
                project.id = str(uuid.uuid4())
    
            # Projektpfad erstellen mit sicherer Pfadverarbeitung
            project_path = secure_join(self.projects_dir, project.id)
            os.makedirs(project_path, exist_ok=True)
    
            # Sessions-Verzeichnis erstellen
            sessions_path = secure_join(project_path, "sessions")
            os.makedirs(sessions_path, exist_ok=True)
            
            # Images-Verzeichnis erstellen
            images_path = secure_join(project_path, "images")
            os.makedirs(images_path, exist_ok=True)
    
            # Pfad im Projekt aktualisieren
            project.path = project_path
    
            # Projekt speichern
            success = project.save()
            
            if success:
                self.logger.info(f"Projekt erfolgreich gespeichert: {project.id} in {project_path}")
            else:
                self.logger.error(f"Fehler beim Speichern des Projekts: {project.id}")
                
            return success
        except Exception as e:
            self.logger.error(f"Fehler in save_project: {str(e)}")
            return False

    def delete_project(self, project_id):
        if not project_id or '..' in project_id or '/' in project_id or '\\' in project_id:
            return False

        project_path = secure_join(self.projects_dir, project_id)

        if os.path.isdir(project_path):
            try:
                # Warte kurz, um sicherzustellen, dass keine offenen Datei-Handles blockieren
                time.sleep(1)

                # Versuche, das Verzeichnis mehrfach zu löschen
                for _ in range(3):
                    shutil.rmtree(project_path, ignore_errors=True)
                    time.sleep(0.5)
                    if not os.path.exists(project_path):
                        break

                if os.path.exists(project_path):
                    raise Exception("Projektverzeichnis konnte nicht gelöscht werden")

                self.logger.info(f"Projekt {project_id} gelöscht")
                return True

            except Exception as e:
                self.logger.error(f"Fehler beim Löschen des Projekts {project_id}: {str(e)}")

        return False
