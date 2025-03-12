#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/models/photo_session.py
Modell für eine Fotosession
"""

import os
import time
import uuid
import logging

# Logger einrichten
logger = logging.getLogger(__name__)

class PhotoSession:
    """Klasse zur Darstellung einer Fotosession"""

    def __init__(self, id=None, name="Neue Session", timestamp=None, angle_step=5):
        """
        Initialisiert eine Fotosession
        
        Args:
            id: Session-ID (optional)
            name: Sessionname (optional)
            timestamp: Zeitstempel (optional)
            angle_step: Winkelschritt in Grad (optional)
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.timestamp = timestamp or time.time()
        self.angle_step = angle_step
        self.photos = {}  # Dictionary mit Winkel als Schlüssel und Dateipfad als Wert
        self.completed = False
        
        logger.debug(f"PhotoSession erstellt: {self.name} (ID: {self.id})")

    def add_photo(self, angle, photo_path):
        """
        Fügt ein Foto zur Session hinzu
        
        Args:
            angle: Winkel in Grad
            photo_path: Pfad zum Foto
        """
        self.photos[angle] = photo_path
        logger.debug(f"Foto bei {angle}° zur Session {self.id} hinzugefügt: {photo_path}")

    def get_photo(self, angle):
        """
        Gibt den Pfad eines Fotos für einen bestimmten Winkel zurück
        
        Args:
            angle: Winkel in Grad
            
        Returns:
            Pfad zum Foto oder None
        """
        return self.photos.get(angle)

    def get_all_photos(self):
        """
        Gibt alle Fotos der Session zurück
        
        Returns:
            Liste von Fotopfaden, sortiert nach Winkel
        """
        # Sortieren nach Winkel
        return [self.photos[angle] for angle in sorted(self.photos.keys())]

    def to_dict(self):
        """
        Konvertiert die Session in ein Dictionary
        
        Returns:
            Dictionary-Repräsentation der Session
        """
        return {
            'id': self.id,
            'name': self.name,
            'timestamp': self.timestamp,
            'angle_step': self.angle_step,
            'photos': self.photos,
            'completed': self.completed
        }

    @classmethod
    def from_dict(cls, data):
        """
        Erstellt eine Session aus einem Dictionary
        
        Args:
            data: Dictionary mit Sessiondaten
            
        Returns:
            PhotoSession-Instanz
        """
        session = cls(
            id=data.get('id'),
            name=data.get('name', "Unbenannte Session"),
            timestamp=data.get('timestamp', time.time()),
            angle_step=data.get('angle_step', 5)
        )

        # String-Schlüssel in Integer umwandeln
        photos = data.get('photos', {})
        if isinstance(photos, dict):
            for angle, path in photos.items():
                try:
                    session.photos[int(angle)] = path
                except ValueError:
                    # Falls der Winkel kein gültiger Integer ist
                    session.photos[angle] = path
        
        session.completed = data.get('completed', False)

        return session
