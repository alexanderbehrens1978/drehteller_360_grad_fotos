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
        
        # Alle Video-Geräte erkennen
        try:
            import glob
            video_devices = glob.glob('/dev/video*')
            
            # Teste jedes Gerät
            for device in video_devices:
                try:
                    # Prüfen, ob es eine DSLR oder eine Webcam ist
                    is_dslr = False
                    device_name = f"Gerät an {device}"
                    
                    # Versuche, Kamerainformationen mit v4l2-ctl zu bekommen
                    try:
                        # Mehr Informationen über das Gerät sammeln
                        device_manufacturer = ""
                        device_product = ""
                        device_model = ""
                        
                        # Versuche zuerst Informationen aus v4l2-ctl --info zu bekommen
                        result = subprocess.run(['v4l2-ctl', '--device', device, '--info'],
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE,
                                             text=True)
                        
                        if result.returncode == 0:
                            for line in result.stdout.strip().split('\n'):
                                if 'Card type' in line:
                                    device_info = line.split(':', 1)[1].strip()
                                    device_name = device_info
                                    # Wenn im Namen Nikon oder Canon vorkommt, ist es eine DSLR
                                    if any(brand in device_info for brand in ['Nikon', 'Canon', 'DSLR']):
                                        is_dslr = True
                                        break
                                elif 'Driver name' in line:
                                    device_model = line.split(':', 1)[1].strip()
                        
                        # Zusätzliche Informationen aus v4l2-ctl --list-devices und udevadm holen
                        if not is_dslr:
                            try:
                                # Geräte-Details mit udevadm erfragen für zusätzliche Infos
                                udev_result = subprocess.run(['udevadm', 'info', '--name=' + device, '--query=property'],
                                                         stdout=subprocess.PIPE,
                                                         stderr=subprocess.PIPE,
                                                         text=True)
                                
                                if udev_result.returncode == 0:
                                    for line in udev_result.stdout.strip().split('\n'):
                                        if 'ID_VENDOR=' in line:
                                            device_manufacturer = line.split('=', 1)[1].replace('_', ' ').title()
                                        elif 'ID_MODEL=' in line:
                                            device_product = line.split('=', 1)[1].replace('_', ' ').title()
                                        elif 'ID_VENDOR_FROM_DATABASE=' in line:
                                            device_manufacturer = line.split('=', 1)[1]
                                        elif 'ID_MODEL_FROM_DATABASE=' in line:
                                            device_product = line.split('=', 1)[1]
                            except Exception as e:
                                self.logger.debug(f"Fehler beim Abrufen der udevadm-Informationen: {str(e)}")
                            
                            # Sinnvollen Namen aus allen Informationen bilden
                            if device_manufacturer and device_product:
                                device_name = f"{device_manufacturer} {device_product}"
                            elif device_manufacturer:
                                device_name = f"{device_manufacturer} Webcam"
                            elif device_product:
                                device_name = device_product
                            elif device_model:
                                device_name = f"Webcam ({device_model})"
                            else:
                                device_name = f"Webcam an {device}"
                    except Exception as e:
                        self.logger.debug(f"Fehler beim Abrufen der Geräteinformationen mit v4l2-ctl: {str(e)}")
                    
                    # Testen, ob das Gerät funktioniert
                    cap = cv2.VideoCapture(device)
                    device_working = False
                    
                    if cap.isOpened():
                        ret, frame = cap.read()
                        device_working = ret
                        cap.release()
                    
                    # Kamera dem passenden Typ zuordnen
                    if is_dslr:
                        # Wenn es eine DSLR ist, zur gphoto2-Liste hinzufügen
                        cameras['gphoto2'].append({
                            'device': device,
                            'name': f"DSLR {device_name}",
                            'model': 'DSLR via V4L2',
                            'status': 'working' if device_working else 'detected'
                        })
                    else:
                        # Andernfalls ist es eine Webcam
                        cameras['webcams'].append({
                            'device': device,
                            'name': f"Webcam {device_name}",
                            'model': 'Generic Webcam',
                            'status': 'working' if device_working else 'error'
                        })
                except Exception as e:
                    self.logger.debug(f"Fehler beim Testen von {device}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Fehler bei der Geräte-Erkennung: {str(e)}")
        
        # Zusätzlich gphoto2-Kameras über den normalen Weg erkennen
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
                                    
                                    # Prüfen, ob diese Kamera bereits in der Liste ist (falls sie auch als /dev/video erscheint)
                                    already_added = False
                                    for existing_cam in cameras['gphoto2']:
                                        if model in existing_cam['name']:
                                            already_added = True
                                            break
                                    
                                    if not already_added:
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
                # cv2.VideoCapture mit Nummer (0, 1, ...) oder Pfad (/dev/video0, ...)
                if self.device.isdigit():
                    device_id = int(self.device)
                else:
                    device_id = self.device

                self.webcam = cv2.VideoCapture(device_id)

                # Auflösung einstellen
                self.webcam.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.webcam.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                
                # Kamera-Einstellungen für bessere Bildqualität
                self.webcam.set(cv2.CAP_PROP_AUTOFOCUS, 1)  # Autofokus aktivieren
                self.webcam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Auto-Belichtung aktivieren
                self.webcam.set(cv2.CAP_PROP_BRIGHTNESS, 100)  # Helligkeit erhöhen
                
                # Überprüfen, ob die Kamera geöffnet wurde
                if not self.webcam.isOpened():
                    self.logger.error(f"Webcam konnte nicht geöffnet werden: {self.device}")
                    self.webcam = None
                    return False
                
                # Einige Test-Frames lesen, um die Kamera zu initialisieren
                self.logger.info("Initialisiere Kamera mit Test-Frames...")
                for i in range(10):  # Mehr Frames als zuvor
                    ret, _ = self.webcam.read()
                    if not ret:
                        self.logger.warning(f"Test-Frame {i+1} konnte nicht gelesen werden")
                    time.sleep(0.3)  # Längere Pause für bessere Initialisierung

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

    def _setup_gphoto2(self):
        """
        Überprüft, ob gphoto2-Kamera bereit ist
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self.gphoto2_available:
            self.logger.error("gphoto2 ist nicht installiert. Es können keine DSLR-Kameras verwendet werden.")
            return False
            
        port_option = []
        
        # Wenn ein bestimmter Gerätepfad angegeben wurde
        if self.device and self.device.lower() != 'auto':
            # Anpassung für gphoto2-Pfadformat
            device_path = self.device
            
            # Wenn der Pfad bereits das usb-Format hat, aber Komma verwendet statt Punkt
            if device_path.startswith('usb:') and ',' in device_path:
                # Ersetze Komma durch Punkt für gphoto2
                device_path = device_path.replace(',', '.')
                self.logger.debug(f"DSLR-Pfad von {self.device} zu {device_path} formatiert")
            
            port_option = ['--port', device_path]
            self.logger.debug(f"Verwende DSLR-Gerätepfad: {device_path}")
        
        return port_option

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
            frames = []
            for i in range(15):  # Mehr Frames für bessere Anpassung
                ret, frame = self.webcam.read()
                if not ret:
                    self.logger.error(f"Fehler beim Lesen des Webcam-Frames {i+1}")
                    continue
                
                # Überprüfen, ob das Frame schwarz ist
                if frame is not None and frame.size > 0:
                    avg_brightness = cv2.mean(frame)[0]
                    if avg_brightness > 5:  # Ignoriere zu dunkle Frames
                        frames.append(frame)
                        self.logger.debug(f"Frame {i+1} erfasst, Helligkeit: {avg_brightness:.2f}")
                    else:
                        self.logger.warning(f"Frame {i+1} zu dunkel (Helligkeit: {avg_brightness:.2f})")
                
                # Längere Pause zwischen den Frames
                time.sleep(0.2)
            
            if not frames:
                self.logger.error("Keine brauchbaren Frames gefunden - alle Bilder zu dunkel oder fehlerhaft")
                return False
                
            # Das hellste Frame verwenden
            best_frame = max(frames, key=lambda f: cv2.mean(f)[0])
            self.logger.info(f"Verwende hellstes Frame (Helligkeit: {cv2.mean(best_frame)[0]:.2f})")
            
            # Verbessere Kontrast und Helligkeit wenn nötig
            if cv2.mean(best_frame)[0] < 50:
                self.logger.info("Verbessere Bild mit automatischer Kontrastanpassung")
                # Normalisiere Helligkeit und Kontrast
                lab = cv2.cvtColor(best_frame, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                cl = clahe.apply(l)
                limg = cv2.merge((cl, a, b))
                best_frame = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

            # Frame speichern
            success = cv2.imwrite(output_path, best_frame)

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
            port_option = self._setup_gphoto2()
            if port_option:
                cmd.extend(port_option)
            
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
