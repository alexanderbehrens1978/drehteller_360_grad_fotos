#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/utils/path_manager.py
Verwaltet Dateipfade und stellt sicher, dass erforderliche Verzeichnisse existieren
"""

import os
import logging

class PathManager:
    """Klasse zur Verwaltung von Dateipfaden und Verzeichnissen"""
    
    def __init__(self):
        """Initialisiert den Path Manager"""
        self.logger = logging.getLogger(__name__)
        self.base_dir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        # Wichtige Verzeichnisse
        self.static_dir = os.path.join(self.base_dir, 'static')
        self.photos_dir = os.path.join(self.static_dir, 'photos')
        self.sample_images_dir = os.path.join(self.static_dir, 'sample_images')
        self.projects_dir = os.path.join(self.static_dir, 'projects')
        self.temp_dir = os.path.join(self.static_dir, 'temp')
        
        self.logger.debug(f"PathManager initialisiert mit Basis-Verzeichnis: {self.base_dir}")
    
    def ensure_directories(self):
        """Stellt sicher, dass alle erforderlichen Verzeichnisse existieren"""
        dirs_to_create = [
            self.static_dir,
            self.photos_dir,
            self.sample_images_dir,
            self.projects_dir,
            self.temp_dir
        ]
        
        for directory in dirs_to_create:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.logger.info(f"Verzeichnis erstellt: {directory}")
            else:
                self.logger.debug(f"Verzeichnis existiert bereits: {directory}")
    
    def get_photo_path(self, filename=None):
        """
        Gibt den vollständigen Pfad zu einem Foto zurück
        
        Args:
            filename: Name der Datei (optional)
            
        Returns:
            Vollständiger Pfad zum Foto oder zum Fotos-Verzeichnis
        """
        if filename:
            return os.path.join(self.photos_dir, filename)
        return self.photos_dir
    
    def get_project_path(self, project_id=None):
        """
        Gibt den vollständigen Pfad zu einem Projekt zurück
        
        Args:
            project_id: ID des Projekts (optional)
            
        Returns:
            Vollständiger Pfad zum Projekt oder zum Projekte-Verzeichnis
        """
        if project_id:
            return os.path.join(self.projects_dir, project_id)
        return self.projects_dir
    
    def get_sample_image_path(self, filename=None):
        """
        Gibt den vollständigen Pfad zu einem Beispielbild zurück
        
        Args:
            filename: Name der Datei (optional)
            
        Returns:
            Vollständiger Pfad zum Beispielbild oder zum Beispielbilder-Verzeichnis
        """
        if filename:
            return os.path.join(self.sample_images_dir, filename)
        return self.sample_images_dir
    
    def get_project_photo_path(self, project_id, session_id, filename):
        """
        Gibt den vollständigen Pfad zu einem Projektfoto zurück
        
        Args:
            project_id: ID des Projekts
            session_id: ID der Session
            filename: Name der Datei
            
        Returns:
            Vollständiger Pfad zum Projektfoto
        """
        session_dir = os.path.join(self.get_project_path(project_id), 'sessions', session_id)
        
        # Stelle sicher, dass das Session-Verzeichnis existiert
        if not os.path.exists(session_dir):
            os.makedirs(session_dir)
            self.logger.debug(f"Session-Verzeichnis erstellt: {session_dir}")
        
        return os.path.join(session_dir, filename)
