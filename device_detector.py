#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modul zur Erkennung von Kameras und Arduino-Geräten.
Erkennt automatisch verfügbare Geräte und aktualisiert regelmäßig die Liste.
"""

import os
import time
import logging
import subprocess
import glob
import threading
from serial.tools import list_ports

from webcam_detection_helper import find_working_webcam

# Logger konfigurieren
logger = logging.getLogger("drehteller360.device_detector")


class DeviceDetector:
    """Erkennt und verfolgt verfügbare Kameras und Arduino-Geräte."""

    def __init__(self, scan_interval=10):
        """
        Initialisiert den Gerätedetektor.

        Args:
            scan_interval: Zeit in Sekunden zwischen Geräte-Scans
        """
        self.scan_interval = scan_interval
        self.devices = {
            'cameras': {
                'webcams': [],
                'gphoto2': []
            },
            'arduinos': []
        }
        self.running = False
        self.lock = threading.Lock()

    def detect_webcams(self):
        """Erkennt angeschlossene Webcams."""
        webcam_devices = []

        try:
            # Videoeingabegeräte finden
            video_devices = glob.glob('/dev/video*')
            working_webcam = find_working_webcam(video_devices)

            if working_webcam:
                webcam_devices.append(working_webcam)

            for device in video_devices:
                if device != working_webcam and os.path.exists(device):
                    webcam_devices.append(device)
        except Exception as e:
            logger.error(f"Fehler bei der Webcam-Erkennung: {e}")

        return webcam_devices

    def detect_gphoto2_cameras(self):
        """Erkennt Kameras, die mit gphoto2 kompatibel sind."""
        gphoto2_cameras = []

        try:
            # Prüfen, ob gphoto2 installiert ist
            result = subprocess.run(['which', 'gphoto2'],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

            if result.returncode == 0:
                # Kameras auflisten
                result = subprocess.run(['gphoto2', '--auto-detect'],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True)

                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[2:]:  # Überschriften überspringen
                        if line.strip():
                            gphoto2_cameras.append(line.strip())
        except Exception as e:
            logger.error(f"Fehler bei der gphoto2-Kamera-Erkennung: {e}")

        return gphoto2_cameras

    def detect_arduinos(self):
        """Erkennt angeschlossene Arduino-Geräte."""
        arduino_devices = []

        try:
            # Serielle Ports auflisten
            ports = list(list_ports.comports())
            for port in ports:
                if "Arduino" in port.description or "ACM" in port.device:
                    arduino_devices.append({
                        'port': port.device,
                        'description': port.description
                    })
        except Exception as e:
            logger.error(f"Fehler bei der Arduino-Erkennung: {e}")

        return arduino_devices

    def scan_devices(self):
        """Scannt nach allen verfügbaren Geräten."""
        with self.lock:
            self.devices['cameras']['webcams'] = self.detect_webcams()
            self.devices['cameras']['gphoto2'] = self.detect_gphoto2_cameras()
            self.devices['arduinos'] = self.detect_arduinos()

        logger.info(f"Geräte erkannt: {len(self.devices['cameras']['webcams'])} Webcams, "
                    f"{len(self.devices['cameras']['gphoto2'])} gphoto2-Kameras, "
                    f"{len(self.devices['arduinos'])} Arduino-Geräte")

    def get_devices(self):
        """Gibt die aktuell erkannten Geräte zurück."""
        with self.lock:
            return self.devices.copy()

    def start_detection(self):
        """Startet den Erkennungsprozess in einer Schleife."""
        self.running = True

        while self.running:
            self.scan_devices()
            time.sleep(self.scan_interval)

    def stop_detection(self):
        """Stoppt den Erkennungsprozess."""
        self.running = False


# Globale Instanz für die Anwendung
device_detector = DeviceDetector()