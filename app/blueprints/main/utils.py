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

# Logger einrichten
logger = logging.getLogger(__name__)

def rotate_teller(degrees):
    """
    Dreht den Teller um den angegebenen Winkel
    
    Args:
        degrees: Drehwinkel in Grad
    """
    # Prüfen, ob Simulator aktiviert ist
    USE_SIMULATOR = config_manager.get('simulator.enabled', True)
    
    if USE_SIMULATOR:
        logger.info(f"Simulierte Rotation: {degrees} Grad")
        return
    
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

def take_photo(filename=None):
    """
    Nimmt ein Foto auf
    
    Args:
        filename: Optionaler Dateiname
        
    Returns:
        Pfad zum gespeicherten Foto
    """
    # Prüfen, ob Simulator aktiviert ist
    USE_SIMULATOR = config_manager.get('simulator.enabled', True)
    
    if USE_SIMULATOR:
        # Webcam-Simulator verwenden
        from app.utils.webcam_simulator import webcam_simulator
        
        # Stelle sicher, dass nur der Dateiname verwendet wird
        if filename:
            filename = os.path.basename(filename)
            
        return webcam_simulator.capture_photo(filename)
    
    try:
        # Kameraeinstellungen aus der Konfiguration holen
        camera_device = config_manager.get('camera.device_path', '/dev/video0')
        camera_type = config_manager.get('camera.type', 'webcam')
        
        # Kamera-Auflösung holen
        camera_width = config_manager.get('camera.resolution.width')
        camera_height = config_manager.get('camera.resolution.height')
        
        # Kamera-Controller verwenden, falls verfügbar
        if camera_controller:
            if not filename:
                filename = f'photo_{int(time.time())}.jpg'
                
            # Stelle sicher, dass nur der Dateiname verwendet wird
            filename = os.path.basename(filename)
            full_path = os.path.join('static/photos', filename)
            
            # Foto aufnehmen
            success = camera_controller.capture_photo(full_path)
            
            if success:
                logger.info(f"Foto aufgenommen und als {filename} gespeichert.")
                return filename
            else:
                logger.error(f"Fehler beim Aufnehmen des Fotos mit dem Kamera-Controller.")
                return None
        
        # Fallback: Direkte Kamerasteuerung
        if not filename:
            filename = f'photo_{int(time.time())}.jpg'
        
        # Stelle sicher, dass nur der Dateiname verwendet wird
        filename = os.path.basename(filename)
        full_path = os.path.join('static/photos', filename)
        
        # Stelle sicher, dass das Verzeichnis existiert
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Wähle die Aufnahmemethode basierend auf dem Kameratyp
        if camera_type == 'gphoto2':
            # gphoto2 für DSLR-Kameras verwenden
            subprocess.call(['gphoto2', '--capture-image-and-download', '--filename', full_path])
        else:
            # OpenCV für Webcams verwenden
            cap = cv2.VideoCapture(camera_device)
            
            # Auflösung einstellen, falls angegeben
            if camera_width and camera_height:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
            
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(full_path, frame)
                cap.release()
            else:
                # Fallback zu fswebcam, falls OpenCV fehlschlägt
                subprocess.call(['fswebcam', '--no-banner', 
                                '-d', camera_device, 
                                full_path])
        
        logger.info(f"Foto aufgenommen und als {filename} gespeichert.")
        return filename
    except Exception as e:
        logger.error(f"Fehler beim Aufnehmen des Fotos: {e}")
        return None
