#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/blueprints/main/utils.py
Hilfsfunktionen für die Hauptrouten
"""

import os
import time
import logging
import subprocess
import cv2
from app.utils.config_manager import config_manager
from app import arduino_controller, camera_controller
from app.utils.secure_path import secure_filename, secure_join

# Logger einrichten
logger = logging.getLogger(__name__)

def rotate_teller(degrees):
    """
    Dreht den Teller um den angegebenen Winkel
    
    Args:
        degrees: Drehwinkel in Grad
    """
    if arduino_controller is None or not arduino_controller.is_connected():
        logger.error("Arduino nicht verbunden!")
        return
    
    # Berechnung der Drehzeit basierend auf der Gradzahl (0,8 Grad pro Sekunde)
    rotation_time = degrees / 0.8
    
    # Relais einschalten (Drehteller starten)
    arduino_controller.turn_motor_on()
    time.sleep(rotation_time)  # Warte für die berechnete Zeit
    arduino_controller.turn_motor_off()
    
    logger.info(f"Drehteller um {degrees} Grad gedreht.")

def take_photo(project_id, filename=None):
    """
    Nimmt ein Foto auf und speichert es im Projektordner
    
    Args:
        project_id: ID des Projekts, in dem das Foto gespeichert werden soll
        filename: Optionaler Dateiname
        
    Returns:
        Pfad zum gespeicherten Foto
    """
    
    try:
        # Stelle sicher, dass nur der Dateiname verwendet wird
        if filename:
            filename = os.path.basename(filename)
        else:
            # Generiere einen Dateinamen, wenn keiner angegeben wurde
            timestamp = int(time.time())
            filename = f'photo_{timestamp}.jpg'
            
        # Projektverzeichnis ermitteln
        from app.utils.path_manager import PathManager
        path_manager = PathManager()
        
        # Pfad zum Projektverzeichnis erstellen
        project_path = path_manager.get_project_path(project_id)
        
        # Stelle sicher, dass das Bilder-Verzeichnis im Projekt existiert
        images_dir = os.path.join(project_path, 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        # Vollständiger Pfad zum Foto
        full_path = os.path.join(images_dir, filename)
        
        # Reale Kamera verwenden
        if camera_controller:
            success = camera_controller.capture_photo(full_path)
            if success:
                logger.info(f"Foto aufgenommen und als {filename} gespeichert.")
                return full_path
            else:
                logger.error(f"Fehler beim Aufnehmen des Fotos mit dem Kamera-Controller.")
                return None
        else:
            logger.error("Kein Kamera-Controller verfügbar.")
            return None
    except Exception as e:
        logger.error(f"Fehler beim Aufnehmen des Fotos: {e}")
        return None




