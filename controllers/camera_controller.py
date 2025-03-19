# Datei: controllers/camera_controller.py
# Modul zur Steuerung von Kameras (Webcam und gphoto2-Kameras)

import os
import time
import logging
import subprocess
import cv2
from pathlib import Path


class CameraController:
    """Klasse zur Steuerung der Kamera (Webcam oder gphoto2-Kamera)"""

    def __init__(self, camera_type='webcam', device='/dev/video0', resolution=(1920, 1080)):
        """Initialisiert den Kameracontroller"""
        self.logger = logging.getLogger(__name__)
        self.camera_type = camera_type
        self.device = device

        # Auflösung als Tupel (Breite, Höhe)
        if isinstance(resolution, str) and 'x' in resolution:
            width, height = resolution.split('x')
            self.resolution = (int(width), int(height))
        elif isinstance(resolution, tuple) and len(resolution) == 2:
            self.resolution = resolution
        else:
            self.resolution = (1920, 1080)  # Standardauflösung

        self.webcam = None
        self.gphoto2_available = self._check_gphoto2()

    def _check_gphoto2(self):
        """Prüft, ob gphoto2 installiert ist"""
        try:
            result = subprocess.run(['which', 'gphoto2'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            return result.returncode == 0
        except Exception:
            return False

    def _setup_webcam(self):
        """Initialisiert die Webcam"""
        if self.webcam is None:
            try:
                # cv2.VideoCapture mit Nummer (0, 1, ...) oder Pfad (/dev/video0, ...)
                if self.device.isdigit():
                    device_id = int(self.device)
                else:
                    device_id = self.device

                self.webcam = cv2.VideoCapture(device_id)

                # Auflösung einstellen
                self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

                if not self.webcam.isOpened():
                    self.logger.error("Webcam konnte nicht geöffnet werden: %s", self.device)
                    self.webcam = None
                    return False

                self.logger.info("Webcam erfolgreich initialisiert: %s", self.device)
                return True
            except Exception as e:
                self.logger.error("Fehler bei der Webcam-Initialisierung: %s", str(e))
                self.webcam = None
                return False
        return True

    def _close_webcam(self):
        """Schließt die Webcam"""
        if self.webcam is not None:
            self.webcam.release()
            self.webcam = None

    def capture_webcam_photo(self, output_path):
        """Nimmt ein Foto mit der Webcam auf"""
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
                self.logger.info("Webcam-Foto gespeichert: %s", output_path)
                return True
            else:
                self.logger.error("Fehler beim Speichern des Webcam-Fotos: %s", output_path)
                return False
        except Exception as e:
            self.logger.error("Fehler bei der Webcam-Fotoaufnahme: %s", str(e))
            return False

    def capture_gphoto2_photo(self, output_path):
        """Nimmt ein Foto mit einer gphoto2-kompatiblen Kamera auf"""
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
            self.logger.debug("gphoto2-Befehl: %s", ' '.join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info("gphoto2-Foto gespeichert: %s", output_path)
                return True
            else:
                self.logger.error("gphoto2-Fehler: %s", result.stderr)
                return False
        except Exception as e:
            self.logger.error("Fehler bei der gphoto2-Fotoaufnahme: %s", str(e))
            return False

    def capture_photo(self, output_path):
        """Nimmt ein Foto auf (je nach Kameratyp)"""
        if self.camera_type == 'webcam':
            return self.capture_webcam_photo(output_path)
        elif self.camera_type == 'gphoto2':
            return self.capture_gphoto2_photo(output_path)
        else:
            self.logger.error("Unbekannter Kameratyp: %s", self.camera_type)
            return False

    def cleanup(self):
        """Ressourcen freigeben, wenn die Kamera nicht mehr benötigt wird"""
        self._close_webcam()