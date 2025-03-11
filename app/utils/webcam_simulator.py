#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/utils/webcam_simulator.py
Simuliert eine Webcam für Testzwecke
"""

import os
import time
import random
import logging
import cv2
import numpy as np
from datetime import datetime
from app.utils.webcam_detection_helper import find_working_webcam, test_webcam_capture
from app.utils.path_manager import PathManager

class WebcamCaptureSimulator:
    """Klasse zur Simulation einer Webcam"""
    
    def __init__(self, base_path=None, sample_images_path=None):
        """
        Initialisiert den Webcam-Capture-Simulator
        
        Args:
            base_path: Basisverzeichnis für Fotos (optional)
            sample_images_path: Verzeichnis mit Beispielbildern (optional)
        """
        # Logger einrichten
        self.logger = logging.getLogger(__name__)
        
        # Verzeichnisse
        path_manager = PathManager()
        self.base_path = base_path or path_manager.photos_dir
        self.sample_images_path = sample_images_path or path_manager.sample_images_dir

        # Sicherstellen, dass die Verzeichnisse existieren
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(self.sample_images_path, exist_ok=True)

        # Beste Kamera finden
        self.camera_device = self._find_best_camera_device()
        self.logger.debug(f"Webcam-Simulator initialisiert mit Kamera: {self.camera_device}")

    def _find_best_camera_device(self, preferred_devices=None):
        """
        Findet die beste Kamera
        
        Args:
            preferred_devices: Bevorzugte Geräte (optional)
            
        Returns:
            Pfad zum besten Gerät
        """
        # Bevorzugte Geräte festlegen, falls nicht angegeben
        if preferred_devices is None:
            preferred_devices = ['/dev/video0', '/dev/video1']

        # Funktionierende Webcam finden
        return find_working_webcam(preferred_devices)

    def capture_photo(self, filename=None):
        """
        Nimmt ein Foto auf oder simuliert es
        
        Args:
            filename: Name der Datei (optional)
            
        Returns:
            Pfad zum Foto
        """
        # Sicherstellen, dass das Verzeichnis existiert
        os.makedirs(self.base_path, exist_ok=True)

        # Falls kein Dateiname angegeben, einen generieren
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'webcam_photo_{timestamp}.jpg'

        # Sicherstellen, dass nur der Dateiname verwendet wird
        filename = os.path.basename(filename)

        # Vollständiger Pfad für das neue Bild
        full_path = os.path.join(self.base_path, filename)

        # Versuche, ein Foto mit der erkannten Kamera aufzunehmen
        if self.camera_device:
            try:
                success, captured_path = test_webcam_capture(self.camera_device)
                if success:
                    # Kopiere das aufgenommene Bild mit dem gewünschten Dateinamen
                    import shutil
                    shutil.copy(captured_path, full_path)
                    self.logger.info(f"Echtes Webcam-Foto aufgenommen: {full_path}")
                    return full_path
            except Exception as e:
                self.logger.error(f"Fehler bei der Kamera-Aufnahme: {e}")

        # Fallback auf Beispielbild
        sample_images = [
            f for f in os.listdir(self.sample_images_path)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]

        if sample_images:
            # Zufälliges Beispielbild auswählen
            selected_sample = random.choice(sample_images)
            sample_path = os.path.join(self.sample_images_path, selected_sample)

            # Beispielbild ins Fotoverzeichnis kopieren
            import shutil
            shutil.copy(sample_path, full_path)
            self.logger.info(f"Beispielbild verwendet: {selected_sample} -> {full_path}")
            return full_path

        # Letzter Ausweg: Leeres Bild erstellen
        blank_image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank_image, "No Image Available", (50, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imwrite(full_path, blank_image)
        self.logger.warning(f"Leeres Bild erstellt: {full_path}")
        return full_path

    def list_photos(self):
        """
        Listet alle Fotos im Basisverzeichnis auf
        
        Returns:
            Liste von Dateinamen
        """
        return [f for f in os.listdir(self.base_path)
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))]


# Globale Instanz für einfachen Zugriff
webcam_simulator = WebcamCaptureSimulator()

# Standalone-Verwendungsbeispiel
if __name__ == '__main__':
    # Logger konfigurieren
    logging.basicConfig(level=logging.DEBUG)
    
    # Webcam-Simulator initialisieren
    simulator = WebcamCaptureSimulator()

    # Einige Fotos aufnehmen
    for i in range(3):
        image_path = simulator.capture_photo()
        print(f"Foto {i+1}: {image_path}")

    # Aufgenommene Fotos auflisten
    print("\nAufgenommene Fotos:")
    for photo in simulator.list_photos():
        print(f"- {photo}")
