#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/controllers/camera_controller.py
Controller für die Kamerasteuerung
"""

import os
import time
import logging
import subprocess
import json
import cv2
from pathlib import Path

# Logger einrichten
logger = logging.getLogger(__name__)

class CameraController:
    """Controller für die Kamerasteuerung (Webcam und gphoto2-Kameras)"""

    def __init__(self, camera_type='webcam', device='/dev/video0', resolution=None, camera_settings=None):
        """
        Initialisiert den Kamera-Controller
        
        Args:
            camera_type: Kameratyp ('webcam' oder 'gphoto2') (optional)
            device: Gerätepfad (optional)
            resolution: Auflösung als Tupel (Breite, Höhe) oder String 'BreitexHöhe' (optional)
            camera_settings: Spezifische Kameraeinstellungen für gphoto2 (optional)
        """
        self.logger = logging.getLogger(__name__)
        
        # Explizite Überprüfung und Protokollierung des übergebenen Kameratyps
        self.logger.info(f"CameraController wird initialisiert mit Typ={camera_type}, Gerät={device}")
        
        # Sicherstellen, dass camera_type korrekt ist und nicht überschrieben wird
        self.camera_type = camera_type
        self.device = device
        self.camera_settings = camera_settings or {}

        # Auflösung als Tupel (Breite, Höhe)
        if isinstance(resolution, str) and 'x' in resolution:
            width, height = resolution.split('x')
            self.resolution = (int(width), int(height))
        elif isinstance(resolution, tuple) and len(resolution) == 2:
            self.resolution = resolution
        elif isinstance(resolution, dict) and 'width' in resolution and 'height' in resolution:
            self.resolution = (resolution['width'], resolution['height'])
        else:
            self.resolution = (1920, 1080)  # Standardauflösung

        self.webcam = None
        self.gphoto2_available = self._check_gphoto2()
        
        self.logger.debug(f"CameraController initialisiert: Typ={self.camera_type}, Gerät={self.device}, "
                        f"Auflösung={self.resolution}")

    def _check_gphoto2(self):
        """
        Prüft, ob gphoto2 installiert ist
        
        Returns:
            True wenn gphoto2 verfügbar ist, sonst False
        """
        try:
            result = subprocess.run(['which', 'gphoto2'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception as e:
            self.logger.warning(f"Konnte gphoto2 nicht überprüfen: {str(e)}")
            return False
    
    def detect_cameras(self):
        """
        Erkennt verfügbare Kameras (gphoto2 und Webcams)
        
        Returns:
            Dictionary mit erkannten Kameras
        """
        cameras = {
            'webcams': [],
            'gphoto2': []
        }
        
        # Webcams erkennen
        try:
            from app.utils.webcam_detection_helper import find_working_webcam
            
            # Linux: Nach /dev/video* Geräten suchen
            import glob
            video_devices = glob.glob('/dev/video*')
            
            # Teste jedes Gerät
            for device in video_devices:
                try:
                    cap = cv2.VideoCapture(device)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        if ret:
                            cameras['webcams'].append({
                                'device': device,
                                'name': f"Webcam an {device}",
                                'model': 'Generic Webcam',
                                'status': 'working'
                            })
                        else:
                            cameras['webcams'].append({
                                'device': device,
                                'name': f"Webcam an {device}",
                                'model': 'Generic Webcam',
                                'status': 'error'
                            })
                    cap.release()
                except Exception as e:
                    self.logger.debug(f"Fehler beim Testen von {device}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Fehler bei der Webcam-Erkennung: {str(e)}")
        
        # gphoto2-Kameras erkennen
        if self.gphoto2_available:
            try:
                result = subprocess.run(['gphoto2', '--auto-detect'],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    
                    # Die ersten beiden Zeilen sind Header
                    if len(lines) > 2:
                        for line in lines[2:]:
                            if line.strip():
                                try:
                                    model, port = line.strip().split("usb:")
                                    model = model.strip()
                                    port = "usb:" + port.strip()
                                    
                                    cameras['gphoto2'].append({
                                        'device': port,
                                        'name': model,
                                        'model': model,
                                        'status': 'available'
                                    })
                                except Exception as e:
                                    self.logger.debug(f"Fehler beim Parsen der Kamerazeile: {line}, {str(e)}")
            except Exception as e:
                self.logger.error(f"Fehler bei der gphoto2-Kameraerkennung: {str(e)}")
                
        return cameras
        
    def get_camera_capabilities(self, device, camera_type='gphoto2'):
        """
        Ruft die Fähigkeiten einer Kamera ab
        
        Args:
            device: Gerätepfad
            camera_type: Kameratyp ('webcam' oder 'gphoto2')
            
        Returns:
            Dictionary mit den Fähigkeiten der Kamera
        """
        capabilities = {}
        
        if camera_type == 'gphoto2' and self.gphoto2_available:
            try:
                # Geräteoptionen ausgeben
                result = subprocess.run(['gphoto2', '--port', device, '--list-config'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       text=True)
                
                if result.returncode == 0:
                    configs = result.stdout.strip().split('\n')
                    capabilities['configs'] = configs
                    
                    # Kameraeinstellungen
                    settings = {}
                    
                    # Wichtige Einstellungen ausgeben
                    for config in configs:
                        if any(key in config for key in ['shutterspeed', 'iso', 'aperture', 'imageformat']):
                            try:
                                value_result = subprocess.run(['gphoto2', '--port', device, '--get-config', config],
                                                            stdout=subprocess.PIPE,
                                                            stderr=subprocess.PIPE,
                                                            text=True)
                                
                                if value_result.returncode == 0:
                                    values = {}
                                    for line in value_result.stdout.strip().split('\n'):
                                        if ':' in line:
                                            key, value = line.split(':', 1)
                                            values[key.strip()] = value.strip()
                                    
                                    settings[config] = values
                            except Exception as e:
                                self.logger.debug(f"Fehler beim Abrufen der Konfiguration {config}: {str(e)}")
                    
                    capabilities['settings'] = settings
                    
                    # Kameramodell hinzufügen
                    try:
                        summary_result = subprocess.run(['gphoto2', '--port', device, '--summary'],
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE,
                                                    text=True)
                        
                        if summary_result.returncode == 0:
                            summary = summary_result.stdout
                            capabilities['summary'] = summary
                            
                            # Modell aus Summary extrahieren
                            for line in summary.split('\n'):
                                if 'Model:' in line:
                                    capabilities['model'] = line.split('Model:', 1)[1].strip()
                                    break
                    except Exception as e:
                        self.logger.debug(f"Fehler beim Abrufen der Kamerazusammenfassung: {str(e)}")
            except Exception as e:
                self.logger.error(f"Fehler beim Abrufen der gphoto2-Fähigkeiten: {str(e)}")
        
        elif camera_type == 'webcam':
            try:
                from app.utils.webcam_detection_helper import get_camera_capabilities
                webcam_caps = get_camera_capabilities(device)
                capabilities.update(webcam_caps)
            except Exception as e:
                self.logger.error(f"Fehler beim Abrufen der Webcam-Fähigkeiten: {str(e)}")
                
        return capabilities

    def _setup_webcam(self):
        """
        Initialisiert die Webcam
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if self.webcam is None:
            try:
                # Verbesserte Geräte-ID-Extraktion für verschiedene Formate
                device_id = self.device
                
                # Für numerische IDs (z.B. "0", "1", "2")
                if str(self.device).isdigit():
                    device_id = int(self.device)
                # Für /dev/videoX Pfade - extrahiere die Nummer
                elif isinstance(self.device, str) and self.device.startswith('/dev/video'):
                    try:
                        # Extrahiere die Nummer aus "/dev/videoX"
                        video_num = self.device.split('video')[1]
                        if video_num.isdigit():
                            device_id = int(video_num)
                            self.logger.info(f"Verwende Gerätenummer {device_id} für {self.device}")
                    except Exception as e:
                        self.logger.warning(f"Konnte Gerätenummer nicht aus {self.device} extrahieren: {str(e)}")
                
                self.logger.info(f"Öffne Kamera mit device_id: {device_id}")
                self.webcam = cv2.VideoCapture(device_id)

                # Auflösung einstellen
                self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

                if not self.webcam.isOpened():
                    self.logger.error(f"Webcam konnte nicht geöffnet werden: {self.device}")
                    self.webcam = None
                    return False

                self.logger.info(f"Webcam erfolgreich initialisiert: {self.device}")
                return True
            except Exception as e:
                self.logger.error(f"Fehler bei der Webcam-Initialisierung: {str(e)}")
                self.webcam = None
                return False
        return True

    def _close_webcam(self):
        """Schließt die Webcam"""
        if self.webcam is not None:
            self.webcam.release()
            self.webcam = None
            self.logger.debug("Webcam-Verbindung geschlossen")

    def capture_webcam_photo(self, output_path):
        """
        Nimmt ein Foto mit der Webcam auf
        
        Args:
            output_path: Pfad für das aufgenommene Foto
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self._setup_webcam():
            return False

        try:
            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Mehrere Frames lesen, um sicherzustellen, dass die Kamera sich angepasst hat
            for _ in range(5):
                ret, frame = self.webcam.read()
                if not ret:
                    self.logger.error("Fehler beim Lesen des Webcam-Frames")
                    return False
                time.sleep(0.1)

            # Letzten Frame speichern
            success = cv2.imwrite(output_path, frame)

            if success:
                self.logger.info(f"Webcam-Foto gespeichert: {output_path}")
                return True
            else:
                self.logger.error(f"Fehler beim Speichern des Webcam-Fotos: {output_path}")
                return False
        except Exception as e:
            self.logger.error(f"Fehler bei der Webcam-Fotoaufnahme: {str(e)}")
            return False
        finally:
            # Webcam wieder freigeben
            self._close_webcam()

    def capture_gphoto2_photo(self, output_path):
        """
        Nimmt ein Foto mit einer gphoto2-kompatiblen Kamera auf
        
        Args:
            output_path: Pfad für das aufgenommene Foto
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self.gphoto2_available:
            self.logger.error("gphoto2 ist nicht installiert oder nicht verfügbar")
            return False

        try:
            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Basis-Befehl für gphoto2
            cmd = [
                'gphoto2',
                '--capture-image-and-download',
                '--filename', output_path
            ]

            # Wenn eine bestimmte Kamera ausgewählt wurde (Port)
            if self.device and self.device != 'auto':
                cmd.extend(['--port', self.device])
            
            # Kamera-spezifische Einstellungen hinzufügen, falls vorhanden
            for setting, value in self.camera_settings.items():
                if setting.startswith('/') and value:  # gphoto2 Konfigurationen beginnen mit /
                    cmd.extend(['--set-config', f"{setting}={value}"])

            # gphoto2-Befehl ausführen
            self.logger.debug(f"gphoto2-Befehl: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info(f"gphoto2-Foto gespeichert: {output_path}")
                return True
            else:
                self.logger.error(f"gphoto2-Fehler: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Fehler bei der gphoto2-Fotoaufnahme: {str(e)}")
            return False

    def capture_photo(self, output_path):
        """
        Nimmt ein Foto auf (je nach Kameratyp)
        
        Args:
            output_path: Pfad für das aufgenommene Foto
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        self.logger.info(f"Foto wird aufgenommen mit Kameratyp: {self.camera_type}, Gerät: {self.device}")
        
        if self.camera_type == 'webcam':
            return self.capture_webcam_photo(output_path)
        elif self.camera_type == 'gphoto2':
            return self.capture_gphoto2_photo(output_path)
        else:
            self.logger.error(f"Unbekannter Kameratyp: {self.camera_type}")
            return False

    def cleanup(self):
        """Ressourcen freigeben, wenn die Kamera nicht mehr benötigt wird"""
        self._close_webcam()
