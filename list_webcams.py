#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
list_webcams.py
Dieses Skript listet alle verfügbaren Webcams auf und ermöglicht es,
eine davon auszuwählen und in der Konfiguration zu speichern.
"""

import os
import sys
import json
import logging
from utils.camera_finder import CameraFinder
from app.utils.config_manager import config_manager

# Logger einrichten
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_and_select_webcam():
    """Listet alle verfügbaren Webcams auf und ermöglicht die Auswahl"""
    try:
        # Kamera-Finder initialisieren
        finder = CameraFinder()
        
        # Verfügbare Kameras abrufen
        cameras = finder.find_cameras()
        
        if not cameras:
            print("Keine Kameras gefunden.")
            return
        
        # Aktuelle Konfiguration laden
        current_camera_type = config_manager.get('camera.type', 'webcam')
        current_device = config_manager.get('camera.device_path', '')
        
        print("\n=== Verfügbare Kameras ===")
        print(f"Aktuelle Konfiguration: Typ={current_camera_type}, Gerät={current_device}")
        print("-" * 50)
        
        # Kameras auflisten
        for i, camera in enumerate(cameras):
            is_current = current_device == camera.get('device')
            current_marker = "* " if is_current else "  "
            print(f"{current_marker}[{i+1}] {camera.get('name', 'Unbekannt')} ({camera.get('type', 'Unbekannt')})")
            print(f"    Gerät: {camera.get('device', 'Nicht verfügbar')}")
            print()
        
        # Benutzerauswahl
        try:
            selection = input("Wähle eine Kamera aus (Nummer) oder drücke Enter zum Abbrechen: ")
            
            if not selection.strip():
                print("Auswahl abgebrochen.")
                return
            
            index = int(selection) - 1
            if 0 <= index < len(cameras):
                selected_camera = cameras[index]
                camera_type = selected_camera.get('type', 'webcam')
                device_path = selected_camera.get('device', '')
                
                # Konfiguration aktualisieren
                config = config_manager.config.copy()
                config['camera'] = config.get('camera', {})
                config['camera']['type'] = camera_type
                config['camera']['device_path'] = device_path
                
                # Konfiguration speichern
                if config_manager.save_config(config):
                    print(f"Kamera erfolgreich gespeichert: {selected_camera.get('name')} ({device_path})")
                else:
                    print("Fehler beim Speichern der Konfiguration.")
            else:
                print("Ungültige Auswahl.")
        except ValueError:
            print("Ungültige Eingabe. Bitte gib eine Zahl ein.")
    except Exception as e:
        logger.error(f"Fehler: {str(e)}")
        print(f"Ein Fehler ist aufgetreten: {str(e)}")

if __name__ == "__main__":
    list_and_select_webcam()
