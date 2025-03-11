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
import cv2
from pathlib import Path

# Logger einrichten
logger = logging.getLogger(__name__)

class CameraController:
    """Controller für die Kamerasteuerung (Webcam und gphoto2-Kameras)"""

    def __init__(self, camera_type='webcam', device='/dev/video0', resolution=None):
        """
        Initialisiert den Kamera-Controller
        
        Args:
            camera_type: Kameratyp ('webcam' oder 'gphoto2') (optional)
            device: Gerätepfad (optional)
            resolution: Auflösung als Tupel (Breite, Höhe) oder String 'BreitexHöhe' (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.camera_type = camera_type
        self.device = device

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

    def _setup_webcam(self):
        """
        Initialisiert die Webcam
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if self.webcam is None:
            try:
                # cv2.VideoCapture mit Nummer (0, 1, ...) oder Pfad (/dev/video0, ...)
                if str(self.device).isdigit():
                    device_id = int(self.device)
                else:
                    device_id = self.device

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
            # Stellen Sie sicher, dass das Verzeichnis existiert
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
            # Stellen Sie sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Zusammengesetzter gphoto2-Befehl
            cmd = [
                'gphoto2',
                '--capture-image-and-download',
                '--filename', output_path
            ]

            # Wenn eine bestimmte Kamera ausgewählt wurde (Port)
            if self.device and self.device != 'auto':
                cmd.extend(['--port', self.device])

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
