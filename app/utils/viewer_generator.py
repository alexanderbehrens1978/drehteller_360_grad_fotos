#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/utils/viewer_generator.py
Generiert den 360°-Viewer aus einer Serie von Bildern
"""

import os
import json
import shutil
import logging
import time
from datetime import datetime
from PIL import Image
from app.utils.path_manager import PathManager

class ViewerGenerator:
    """Klasse zur Generierung eines 360°-Viewers aus Bildern"""
    
    def __init__(self, photo_dir=None, output_dir=None):
        """
        Initialisiert den Viewer-Generator
        
        Args:
            photo_dir: Verzeichnis mit den Quellfotos (optional)
            output_dir: Ausgabeverzeichnis für generierte Projekte (optional)
        """
        # Logger einrichten
        self.logger = logging.getLogger(__name__)
        
        # Verzeichnisse festlegen
        path_manager = PathManager()
        self.photo_dir = photo_dir or path_manager.photos_dir
        self.output_dir = output_dir or path_manager.projects_dir

        # Sicherstellen, dass das Ausgabeverzeichnis existiert
        os.makedirs(self.output_dir, exist_ok=True)
        self.logger.debug(f"Viewer-Generator initialisiert: {self.photo_dir} -> {self.output_dir}")

    def prepare_images(self, images, project_name):
        """
        Bereitet Bilder für den 360°-Viewer vor (Größenanpassung, Optimierung)
        
        Args:
            images: Liste der Bildpfade
            project_name: Name des Projekts
            
        Returns:
            Pfad zum Projektverzeichnis und Liste der verarbeiteten Bilder
        """
        project_dir = os.path.join(self.output_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)

        processed_images = []

        for i, img_path in enumerate(images):
            try:
                # Bild laden
                full_img_path = os.path.join(self.photo_dir, img_path)
                img = Image.open(full_img_path)

                # Größe anpassen (max. 1200px Breite für optimale Performance)
                max_width = 1200
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.LANCZOS)

                # Optimiertes Bild speichern
                img_filename = f"image_{i:03d}.jpg"
                output_path = os.path.join(project_dir, img_filename)
                img.save(output_path, "JPEG", quality=85, optimize=True)

                processed_images.append(img_filename)
                self.logger.debug(f"Bild {i+1}/{len(images)} verarbeitet: {img_path} -> {img_filename}")
            except Exception as e:
                self.logger.error(f"Fehler bei der Bildverarbeitung für {img_path}: {e}")

        return project_dir, processed_images

    def generate_viewer(self, images, metadata=None):
        """
        Generiert einen 360°-Viewer aus den gegebenen Bildern
        
        Args:
            images: Liste der Bildpfade
            metadata: Zusätzliche Metadaten für das Projekt (optional)
            
        Returns:
            URL zum erstellten Viewer
        """
        if not images:
            self.logger.error("Keine Bilder zum Generieren des Viewers gefunden")
            return None

        # Projektname erstellen (Zeitstempel)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"project_{timestamp}"

        # Bilder vorbereiten
        project_dir, processed_images = self.prepare_images(images, project_name)

        # Projektmetadaten erstellen
        project_metadata = {
            "name": metadata.get("name", project_name) if metadata else project_name,
            "created": time.time(),
            "image_count": len(processed_images),
            "images": processed_images,
            "user_metadata": metadata or {}
        }

        # Metadaten speichern
        metadata_path = os.path.join(project_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(project_metadata, f, indent=4)

        self.logger.info(f"Viewer für Projekt {project_name} mit {len(processed_images)} Bildern erstellt")
        return f"/viewer/cloudimage?project={project_name}"


# Globale Instanz für einfachen Zugriff
viewer_generator = ViewerGenerator()

# Standalone-Verwendungsbeispiel
if __name__ == '__main__':
    # Logger konfigurieren
    logging.basicConfig(level=logging.DEBUG)
    
    # Viewer-Generator erstellen
    generator = ViewerGenerator()
    
    # Beispieldaten
    test_images = [f for f in os.listdir(generator.photo_dir) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png'))][:5]
    
    if test_images:
        viewer_url = generator.generate_viewer(test_images, {"name": "Test-Projekt"})
        print(f"Viewer erstellt: {viewer_url}")
    else:
        print("Keine Bilder gefunden")
