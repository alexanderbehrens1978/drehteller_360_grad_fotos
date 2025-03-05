#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modul zur Generierung des 360°-Viewers aus einer Serie von Bildern.
Bereitet Bilder auf und erstellt HTML/JavaScript für den interaktiven Viewer.
"""

import os
import json
import shutil
import logging
import time
from datetime import datetime
from PIL import Image

# Logger konfigurieren
logger = logging.getLogger("drehteller360.viewer_generator")


class ViewerGenerator:
    """Generiert einen interaktiven 360°-Viewer aus einer Serie von Bildern."""

    def __init__(self, photo_dir='static/photos', output_dir='static/projects'):
        """
        Initialisiert den Viewer-Generator.

        Args:
            photo_dir: Verzeichnis mit den Quellfotos
            output_dir: Ausgabeverzeichnis für generierte Projekte
        """
        self.photo_dir = photo_dir
        self.output_dir = output_dir

        # Stelle sicher, dass das Ausgabeverzeichnis existiert
        os.makedirs(output_dir, exist_ok=True)

    def prepare_images(self, images, project_name):
        """
        Bereitet Bilder für den 360°-Viewer vor (Größenanpassung, Optimierung).

        Args:
            images: Liste der Bildpfade
            project_name: Name des Projekts

        Returns:
            Pfad zum Projektverzeichnis
        """
        project_dir = os.path.join(self.output_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)

        processed_images = []

        for i, img_path in enumerate(images):
            try:
                # Lade Bild
                img = Image.open(os.path.join(self.photo_dir, img_path))

                # Passe Größe an (max. 1200px Breite für optimale Performance)
                max_width = 1200
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.LANCZOS)

                # Speichere optimiertes Bild
                img_filename = f"image_{i:03d}.jpg"
                output_path = os.path.join(project_dir, img_filename)
                img.save(output_path, "JPEG", quality=85, optimize=True)

                processed_images.append(img_filename)
            except Exception as e:
                logger.error(f"Fehler bei der Bildverarbeitung für {img_path}: {e}")

        return project_dir, processed_images

    def generate_viewer(self, images, metadata=None):
        """
        Generiert einen 360°-Viewer aus den gegebenen Bildern.

        Args:
            images: Liste der Bildpfade
            metadata: Zusätzliche Metadaten für das Projekt

        Returns:
            URL zum erstellten Viewer
        """
        if not images:
            logger.error("Keine Bilder zum Generieren des Viewers gefunden")
            return None

        # Projektname erstellen (Zeitstempel)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"project_{timestamp}"

        # Bilder vorbereiten
        project_dir, processed_images = self.prepare_images(images, project_name)

        # Erstelle Projektmetadaten
        project_metadata = {
            "name": project_name,
            "created": time.time(),
            "image_count": len(processed_images),
            "images": processed_images,
            "user_metadata": metadata or {}
        }

        # Speichere Metadaten
        metadata_path = os.path.join(project_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(project_metadata, f)

        return f"/viewer?project={project_name}"


# Globale Instanz für die Anwendung
viewer_generator = ViewerGenerator()