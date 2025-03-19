# Datei: models/photo_session.py
# Modul für das Fotosession-Datenmodell

import os
import time
import uuid
import logging
from pathlib import Path


class PhotoSession:
    """Klasse zur Darstellung einer Fotosession"""

    def __init__(self, id=None, name="Neue Session", timestamp=None, angle_step=5):
        """Initialisiert eine Fotosession"""
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.timestamp = timestamp or time.time()
        self.angle_step = angle_step
        self.photos = {}  # Dictionary mit Winkel als Schlüssel und Dateipfad als Wert
        self.completed = False

    def add_photo(self, angle, photo_path):
        """Fügt ein Foto zur Session hinzu"""
        self.photos[angle] = photo_path

    def get_photo(self, angle):
        """Gibt den Pfad eines Fotos für einen bestimmten Winkel zurück"""
        return self.photos.get(angle)

    def get_all_photos(self):
        """Gibt alle Fotos der Session zurück"""
        # Sortieren nach Winkel
        return [self.photos[angle] for angle in sorted(self.photos.keys())]

    def to_dict(self):
        """Konvertiert die Session in ein Dictionary"""
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
        """Erstellt eine Session aus einem Dictionary"""
        session = cls(
            id=data.get('id'),
            name=data.get('name', "Unbenannte Session"),
            timestamp=data.get('timestamp', time.time()),
            angle_step=data.get('angle_step', 5)
        )

        session.photos = data.get('photos', {})
        session.completed = data.get('completed', False)

        return session