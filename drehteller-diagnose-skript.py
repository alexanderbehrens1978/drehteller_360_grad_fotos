#!/usr/bin/env python3
"""
Diagnose- und Reparaturskript für das 360° Drehteller-System
Dieses Skript prüft die Konfiguration und behebt typische Probleme.
"""

import os
import sys
import json
import shutil
import logging
import subprocess
from pathlib import Path

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("drehteller360_diagnose.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("drehteller360.diagnose")

class Drehteller360Diagnose:
    """Klasse zur Diagnose und Reparatur des Drehteller-Systems"""

    def __init__(self):
        """Initialisiert die Diagnose"""
        # Projektverzeichnis bestimmen (aktuelles Verzeichnis)
        self.project_dir = os.path.abspath(os.getcwd())
        logger.info(f"Projektverzeichnis: {self.project_dir}")
        
        # Wichtige Pfade
        self.config_path = os.path.join(self.project_dir, "config.json")
        self.static_dir = os.path.join(self.project_dir, "static")
        self.photos_dir = os.path.join(self.static_dir, "photos")
        self.sample_images_dir = os.path.join(self.static_dir, "sample_images")
        self.projects_dir = os.path.join(self.project_dir, "projects")
        self.templates_dir = os.path.join(self.project_dir, "templates")
        
        # Web.py-Datei finden
        self.web_py_path = os.path.join(self.project_dir, "web.py")
        self.backup_web_py_path = None
        for file in os.listdir(self.project_dir):
            if file.startswith("web.py-"):
                self.backup_web_py_path = os.path.join(self.project_dir, file)
                break
        
        # Konfiguration
        self.config = self._load_config()

    def run_diagnostics(self):
        """Führt alle Diagnoseprüfungen durch"""
        logger.info("Starte Diagnose des 360° Drehteller-Systems...")
        
        # Struktur prüfen
        self._check_directory_structure()
        
        # Konfiguration prüfen
        self._check_config()
        
        # Web.py-Datei prüfen
        self._check_web_py()
        
        # Module prüfen
        self._check_modules()
        
        # Geräte prüfen
        self._check_devices()
        
        logger.info("Diagnose abgeschlossen.")

    def fix_issues(self):
        """Behebt erkannte Probleme"""
        logger.info("Starte Reparatur des 360° Drehteller-Systems...")
        
        # Verzeichnisstruktur erstellen
        self._create_directory_structure()
        
        # Konfiguration reparieren/erstellen
        self._fix_config()
        
        # Web.py wiederherstellen, falls nötig
        self._fix_web_py()
        
        # Platzhalter-Bild erstellen
        self._create_placeholder_image()
        
        # Sample-Bilder generieren
        self._generate_sample_images()
        
        logger.info("Reparatur abgeschlossen.")

    def _load_config(self):
        """Lädt die Konfigurationsdatei"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"Konfigurationsdatei nicht gefunden: {self.config_path}")
                return {}
        except Exception as e:
            logger.error(f"Fehler beim Laden der Konfiguration: {str(e)}")
            return {}

    def _save_config(self, config):
        """Speichert die Konfigurationsdatei"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info(f"Konfiguration gespeichert: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Konfiguration: {str(e)}")
            return False

    def _check_directory_structure(self):
        """Prüft, ob die Verzeichnisstruktur korrekt ist"""
        dirs_to_check = [
            self.static_dir,
            self.photos_dir,
            self.sample_images_dir,
            self.projects_dir,
            self.templates_dir
        ]
        
        for directory in dirs_to_check:
            if os.path.exists(directory):
                logger.info(f"Verzeichnis vorhanden: {os.path.relpath(directory, self.project_dir)}")
            else:
                logger.warning(f"Verzeichnis fehlt: {os.path.relpath(directory, self.project_dir)}")

    def _create_directory_structure(self):
        """Erstellt die erforderliche Verzeichnisstruktur"""
        dirs_to_create = [
            self.static_dir,
            self.photos_dir,
            self.sample_images_dir,
            self.projects_dir,
            self.templates_dir
        ]
        
        for directory in dirs_to_create:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                logger.info(f"Verzeichnis erstellt: {os.path.relpath(directory, self.project_dir)}")

    def _check_config(self):
        """Prüft die Konfigurationsdatei"""
        if not self.config:
            logger.warning("Keine Konfiguration gefunden oder Konfiguration leer")
            return
        
        # Erforderliche Konfigurationsabschnitte prüfen
        required_sections = ["camera", "arduino", "rotation", "simulator"]
        for section in required_sections:
            if section not in self.config:
                logger.warning(f"Konfigurationsabschnitt fehlt: {section}")
            else:
                logger.info(f"Konfigurationsabschnitt vorhanden: {section}")
        
        # Prüfen, ob die Arduino-Konfiguration korrekt ist
        if "arduino" in self.config:
            arduino_config = self.config["arduino"]
            if "port" not in arduino_config or not arduino_config["port"]:
                logger.warning("Arduino-Port nicht konfiguriert")
            else:
                logger.info(f"Arduino-Port: {arduino_config['port']}")
            
            if "baudrate" not in arduino_config:
                logger.warning("Arduino-Baudrate nicht konfiguriert")
            else:
                logger.info(f"Arduino-Baudrate: {arduino_config['baudrate']}")
        
        # Prüfen, ob die Kamera-Konfiguration korrekt ist
        if "camera" in self.config:
            camera_config = self.config["camera"]
            if "device_path" not in camera_config or not camera_config["device_path"]:
                logger.warning("Kamera-Gerätepfad nicht konfiguriert")
            else:
                logger.info(f"Kamera-Gerätepfad: {camera_config['device_path']}")
            
            if "type" not in camera_config:
                logger.warning("Kamera-Typ nicht konfiguriert")
            else:
                logger.info(f"Kamera-Typ: {camera_config['type']}")

    def _fix_config(self):
        """Repariert oder erstellt die Konfigurationsdatei"""
        default_config = {
            "camera": {
                "device_path": "/dev/video0",
                "type": "webcam",
                "resolution": {
                    "width": 1280,
                    "height": 720
                }
            },
            "arduino": {
                "port": "/dev/ttyACM0",
                "baudrate": 9600
            },
            "rotation": {
                "default_degrees": 15,
                "default_interval": 5
            },
            "simulator": {
                "enabled": True
            }
        }
        
        # Wenn Konfiguration leer oder nicht vorhanden, verwende die Standardkonfiguration
        if not self.config:
            logger.info("Verwende Standardkonfiguration")
            self.config = default_config
            self._save_config(self.config)
            return
        
        # Fehlerhafte Konfiguration reparieren
        modified = False
        
        # Erforderliche Abschnitte hinzufügen, falls sie fehlen
        for section, default_section in default_config.items():
            if section not in self.config:
                logger.info(f"Füge fehlenden Konfigurationsabschnitt hinzu: {section}")
                self.config[section] = default_section
                modified = True
            else:
                # Fehlende Eigenschaften innerhalb der Abschnitte hinzufügen
                for key, value in default_section.items():
                    if key not in self.config[section]:
                        logger.info(f"Füge fehlende Konfigurationseigenschaft hinzu: {section}.{key}")
                        self.config[section][key] = value
                        modified = True
        
        # Konfiguration speichern, wenn sie geändert wurde
        if modified:
            self._save_config(self.config)

    def _check_web_py(self):
        """Prüft die web.py-Datei"""
        if not os.path.exists(self.web_py_path):
            logger.warning(f"web.py nicht gefunden: {self.web_py_path}")
            
            if self.backup_web_py_path:
                logger.info(f"Backup von web.py gefunden: {self.backup_web_py_path}")
            else:
                logger.warning("Kein Backup von web.py gefunden")
        else:
            logger.info(f"web.py gefunden: {self.web_py_path}")

    def _fix_web_py(self):
        """Repariert die web.py-Datei, falls nötig"""
        if not os.path.exists(self.web_py_path) and self.backup_web_py_path:
            logger.info(f"Stelle web.py aus Backup wieder her: {self.backup_web_py_path}")
            shutil.copy(self.backup_web_py_path, self.web_py_path)
            logger.info(f"web.py wiederhergestellt: {self.web_py_path}")

    def _check_modules(self):
        """Prüft, ob die erforderlichen Python-Module verfügbar sind"""
        modules_to_check = [
            "flask", 
            "werkzeug", 
            "cv2", 
            "numpy", 
            "PIL", 
            "serial", 
            "gphoto2"
        ]
        
        for module_name in modules_to_check:
            try:
                __import__(module_name)
                logger.info(f"Modul verfügbar: {module_name}")
            except ImportError:
                logger.warning(f"Modul nicht verfügbar: {module_name}")

    def _check_devices(self):
        """Prüft verfügbare Geräte (Arduino, Kameras)"""
        # Prüfe Arduino-Geräte
        self._check_arduino_devices()
        
        # Prüfe Kamera-Geräte
        self._check_camera_devices()

    def _check_arduino_devices(self):
        """Prüft verfügbare Arduino-Geräte"""
        try:
            import serial.tools.list_ports
            
            arduino_ports = []
            for port in serial.tools.list_ports.comports():
                if "Arduino" in port.description or "ACM" in port.device:
                    arduino_ports.append({
                        'port': port.device,
                        'description': port.description
                    })
            
            if arduino_ports:
                logger.info(f"Arduino-Geräte gefunden ({len(arduino_ports)}):")
                for device in arduino_ports:
                    logger.info(f"  - {device['port']} ({device['description']})")
            else:
                logger.warning("Keine Arduino-Geräte gefunden")
                
        except ImportError:
            logger.warning("Modul 'serial' nicht verfügbar, Arduino-Geräte können nicht geprüft werden")

    def _check_camera_devices(self):
        """Prüft verfügbare Kamera-Geräte"""
        # Prüfe Webcams
        self._check_webcams()
        
        # Prüfe gphoto2-Kameras
        self._check_gphoto2_cameras()

    def _check_webcams(self):
        """Prüft verfügbare Webcams"""
        try:
            import cv2
            
            webcams = []
            # Versuche die ersten 5 Webcam-Indizes
            for i in range(5):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    webcams.append(f"/dev/video{i}")
                    cap.release()
            
            if webcams:
                logger.info(f"Webcams gefunden ({len(webcams)}):")
                for webcam in webcams:
                    logger.info(f"  - {webcam}")
            else:
                logger.warning("Keine Webcams gefunden")
                
            # Zusätzliche Prüfung für Linux-Systeme
            if os.name == 'posix':
                video_devices = [f for f in os.listdir('/dev') if f.startswith('video')]
                if video_devices:
                    logger.info(f"Video-Geräte in /dev gefunden ({len(video_devices)}):")
                    for device in video_devices:
                        device_path = f"/dev/{device}"
                        logger.info(f"  - {device_path}")
                else:
                    logger.warning("Keine Video-Geräte in /dev gefunden")
            
        except ImportError:
            logger.warning("Modul 'cv2' nicht verfügbar, Webcams können nicht geprüft werden")

    def _check_gphoto2_cameras(self):
        """Prüft verfügbare gphoto2-Kameras"""
        try:
            result = subprocess.run(['which', 'gphoto2'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
            
            if result.returncode == 0:
                logger.info("gphoto2 ist installiert")
                
                # Kameras auflisten
                result = subprocess.run(['gphoto2', '--auto-detect'],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True)
                
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output:
                        logger.info("gphoto2 Ausgabe:")
                        for line in output.split('\n'):
                            logger.info(f"  {line}")
                    else:
                        logger.warning("Keine gphoto2-Kameras gefunden")
                else:
                    logger.warning(f"Fehler bei gphoto2 --auto-detect: {result.stderr}")
            else:
                logger.warning("gphoto2 ist nicht installiert")
                
        except Exception as e:
            logger.warning(f"Fehler beim Prüfen von gphoto2-Kameras: {str(e)}")

    def _create_placeholder_image(self):
        """Erstellt ein Platzhalter-Bild für den Viewer"""
        placeholder_path = os.path.join(self.static_dir, "placeholder.jpg")
        
        if os.path.exists(placeholder_path):
            logger.info(f"Platzhalter-Bild existiert bereits: {placeholder_path}")
            return
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Erstelle ein einfaches Platzhalter-Bild
            width, height = 640, 480
            image = Image.new("RGB", (width, height), color=(240, 240, 240))
            draw = ImageDraw.Draw(image)
            
            # Rahmen zeichnen
            draw.rectangle([0, 0, width-1, height-1], outline=(200, 200, 200), width=2)
            
            # Text hinzufügen
            try:
                font = ImageFont.load_default()
            except IOError:
                font = None
            
            text = "Kein Bild verfügbar"
            # In neueren Pillow-Versionen muss textlength oder textbbox verwendet werden
            try:
                if font:
                    if hasattr(draw, 'textlength'):
                        text_width = draw.textlength(text, font=font)
                    elif hasattr(draw, 'textbbox'):
                        bbox = draw.textbbox((0, 0), text, font=font)
                        text_width = bbox[2] - bbox[0]
                    else:
                        text_width = font.getlength(text) if hasattr(font, 'getlength') else 200
                else:
                    text_width = 200  # Ungefähre Breite
            except:
                text_width = 200  # Fallback-Wert
                
            text_position = ((width - text_width) // 2, height // 2 - 15)
            draw.text(text_position, text, fill=(100, 100, 100), font=font)
            
            # Bild speichern
            image.save(placeholder_path)
            logger.info(f"Platzhalter-Bild erstellt: {placeholder_path}")
            
        except ImportError:
            logger.warning("Modul 'PIL' nicht verfügbar, Platzhalter-Bild kann nicht erstellt werden")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Platzhalter-Bildes: {str(e)}")

    def _generate_sample_images(self):
        """Generiert Beispielbilder für den Simulator"""
        if os.path.exists(self.sample_images_dir) and len(os.listdir(self.sample_images_dir)) > 0:
            logger.info(f"Beispielbilder existieren bereits: {len(os.listdir(self.sample_images_dir))} Bilder gefunden")
            return
        
        try:
            from PIL import Image, ImageDraw, ImageFont
            import numpy as np
            
            # Erstelle 10 verschiedene Beispielbilder
            for i in range(10):
                filename = os.path.join(self.sample_images_dir, f"sample_image_{i}.jpg")
                
                # Erstelle ein Bild mit Farbverlauf
                width, height = 800, 600
                image = Image.new("RGB", (width, height))
                draw = ImageDraw.Draw(image)
                
                # Farbverlauf erzeugen
                for y in range(height):
                    r = int(255 * y / height)
                    g = int(255 * (1 - y / height))
                    b = int(128 + 127 * np.sin(y / 50 + i))
                    
                    for x in range(width):
                        draw.point((x, y), fill=(r, g, b))
                
                # Text hinzufügen
                try:
                    font = ImageFont.load_default()
                except IOError:
                    font = None
                
                text = f"Beispielbild {i+1}"
                # In neueren Pillow-Versionen muss textlength oder textbbox verwendet werden
                try:
                    if font:
                        if hasattr(draw, 'textlength'):
                            text_width = draw.textlength(text, font=font)
                        elif hasattr(draw, 'textbbox'):
                            bbox = draw.textbbox((0, 0), text, font=font)
                            text_width = bbox[2] - bbox[0]
                        else:
                            text_width = font.getlength(text) if hasattr(font, 'getlength') else 150
                    else:
                        text_width = 150  # Ungefähre Breite
                except:
                    text_width = 150  # Fallback-Wert
                    
                text_position = ((width - text_width) // 2, height // 2 - 15)
                draw.text(text_position, text, fill=(255, 255, 255), font=font)
                
                # Bild speichern
                image.save(filename)
                logger.info(f"Beispielbild erstellt: {filename}")
            
            logger.info(f"10 Beispielbilder wurden generiert in: {self.sample_images_dir}")
            
        except ImportError as e:
            logger.warning(f"Modul nicht verfügbar, Beispielbilder können nicht erstellt werden: {str(e)}")
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Beispielbilder: {str(e)}")

    def test_arduino_connection(self):
        """Testet die Verbindung zum Arduino"""
        if "arduino" not in self.config:
            logger.warning("Keine Arduino-Konfiguration gefunden")
            return False
        
        arduino_config = self.config["arduino"]
        if "port" not in arduino_config or not arduino_config["port"]:
            logger.warning("Arduino-Port nicht konfiguriert")
            return False
        
        try:
            import serial
            import time
            
            port = arduino_config["port"]
            baudrate = arduino_config.get("baudrate", 9600)
            
            logger.info(f"Verbindungsversuch zum Arduino: {port}, {baudrate} Baud")
            arduino = serial.Serial(port, baudrate, timeout=2)
            time.sleep(2)  # Warten auf Arduino-Reset
            
            # Testbefehl senden ('1' einschalten, kurz warten, '0' ausschalten)
            arduino.write(b'1')
            time.sleep(1)
            response = arduino.readline().decode('utf-8', errors='ignore').strip()
            logger.info(f"Arduino-Antwort: {response}")
            
            arduino.write(b'0')
            time.sleep(0.5)
            response = arduino.readline().decode('utf-8', errors='ignore').strip()
            logger.info(f"Arduino-Antwort: {response}")
            
            arduino.close()
            logger.info("Arduino-Verbindungstest erfolgreich")
            return True
            
        except ImportError:
            logger.warning("Modul 'serial' nicht verfügbar, Arduino-Verbindung kann nicht getestet werden")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Testen der Arduino-Verbindung: {str(e)}")
            return False

    def test_camera_capture(self):
        """Testet die Kameraaufnahme"""
        if "camera" not in self.config:
            logger.warning("Keine Kamera-Konfiguration gefunden")
            return False
        
        camera_config = self.config["camera"]
        camera_type = camera_config.get("type", "webcam")
        device_path = camera_config.get("device_path", "/dev/video0")
        
        if camera_type == "webcam":
            return self._test_webcam_capture(device_path)
        elif camera_type == "gphoto2":
            return self._test_gphoto2_capture(device_path)
        else:
            logger.warning(f"Unbekannter Kamera-Typ: {camera_type}")
            return False

    def _test_webcam_capture(self, device_path):
        """Testet die Aufnahme mit einer Webcam"""
        try:
            import cv2
            
            logger.info(f"Teste Webcam-Aufnahme mit Gerät: {device_path}")
            
            # Versuche, die Kamera zu öffnen
            if device_path.isdigit():
                cap = cv2.VideoCapture(int(device_path))
            else:
                cap = cv2.VideoCapture(device_path)
            
            if not cap.isOpened():
                logger.warning(f"Konnte Webcam nicht öffnen: {device_path}")
                return False
            
            # Bild aufnehmen
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                logger.warning("Konnte kein Bild von der Webcam aufnehmen")
                return False
            
            # Bild speichern
            test_image_path = os.path.join(self.photos_dir, "webcam_test.jpg")
            cv2.imwrite(test_image_path, frame)
            
            logger.info(f"Webcam-Testbild gespeichert: {test_image_path}")
            return True
            
        except ImportError:
            logger.warning("Modul 'cv2' nicht verfügbar, Webcam-Aufnahme kann nicht getestet werden")
            return False
        except Exception as e:
            logger.error(f"Fehler beim Testen der Webcam-Aufnahme: {str(e)}")
            return False

    def _test_gphoto2_capture(self, device_path):
        """Testet die Aufnahme mit einer gphoto2-Kamera"""
        try:
            test_image_path = os.path.join(self.photos_dir, "gphoto2_test.jpg")
            
            # Kommando zusammenbauen
            cmd = ['gphoto2', '--capture-image-and-download', '--filename', test_image_path]
            
            # Port hinzufügen, falls angegeben
            if device_path and device_path != "auto":
                cmd.extend(['--port', device_path])
            
            logger.info(f"Teste gphoto2-Aufnahme mit Befehl: {' '.join(cmd)}")
            
            # Befehl ausführen
            result = subprocess.run(cmd, 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    text=True, 
                                    timeout=30)
            
            if result.returncode == 0:
                logger.info(f"gphoto2-Testbild gespeichert: {test_image_path}")
                return True
            else:
                logger.warning(f"Fehler bei gphoto2-Aufnahme: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Testen der gphoto2-Aufnahme: {str(e)}")
            return False


if __name__ == "__main__":
    diagnosetool = Drehteller360Diagnose()
    
    print("=" * 60)
    print("360° Drehteller Diagnose- und Reparaturskript")
    print("=" * 60)
    print("\nDieses Skript prüft und repariert das 360° Drehteller-System.")
    print("Es werden die Verzeichnisstruktur, Konfiguration und Geräte überprüft.\n")
    
    print("1. Diagnose durchführen")
    print("2. Reparatur durchführen")
    print("3. Arduino-Verbindung testen")
    print("4. Kameraaufnahme testen")
    print("5. Beenden")
    
    choice = input("\nBitte wählen Sie eine Option (1-5): ")
    
    if choice == "1":
        diagnosetool.run_diagnostics()
    elif choice == "2":
        diagnosetool.fix_issues()
    elif choice == "3":
        diagnosetool.test_arduino_connection()
    elif choice == "4":
        diagnosetool.test_camera_capture()
    elif choice == "5":
        print("Programm wird beendet.")
    else:
        print("Ungültige Eingabe. Programm wird beendet.")
