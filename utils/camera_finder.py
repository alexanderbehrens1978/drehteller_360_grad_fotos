# Datei: utils/camera_finder.py
# Modul zur Erkennung von Kameras (Webcams und gphoto2-Kameras)

import os
import logging
import subprocess
import re
import platform
import json


class CameraFinder:
    """Klasse zur Erkennung von Kameras (Webcams und gphoto2-Kameras)"""

    def __init__(self):
        """Initialisiert den Kamera-Finder"""
        self.logger = logging.getLogger(__name__)
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

    def find_cameras(self):
        """Findet alle angeschlossenen Webcams"""
        cameras = []

        try:
            if platform.system() == 'Linux':
                cameras = self._find_linux_webcams()
            elif platform.system() == 'Windows':
                cameras = self._find_windows_webcams()
            elif platform.system() == 'Darwin':  # macOS
                cameras = self._find_macos_webcams()
            else:
                self.logger.warning("Nicht unterstütztes Betriebssystem für Webcam-Erkennung")
        except Exception as e:
            self.logger.error(f"Fehler bei der Webcam-Suche: {str(e)}")

        return cameras

    def _find_linux_webcams(self):
        """Findet Webcams unter Linux mit v4l2-ctl"""
        cameras = []

        try:
            # Prüfen, ob v4l-utils installiert ist
            check_cmd = ['which', 'v4l2-ctl']
            check_result = subprocess.run(check_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if check_result.returncode != 0:
                self.logger.warning("v4l2-ctl nicht gefunden, verwende Fallback-Methode")
                return self._find_linux_webcams_fallback()

            # Geräteliste mit v4l2-ctl abfragen
            cmd = ['v4l2-ctl', '--list-devices']
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode != 0:
                self.logger.error(f"Fehler bei v4l2-ctl: {result.stderr}")
                return self._find_linux_webcams_fallback()

            # Ausgabe parsen
            current_device = None
            for line in result.stdout.splitlines():
                line = line.strip()

                if line and not line.startswith('/dev/'):
                    # Zeile enthält den Kameranamen
                    current_device = {
                        'name': line.rstrip(':'),
                        'device': None,
                        'type': 'webcam'
                    }
                elif line.startswith('/dev/video'):
                    # Zeile enthält den Gerätepfad
                    if current_device:
                        current_device['device'] = line
                        cameras.append(current_device)
                        current_device = None

        except Exception as e:
            self.logger.error(f"Fehler bei der Linux-Webcam-Erkennung: {str(e)}")
            return self._find_linux_webcams_fallback()

        return cameras

    def _find_linux_webcams_fallback(self):
        """Fallback-Methode zur Erkennung von Webcams unter Linux"""
        cameras = []

        try:
            # Suche nach /dev/video* Geräten
            video_devices = [f for f in os.listdir('/dev') if f.startswith('video')]

            for device in video_devices:
                device_path = f"/dev/{device}"
                cameras.append({
                    'name': f"Kamera {device}",
                    'device': device_path,
                    'type': 'webcam'
                })
        except Exception as e:
            self.logger.error(f"Fehler bei der Linux-Webcam-Fallback-Erkennung: {str(e)}")

        return cameras

    def _find_windows_webcams(self):
        """Findet Webcams unter Windows mit Python OpenCV"""
        cameras = []

        try:
            # Dies ist ein Platzhalter für die tatsächliche Windows-Implementierung
            # Da OpenCV keine Liste der verfügbaren Kameras bietet, müssen wir testen
            import cv2

            # Teste die ersten 10 Indizes
            for i in range(10):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Kameranamen erhalten (falls möglich)
                    name = f"Kamera {i}"
                    cameras.append({
                        'name': name,
                        'device': str(i),
                        'type': 'webcam'
                    })
                    cap.release()
        except Exception as e:
            self.logger.error(f"Fehler bei der Windows-Webcam-Erkennung: {str(e)}")

        return cameras

    def _find_macos_webcams(self):
        """Findet Webcams unter macOS"""
        cameras = []

        try:
            # Auf macOS verwenden wir system_profiler, um Kamerainformationen zu erhalten
            cmd = ['system_profiler', 'SPCameraDataType', '-json']
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    camera_data = data.get('SPCameraDataType', [])

                    for i, camera in enumerate(camera_data):
                        cameras.append({
                            'name': camera.get('_name', f"Kamera {i}"),
                            'device': str(i),  # macOS verwendet Indizes
                            'type': 'webcam'
                        })
                except json.JSONDecodeError:
                    self.logger.error("Fehler beim Parsen der macOS Kameradaten")
        except Exception as e:
            self.logger.error(f"Fehler bei der macOS-Webcam-Erkennung: {str(e)}")

        return cameras

    def find_gphoto_cameras(self):
        """Findet alle gphoto2-kompatiblen Kameras"""
        cameras = []

        if not self.gphoto2_available:
            self.logger.warning("gphoto2 ist nicht installiert, kann keine DSLR-Kameras erkennen")
            return cameras

        try:
            # gphoto2 --auto-detect ausführen
            cmd = ['gphoto2', '--auto-detect']
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if result.returncode != 0:
                self.logger.error(f"Fehler bei gphoto2 --auto-detect: {result.stderr}")
                return cameras

            # Ausgabe parsen
            # Typisches Format:
            # Model                          Port
            # ----------------------------------------------------------
            # Canon EOS 5D Mark III          usb:001,004

            lines = result.stdout.splitlines()
            if len(lines) <= 2:
                # Keine Kameras gefunden
                return cameras

            # Überspringe Header (erste zwei Zeilen)
            for line in lines[2:]:
                line = line.strip()
                if not line:
                    continue

                # Trenne Modell und Port
                parts = re.split(r'\s{2,}', line)
                if len(parts) == 2:
                    model, port = parts
                    cameras.append({
                        'name': model.strip(),
                        'device': port.strip(),
                        'type': 'gphoto2'
                    })

        except Exception as e:
            self.logger.error(f"Fehler bei der gphoto2-Kameraerkennung: {str(e)}")

        return cameras

    def test_webcam(self, device):
        """Testet, ob eine Webcam funktioniert"""
        try:
            import cv2

            # Gerätepfad oder Nummer
            if device.isdigit():
                device_id = int(device)
            else:
                device_id = device

            # Versuche, die Kamera zu öffnen
            cap = cv2.VideoCapture(device_id)

            if not cap.isOpened():
                self.logger.error(f"Webcam konnte nicht geöffnet werden: {device}")
                return False

            # Ein Frame lesen
            ret, frame = cap.read()

            # Kamera freigeben
            cap.release()

            return ret
        except Exception as e:
            self.logger.error(f"Fehler beim Testen der Webcam {device}: {str(e)}")
            return False

    def test_gphoto2_camera(self, port=None):
        """Testet, ob eine gphoto2-Kamera funktioniert"""
        if not self.gphoto2_available:
            self.logger.warning("gphoto2 ist nicht installiert")
            return False

        try:
            # Testbefehl zusammenstellen
            cmd = ['gphoto2', '--summary']

            # Wenn ein Port angegeben wurde
            if port:
                cmd.extend(['--port', port])

            # Befehl ausführen
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Fehler beim Testen der gphoto2-Kamera: {str(e)}")
            return False