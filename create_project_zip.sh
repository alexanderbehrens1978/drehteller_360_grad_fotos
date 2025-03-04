#!/bin/bash
# Skript zum Erstellen einer ZIP-Datei des drehteller-360 Projekts

# Farbige Ausgabe
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Drehteller 360° ZIP-Erstellungstool${NC}"
echo "======================================"

# Prüfen, ob zip installiert ist
if ! command -v zip &> /dev/null; then
    echo -e "${RED}Das 'zip'-Programm ist nicht installiert. Bitte installiere es zuerst.${NC}"
    echo "Auf Ubuntu/Debian: sudo apt-get install zip"
    echo "Auf Fedora: sudo dnf install zip"
    echo "Auf macOS: sollte bereits installiert sein"
    exit 1
fi

# Erstellen der Projektstruktur
echo -e "${YELLOW}Erstelle temporäre Projektstruktur...${NC}"

# Temporäres Verzeichnis
TEMP_DIR="drehteller-360-temp"
ZIP_NAME="drehteller-360-projekt.zip"

# Bereinigen des temporären Verzeichnisses, falls es existiert
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# Erstellen der Verzeichnisstruktur
mkdir -p "$TEMP_DIR/templates"
mkdir -p "$TEMP_DIR/static/css"
mkdir -p "$TEMP_DIR/static/js"
mkdir -p "$TEMP_DIR/static/photos"
mkdir -p "$TEMP_DIR/static/projects"
mkdir -p "$TEMP_DIR/static/sample_images"

# Python-Hauptdateien
echo -e "${YELLOW}Erstelle Python-Hauptdateien...${NC}"

# main.py
cat > "$TEMP_DIR/main.py" << 'EOL'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hauptanwendungseinstiegspunkt für die 360° Drehteller-Steuerung.
Startet den Webserver und initialisiert alle benötigten Komponenten.
"""

import os
import sys
import logging
from threading import Thread

# Stelle sicher, dass wir im richtigen Verzeichnis sind
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Initialisiere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("drehteller360.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("drehteller360")

# Stelle sicher, dass die benötigten Verzeichnisse existieren
os.makedirs('static/photos', exist_ok=True)
os.makedirs('static/sample_images', exist_ok=True)
os.makedirs('static/projects', exist_ok=True)

# Importiere erst nach Verzeichnissetup
from web import app
from device_detector import DeviceDetector
from config_manager import config_manager

def check_dependencies():
    """Überprüft, ob alle erforderlichen Abhängigkeiten installiert sind."""
    try:
        import flask
        import cv2
        import serial
        import numpy
        logger.info("Alle erforderlichen Python-Pakete sind installiert.")
        return True
    except ImportError as e:
        logger.error(f"Fehlende Abhängigkeit: {e}")
        print(f"Fehler: {e}. Bitte führen Sie 'pip install -r requirements.txt' aus.")
        return False

if __name__ == "__main__":
    logger.info("Starte 360° Drehteller-Steuerung...")
    
    if not check_dependencies():
        sys.exit(1)
    
    # Initialisiere Gerätedetektor im Hintergrund
    device_detector = DeviceDetector()
    detection_thread = Thread(target=device_detector.start_detection, daemon=True)
    detection_thread.start()
    
    # Starte den Flask-Server
    host = config_manager.get('web.host', '0.0.0.0')
    port = config_manager.get('web.port', 5000)
    debug = config_manager.get('web.debug', True)
    
    logger.info(f"Webserver wird gestartet auf {host}:{port}")
    app.run(host=host, port=port, debug=debug)
EOL

# web.py
cat > "$TEMP_DIR/web.py" << 'EOL'
from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import json
import time
import serial
import subprocess

# Import config manager
from config_manager import config_manager

# Import the webcam capture simulator
from webcam_simulator import WebcamCaptureSimulator
from sample_images_generator import SampleImagesGenerator
from webcam_detection_helper import find_working_webcam, get_camera_capabilities, test_webcam_capture
from device_detector import device_detector
from viewer_generator import viewer_generator

app = Flask(__name__)

# Configuration retrieval
USE_SIMULATOR = config_manager.get('simulator.enabled', True)

# Initialize webcam capture simulator
webcam_simulator = WebcamCaptureSimulator()

# Initialize sample images generator (optional, run once to generate images)
if not os.path.exists('static/sample_images') or len(os.listdir('static/sample_images')) < 5:
    image_generator = SampleImagesGenerator()
    image_generator.generate_sample_images(10)

# Arduino connection
def get_arduino_connection():
    """
    Establish Arduino connection based on configuration
    """
    try:
        if USE_SIMULATOR:
            return None
        
        port = config_manager.get('arduino.port', '/dev/ttyACM0')
        baudrate = config_manager.get('arduino.baudrate', 9600)
        
        arduino = serial.Serial(port, baudrate, timeout=1)
        time.sleep(2)  # Wait for initialization
        return arduino
    except Exception as e:
        print(f"Arduino connection error: {e}")
        return None

# Global Arduino connection
arduino = get_arduino_connection()

def rotate_teller(degrees):
    """
    Rotate the platform
    
    :param degrees: Rotation angle
    """
    if USE_SIMULATOR:
        print(f"Simulated rotation: {degrees} degrees")
        return
    
    if arduino is None:
        print("Arduino not connected!")
        return
    
    # Berechnung der Drehzeit basierend auf der Gradzahl (0,8 Grad pro Sekunde)
    rotation_time = degrees / 0.8
    
    # Relais einschalten (Drehteller starten)
    arduino.write(b'1')  # '1' senden, um das Relais einzuschalten
    time.sleep(rotation_time)  # Warte für die berechnete Zeit
    arduino.write(b'0')  # '0' senden, um das Relais auszuschalten
    print(f"Drehteller um {degrees} Grad gedreht.")

def take_photo(filename=None):
    """
    Capture a photo
    
    :param filename: Optional custom filename
    :return: Path to the saved photo
    """
    if USE_SIMULATOR:
        # Use the webcam simulator to generate a photo
        # Ensure filename is just the basename
        if filename:
            filename = os.path.basename(filename)
        return webcam_simulator.capture_photo(filename)
    
    try:
        # Camera device path and resolution from configuration
        camera_device = config_manager.get('camera.device_path', '/dev/video0')
        camera_type = config_manager.get('camera.type', 'webcam')
        
        # Get camera resolution
        camera_width = config_manager.get('camera.resolution.width')
        camera_height = config_manager.get('camera.resolution.height')
        
        # Use actual webcam capture for real hardware
        if not filename:
            filename = f'photo_{int(time.time())}.jpg'
        
        # Ensure filename is just the basename
        filename = os.path.basename(filename)
        full_path = os.path.join('static/photos', filename)
        
        # Choose capture method based on camera type
        if camera_type == 'gphoto2':
            # Use gphoto2 for DSLR cameras
            subprocess.call(['gphoto2', '--capture-image-and-download', '--filename', full_path])
        else:
            # Default to OpenCV for webcams
            import cv2
            cap = cv2.VideoCapture(camera_device)
            
            # Set resolution if specified
            if camera_width and camera_height:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)
            
            ret, frame = cap.read()
            if ret:
                cv2.imwrite(full_path, frame)
                cap.release()
            else:
                # Fallback to fswebcam if OpenCV fails
                subprocess.call(['fswebcam', '--no-banner', 
                                 '-d', camera_device, 
                                 full_path])
        
        print(f"Foto aufgenommen und als {filename} gespeichert.")
        return filename
    except Exception as e:
        print(f"Fehler beim Aufnehmen des Fotos: {e}")
        return None

@app.route('/generate_sample_images', methods=['POST'])
def generate_sample_images():
    """
    Generate sample images for the simulator
    """
    try:
        # Ensure sample images directory exists
        os.makedirs('static/sample_images', exist_ok=True)
        
        # Generate sample images
        image_generator = SampleImagesGenerator()
        generated_images = image_generator.generate_sample_images(10)
        
        return jsonify({
            "status": "success", 
            "message": f"{len(generated_images)} sample images generated",
            "images": generated_images
        })
    except Exception as e:
        print(f"Error generating sample images: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/test_webcam_simulator', methods=['POST'])
def test_webcam_simulator():
    """
    Test the webcam simulator by capturing a sample image
    """
    try:
        # Ensure photos directory exists
        os.makedirs('static/photos', exist_ok=True)
        
        # Capture a test photo using the simulator
        photo_path = webcam_simulator.capture_photo('test_simulator.jpg')
        
        # Return the photo path relative to static folder
        return photo_path.replace('static/', '/static/')
    except Exception as e:
        print(f"Error testing webcam simulator: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

@app.route('/camera_capabilities', methods=['GET'])
def camera_capabilities():
    """
    Get camera device capabilities
    """
    try:
        # Get camera device from configuration
        camera_device = config_manager.get('camera.device_path', '/dev/video0')
        
        # Get camera capabilities
        capabilities = get_camera_capabilities(camera_device)
        
        return jsonify({
            "status": "success",
            "capabilities": capabilities
        })
    except Exception as e:
        print(f"Error getting camera capabilities: {e}")
        return jsonify({
            "status": "error", 
            "message": str(e)
        }), 500

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/viewer')
def view_360():
    """Zeigt den 360°-Viewer an."""
    return render_template('viewer.html')

@app.route('/get_config')
def get_config():
    """
    Retrieve current configuration
    """
    return jsonify(config_manager.config)

@app.route('/save_config', methods=['POST'])
def save_config():
    """
    Save new configuration
    """
    try:
        new_config = request.json
        if not new_config:
            return jsonify({"status": "error", "message": "Keine Konfigurationsdaten empfangen"}), 400
            
        # Konfiguration speichern
        success = config_manager.save_config(new_config)
        
        if success:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Fehler beim Speichern der Konfiguration"}), 500
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/project/<project_id>')
def get_project(project_id):
    """Liefert Projektdaten für den 360°-Viewer."""
    try:
        project_dir = os.path.join('static/projects', project_id)
        metadata_path = os.path.join(project_dir, 'metadata.json')
        
        if not os.path.exists(metadata_path):
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return jsonify(metadata)
    except Exception as e:
        print(f"Fehler beim Laden der Projektdaten: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices')
def get_devices():
    """Liefert eine Liste aller erkannten Geräte."""
    return jsonify(device_detector.get_devices())

@app.route('/generate_360', methods=['POST'])
def generate_360():
    """Generiert einen 360°-Viewer aus den aufgenommenen Bildern."""
    try:
        # Liste der Fotos nach Zeitstempel sortieren
        photo_dir = 'static/photos'
        photos = sorted([f for f in os.listdir(photo_dir) 
                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        
        if not photos:
            return jsonify({"error": "Keine Fotos gefunden"}), 400
        
        # Optionale Metadaten aus der Anfrage
        metadata = request.get_json() if request.is_json else {}
        
        # 360°-Viewer generieren
        viewer_url = viewer_generator.generate_viewer(photos, metadata)
        
        if viewer_url:
            return jsonify({"status": "success", "url": viewer_url})
        else:
            return jsonify({"error": "Fehler beim Generieren des Viewers"}), 500
    except Exception as e:
        print(f"Fehler beim Generieren des 360°-Viewers: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/rotate', methods=['POST'])
def rotate():
    degrees = int(request.form['degrees'])
    interval = float(request.form.get('interval', 5))  # Default 5 seconds if not specified
    
    # Rotate platform
    rotate_teller(degrees)
    
    # Capture photo with timestamp to prevent caching
    filename = f'photo_{int(time.time())}_{degrees}.jpg'
    photo_path = take_photo(filename)
    
    # Return photo name relative to static folder
    if photo_path:
        return f'/static/photos/{os.path.basename(photo_path)}'
    else:
        return 'Error capturing photo', 500

@app.route('/static/photos/<filename>')
def serve_photo(filename):
    return send_from_directory('static/photos', filename)

if __name__ == '__main__':
    # Ensure static directories exist
    os.makedirs('static/photos', exist_ok=True)
    os.makedirs('static/sample_images', exist_ok=True)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
EOL

# device_detector.py
cat > "$TEMP_DIR/device_detector.py" << 'EOL'
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
EOL

# viewer_generator.py
cat > "$TEMP_DIR/viewer_generator.py" << 'EOL'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modul zur Generierung des 360°-Viewers aus einer Serie von Bildern.
Bereitet Bilder auf und erstellt HTML/JavaScript für den interaktiven Viewer.
"""

import os
import json
import shutil
import logging
import time
from datetime import datetime
from PIL import Image

# Logger konfigurieren
logger = logging.getLogger("drehteller360.viewer_generator")

class ViewerGenerator:
    """Generiert einen interaktiven 360°-Viewer aus einer Serie von Bildern."""
    
    def __init__(self, photo_dir='static/photos', output_dir='static/projects'):
        """
        Initialisiert den Viewer-Generator.
        
        Args:
            photo_dir: Verzeichnis mit den Quellfotos
            output_dir: Ausgabeverzeichnis für generierte Projekte
        """
        self.photo_dir = photo_dir
        self.output_dir = output_dir
        
        # Stelle sicher, dass das Ausgabeverzeichnis existiert
        os.makedirs(output_dir, exist_ok=True)
    
    def prepare_images(self, images, project_name):
        """
        Bereitet Bilder für den 360°-Viewer vor (Größenanpassung, Optimierung).
        
        Args:
            images: Liste der Bildpfade
            project_name: Name des Projekts
            
        Returns:
            Pfad zum Projektverzeichnis
        """
        project_dir = os.path.join(self.output_dir, project_name)
        os.makedirs(project_dir, exist_ok=True)
        
        processed_images = []
        
        for i, img_path in enumerate(images):
            try:
                # Lade Bild
                img = Image.open(os.path.join(self.photo_dir, img_path))
                
                # Passe Größe an (max. 1200px Breite für optimale Performance)
                max_width = 1200
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.LANCZOS)
                
                # Speichere optimiertes Bild
                img_filename = f"image_{i:03d}.jpg"
                output_path = os.path.join(project_dir, img_filename)
                img.save(output_path, "JPEG", quality=85, optimize=True)
                
                processed_images.append(img_filename)
            except Exception as e:
                logger.error(f"Fehler bei der Bildverarbeitung für {img_path}: {e}")
        
        return project_dir, processed_images
    
    def generate_viewer(self, images, metadata=None):
        """
        Generiert einen 360°-Viewer aus den gegebenen Bildern.
        
        Args:
            images: Liste der Bildpfade
            metadata: Zusätzliche Metadaten für das Projekt
            
        Returns:
            URL zum erstellten Viewer
        """
        if not images:
            logger.error("Keine Bilder zum Generieren des Viewers gefunden")
            return None
            
        # Projektname erstellen (Zeitstempel)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"project_{timestamp}"
        
        # Bilder vorbereiten
        project_dir, processed_images = self.prepare_images(images, project_name)
        
        # Erstelle Projektmetadaten
        project_metadata = {
            "name": project_name,
            "created": time.time(),
            "image_count": len(processed_images),
            "images": processed_images,
            "user_metadata": metadata or {}
        }
        
        # Speichere Metadaten
        metadata_path = os.path.join(project_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(project_metadata, f)
            
        return f"/viewer?project={project_name}"

# Globale Instanz für die Anwendung
viewer_generator = ViewerGenerator()
EOL

# config_manager.py
cat > "$TEMP_DIR/config_manager.py" << 'EOL'
import os
import json
import logging

# Logger konfigurieren
logger = logging.getLogger("drehteller360.config_manager")

class ConfigManager:
    DEFAULT_CONFIG = {
        'camera': {
            'device_path': '/dev/video0',
            'type': 'webcam',  # or 'gphoto2'
            'resolution': {
                'width': 1280,
                'height': 720
            }
        },
        'arduino': {
            'port': '/dev/ttyACM0',
            'baudrate': 9600
        },
        'rotation': {
            'default_degrees': 15,
            'default_interval': 5
        },
        'simulator': {
            'enabled': True
        },
        'web': {
            'host': '0.0.0.0',
            'port': 5000,
            'debug': True
        }
    }

    def __init__(self, config_path=None):
        """
        Initialize configuration manager
        
        :param config_path: Path to the configuration file
        """
        # Determine the project directory
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        
        # If no config path provided, use a default in the project directory
        if config_path is None:
            config_path = os.path.join(self.project_dir, 'config.json')
        
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self):
        """
        Load configuration from file or create default
        
        :return: Configuration dictionary
        """
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Try to load existing config
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    
                    # Rekursives Zusammenführen von Konfigurationen
                    return self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
            else:
                # Create default config file
                config = self.DEFAULT_CONFIG.copy()
                self.save_config(config)
                return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # If loading fails, use default config and try to save it
            try:
                self.save_config(self.DEFAULT_CONFIG)
            except Exception as save_error:
                logger.error(f"Error saving default config: {save_error}")
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default_config, user_config):
        """
        Rekursives Zusammenführen von Konfigurationen
        
        :param default_config: Default-Konfiguration
        :param user_config: Benutzerkonfiguration
        :return: Zusammengeführte Konfiguration
        """
        result = default_config.copy()
        
        for key, value in user_config.items():
            # Wenn der Wert ein Dictionary ist und im Default-Config existiert
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                # Rekursiv zusammenführen
                result[key] = self._merge_configs(result[key], value)
            else:
                # Sonst den Wert überschreiben
                result[key] = value
                
        return result
    
    def save_config(self, new_config=None):
        """
        Save configuration to file
        
        :param new_config: Optional new configuration to save
        """
        try:
            # Use provided config or current config
            if new_config is not None:
                # Merge with current config to ensure all keys exist
                config_to_save = self._merge_configs(self.config, new_config)
            else:
                config_to_save = self.config
            
            # Ensure full path exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save configuration
            with open(self.config_path, 'w') as f:
                json.dump(config_to_save, f, indent=4)
            
            # Update current config
            self.config = config_to_save
            logger.info(f"Konfiguration erfolgreich gespeichert in {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """
        Get a configuration value
        
        :param key: Dot-separated key (e.g. 'camera.device_path')
        :param default: Default value if key not found
        :return: Configuration value
        """
        try:
            # Split the key into parts
            parts = key.split('.')
            
            # Navigate through nested dictionary
            value = self.config
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    return default
            
            return value
        except Exception as e:
            logger.error(f"Error getting config value: {e}")
            return default

# Create a global config manager
config_manager = ConfigManager()

# Standalone usage example
if __name__ == '__main__':
    # Example usage
    print("Camera Device Path:", config_manager.get('camera.device_path'))
    print("Arduino Port:", config_manager.get('arduino.port'))
    
    # Example of updating config
    test_config = {
        'camera': {
            'device_path': '/dev/video1',
            'type': 'gphoto2'
        }
    }
    config_manager.save_config(test_config)
    
    # Verify changes
    print("\nAfter Update:")
    print("Camera Device Path:", config_manager.get('camera.device_path'))
    print("Arduino Port:", config_manager.get('arduino.port'))
EOL

# webcam_detection_helper.py
cat > "$TEMP_DIR/webcam_detection_helper.py" << 'EOL'
import cv2
import os
import time
import subprocess
import warnings

def find_working_webcam(preferred_devices=None):
    """
    Find a working webcam device
    
    :param preferred_devices: List of device paths to try first
    :return: Working device path or None
    """
    # Prioritize video0 for Microsoft LifeCam HD-5000
    if preferred_devices is None:
        preferred_devices = ['/dev/video0', '/dev/video1']
    
    # First, try fswebcam to check device functionality
    for device in preferred_devices:
        try:
            # Use subprocess to run fswebcam test
            result = subprocess.run([
                'fswebcam', 
                '-d', device, 
                '--no-banner', 
                '--device-timeout', '2',  # Short timeout
                '/dev/null'  # Discard output
            ], capture_output=True, text=True, timeout=3)
            
            # If fswebcam succeeds, return this device
            if result.returncode == 0:
                return device
        except subprocess.TimeoutExpired:
            continue
        except Exception:
            continue
    
    # Fallback to OpenCV detection
    for device in preferred_devices:
        try:
            # Try OpenCV capture
            cap = cv2.VideoCapture(device)
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                cap.release()
                return device
            cap.release()
        except Exception:
            pass
    
    # Comprehensive search if all else fails
    try:
        # Use v4l2-ctl to list all video devices
        result = subprocess.run(['v4l2-ctl', '--list-devices'], 
                                capture_output=True, 
                                text=True)
        
        # Extract all /dev/video* devices
        devices = [
            line.strip() 
            for line in result.stdout.split('\n') 
            if line.startswith('/dev/video')
        ]
        
        # Try each discovered device
        for device in devices:
            try:
                # Try fswebcam first
                result = subprocess.run([
                    'fswebcam', 
                    '-d', device, 
                    '--no-banner', 
                    '--device-timeout', '2',
                    '/dev/null'
                ], capture_output=True, text=True, timeout=3)
                
                if result.returncode == 0:
                    return device
                
                # Fallback to OpenCV
                cap = cv2.VideoCapture(device)
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    cap.release()
                    return device
                cap.release()
            except Exception:
                continue
    except Exception:
        pass
    
    return None

def get_camera_capabilities(device_path):
    """
    Retrieve camera capabilities
    
    :param device_path: Path to the video device
    :return: Dictionary of camera capabilities
    """
    capabilities = {
        'supported_resolutions': [],
        'max_width': 0,
        'max_height': 0
    }
    
    try:
        # Use v4l2-ctl to get detailed device information
        result = subprocess.run([
            'v4l2-ctl', 
            '-d', device_path, 
            '--list-formats-ext'
        ], capture_output=True, text=True, timeout=3)
        
        # Parse output to extract resolutions
        resolutions = []
        for line in result.stdout.split('\n'):
            if 'Size' in line:
                try:
                    # Extract resolution like '640x480'
                    resolution = line.split(':')[-1].strip()
                    width, height = map(int, resolution.split('x'))
                    resolutions.append((width, height))
                    
                    # Track max resolution
                    capabilities['max_width'] = max(capabilities['max_width'], width)
                    capabilities['max_height'] = max(capabilities['max_height'], height)
                except Exception:
                    pass
        
        capabilities['supported_resolutions'] = sorted(set(resolutions))
    except Exception as e:
        print(f"Error getting camera capabilities: {e}")
    
    return capabilities

def test_webcam_capture(device_path, width=None, height=None):
    """
    Attempt to capture an image from the specified device with optional resolution
    
    :param device_path: Path to the video device
    :param width: Optional desired width
    :param height: Optional desired height
    :return: Tuple (success, captured_image_path)
    """
    try:
        # Ensure output directory exists
        os.makedirs('static/photos', exist_ok=True)
        
        # Generate unique filename
        filename = f'webcam_test_{int(time.time())}.jpg'
        full_path = os.path.join('static/photos', filename)
        
        # Prepare fswebcam command
        cmd = ['fswebcam', 
               '-d', device_path, 
               '--no-banner', 
               '--device-timeout', '2']
        
        # Add resolution if specified
        if width and height:
            cmd.extend(['-r', f'{width}x{height}'])
        
        cmd.append(full_path)
        
        # Try fswebcam first
        subprocess.run(cmd, check=True, timeout=5)
        
        # Verify file was created
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            return True, full_path
        
        # Fallback to OpenCV with resolution
        cap = cv2.VideoCapture(device_path)
        
        # Set resolution if specified
        if width and height:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(full_path, frame)
            cap.release()
            return True, full_path
        cap.release()
        
        return False, None
    
    except subprocess.TimeoutExpired:
        print(f"Timeout capturing from {device_path}")
        return False, None
    except Exception as e:
        print(f"Webcam capture error: {e}")
        return False, None

# Standalone usage example
if __name__ == '__main__':
    # Find a working webcam
    working_device = find_working_webcam()
    
    if working_device:
        print(f"Found working webcam at: {working_device}")
        
        # Get camera capabilities
        capabilities = get_camera_capabilities(working_device)
        print("\nCamera Capabilities:")
        print(f"Supported Resolutions: {capabilities['supported_resolutions']}")
        print(f"Max Resolution: {capabilities['max_width']}x{capabilities['max_height']}")
        
        # Try capturing at a specific resolution
        success, image_path = test_webcam_capture(working_device, 1280, 720)
        
        if success:
            print(f"\nTest image captured: {image_path}")
        else:
            print("\nFailed to capture test image")
    else:
        print("No working webcam found")
EOL

# webcam_simulator.py
cat > "$TEMP_DIR/webcam_simulator.py" << 'EOL'
import cv2
import os
import time
import random
import subprocess
import warnings
from datetime import datetime

from webcam_detection_helper import find_working_webcam, test_webcam_capture

class WebcamCaptureSimulator:
    def __init__(self, base_path='static/photos', sample_images_path='static/sample_images'):
        """
        Initialize webcam capture simulator
        
        :param base_path: Directory to save captured photos
        :param sample_images_path: Directory containing sample images to use
        """
        self.base_path = base_path
        self.sample_images_path = sample_images_path
        
        # Ensure base and sample image directories exist
        os.makedirs(base_path, exist_ok=True)
        os.makedirs(sample_images_path, exist_ok=True)
        
        # Find the best webcam device
        self.camera_device = self._find_best_camera_device()
    
    def _find_best_camera_device(self, preferred_devices=None):
        """
        Find the best camera device to use
        
        :param preferred_devices: Optional list of preferred device paths
        :return: Best working device path
        """
        # If specific devices are known, try those first
        if preferred_devices is None:
            preferred_devices = ['/dev/video0', '/dev/video1']
        
        # Find a working webcam
        return find_working_webcam(preferred_devices)
    
    def capture_photo(self, filename=None):
        """
        Capture a photo - either from a real webcam or simulate with a sample image
        
        :param filename: Optional custom filename
        :return: Path to the saved image
        """
        # Ensure the base path exists
        os.makedirs(self.base_path, exist_ok=True)
        
        # If no filename provided, generate a unique one
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'webcam_photo_{timestamp}.jpg'
        
        # Ensure filename is just the basename
        filename = os.path.basename(filename)
        
        # Full path for the new image
        full_path = os.path.join(self.base_path, filename)
        
        # Try to capture from the detected camera device
        if self.camera_device:
            try:
                success, captured_path = test_webcam_capture(self.camera_device)
                if success:
                    # Copy the captured image to the desired filename
                    import shutil
                    shutil.copy(captured_path, full_path)
                    return full_path
            except Exception as e:
                print(f"Camera capture error: {e}")
        
        # Fallback to sample image simulation
        sample_images = [
            f for f in os.listdir(self.sample_images_path) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ]
        
        if sample_images:
            # Randomly select a sample image
            selected_sample = random.choice(sample_images)
            sample_path = os.path.join(self.sample_images_path, selected_sample)
            
            # Copy the sample image to the photos directory
            import shutil
            shutil.copy(sample_path, full_path)
            return full_path
        
        # Last resort - create a blank image
        import numpy as np
        blank_image = np.zeros((480,640,3), dtype=np.uint8)
        cv2.putText(blank_image, "No Image Available", (50,250), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        cv2.imwrite(full_path, blank_image)
        return full_path
    
    def list_photos(self):
        """
        List all photos in the base path
        
        :return: List of photo filenames
        """
        return [f for f in os.listdir(self.base_path) 
                if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

# Standalone usage example
if __name__ == '__main__':
    # Initialize the webcam capture simulator
    webcam_simulator = WebcamCaptureSimulator()
    
    # Capture 5 photos
    for i in range(5):
        captured_image = webcam_simulator.capture_photo()
        print(f"Captured image: {captured_image}")
    
    # List captured images
    print("\nCaptured Images:")
    for photo in webcam_simulator.list_photos():
        print(photo)
EOL

# sample_images_generator.py
cat > "$TEMP_DIR/sample_images_generator.py" << 'EOL'
import os
import random
import math
from PIL import Image, ImageDraw, ImageFont

class SampleImagesGenerator:
    def __init__(self, output_path='static/sample_images', width=800, height=600):
        """
        Generate sample images for webcam simulator
        
        :param output_path: Directory to save generated images
        :param width: Image width
        :param height: Image height
        """
        self.output_path = output_path
        self.width = width
        self.height = height
        
        # Ensure output directory exists
        os.makedirs(output_path, exist_ok=True)
    
    def generate_color_gradient_image(self, index):
        """
        Generate an image with a color gradient
        
        :param index: Unique identifier for the image
        :return: Path to the generated image
        """
        # Create a new image with a gradient
        image = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(image)
        
        # Generate gradient colors
        for y in range(self.height):
            r = int(255 * y / self.height)
            g = int(255 * (1 - y / self.height))
            b = int(128 + 127 * math.sin(y / 50))
            
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        
        # Add text to identify the image
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except IOError:
            font = ImageFont.load_default()
        
        draw.text((50, 50), f"Sample Image {index}", font=font, fill=(255, 255, 255))
        
        # Save the image
        filename = os.path.join(self.output_path, f'sample_image_{index}.jpg')
        image.save(filename)
        return filename
    
    def generate_sample_images(self, count=10):
        """
        Generate multiple sample images
        
        :param count: Number of images to generate
        :return: List of generated image paths
        """
        generated_images = []
        for i in range(count):
            image_path = self.generate_color_gradient_image(i)
            generated_images.append(image_path)
        
        return generated_images

# Optionally, if you want to use this as a standalone script
if __name__ == '__main__':
    generator = SampleImagesGenerator()
    generated_images = generator.generate_sample_images()
    
    print("Generated Sample Images:")
    for img in generated_images:
        print(img)
EOL

# HTML-Templates
echo -e "${YELLOW}Erstelle HTML-Templates...${NC}"

# templates/index.html
cat > "$TEMP_DIR/templates/index.html" << 'EOL'
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>360° Drehteller Steuerung</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/index.css">
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h2 class="mb-0">360° Drehteller Steuerung</h2>
                <a href="/settings" class="btn btn-light btn-sm">
                    <i class="bi bi-gear"></i> Einstellungen
                </a>
            </div>
            <div class="card-body">
                <!-- Captured Image Display -->
                <div class="text-center mb-4">
                    <img id="captured-image" src="/static/placeholder.jpg" alt="Aktuelles Foto" class="img-fluid">
                </div>

                <!-- Rotation Settings -->
                <div id="rotation-settings" class="row g-3">
                    <div class="col-md-4">
                        <label for="rotation-interval" class="form-label">Foto-Intervall (Sekunden)</label>
                        <input type="number" class="form-control" id="rotation-interval" value="5" min="1" max="60">
                    </div>
                    <div class="col-md-4">
                        <label for="rotation-degrees" class="form-label">Drehwinkel pro Schritt</label>
                        <input type="number" class="form-control" id="rotation-degrees" value="15" min="1" max="90">
                    </div>
                    <div class="col-md-4 d-flex align-items-end gap-2">
                        <button id="start-360-rotation" class="btn btn-success btn-play flex-grow-1">
                            <i class="bi bi-play-fill"></i> Start 360°
                        </button>
                        <button id="stop-rotation" class="btn btn-danger btn-stop d-none">
                            <i class="bi bi-stop-fill"></i> Stop
                        </button>
                    </div>
                </div>

                <!-- Progress Display -->
                <div id="progress-container" class="mt-3" style="display: none;">
                    <div class="progress">
                        <div id="rotation-progress" class="progress-bar" role="progressbar" style="width: 0%"></div>
                    </div>
                    <div id="rotation-status" class="text-center mt-2"></div>
                </div>

                <!-- 360° Viewer generieren -->
                <div id="generate-360-container" class="mt-4">
                    <h3>360° Viewer generieren</h3>
                    <div class="row g-3">
                        <div class="col-md-8">
                            <input type="text" class="form-control" id="project-name" placeholder="Projektname (optional)">
                        </div>
                        <div class="col-md-4">
                            <button id="generate-360-btn" class="btn btn-primary w-100">
                                <i class="bi bi-camera-video"></i> 360° Viewer erstellen
                            </button>
                        </div>
                    </div>
                    <div id="generation-status" class="mt-2"></div>
                </div>

                <!-- Manual Rotation -->
                <div class="mt-4">
                    <h3>Manuelle Rotation</h3>
                    <form id="manual-rotation-form">
                        <div class="input-group">
                            <input type="number" class="form-control" id="manual-degrees" placeholder="Drehwinkel" min="0" max="360" required>
                            <button type="submit" class="btn btn-primary">
                                <i class="bi bi-arrow-clockwise"></i> Drehen
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS and dependencies -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/index.js"></script>
    <script>
        // 360° Viewer Generierung
        document.getElementById('generate-360-btn').addEventListener('click', async () => {
            const statusElement = document.getElementById('generation-status');
            statusElement.innerHTML = '<div class="alert alert-info">Generiere 360° Viewer...</div>';
            
            const projectName = document.getElementById('project-name').value;
            
            try {
                const response = await fetch('/generate_360', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: projectName || ('Projekt ' + new Date().toLocaleDateString())
                    })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    statusElement.innerHTML = `
                        <div class="alert alert-success">
                            360° Viewer erfolgreich erstellt! 
                            <a href="${result.url}" class="btn btn-sm btn-primary ms-2">Anzeigen</a>
                        </div>`;
                } else {
                    statusElement.innerHTML = `<div class="alert alert-danger">Fehler: ${result.error}</div>`;
                }
            } catch (error) {
                statusElement.innerHTML = `<div class="alert alert-danger">Fehler: ${error.message}</div>`;
            }
        });
    </script>
</body>
</html>
EOL

# templates/settings.html
cat > "$TEMP_DIR/templates/settings.html" << 'EOL'
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Drehteller Einstellungen</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/settings.css">
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h2 class="text-center mb-0">
                    <i class="bi bi-gear me-2"></i>Drehteller Einstellungen
                </h2>
            </div>
            <div class="card-body">
                <form id="settings-form">
                    <!-- Camera Settings -->
                    <div class="mb-3">
                        <h4>Kamera Einstellungen</h4>
                        <div class="row">
                            <div class="col-md-8">
                                <label for="camera-device-path" class="form-label">Geräte-Pfad</label>
                                <input type="text" class="form-control" id="camera-device-path" 
                                       placeholder="/dev/video0" required>
                                <div class="form-text">Pfad zum Kameragerät (z.B. /dev/video0)</div>
                            </div>
                            <div class="col-md-4">
                                <label for="camera-type" class="form-label">Kameratyp</label>
                                <select class="form-select" id="camera-type">
                                    <option value="webcam">Webcam</option>
                                    <option value="gphoto2">DSLR (gphoto2)</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Arduino Settings -->
                    <div class="mb-3">
                        <h4>Arduino Einstellungen</h4>
                        <div class="row">
                            <div class="col-md-8">
                                <label for="arduino-port" class="form-label">Serieller Port</label>
                                <input type="text" class="form-control" id="arduino-port" 
                                       placeholder="/dev/ttyACM0" required>
                                <div class="form-text">Pfad zum Arduino-Port (z.B. /dev/ttyACM0)</div>
                            </div>
                            <div class="col-md-4">
                                <label for="arduino-baudrate" class="form-label">Baudrate</label>
                                <select class="form-select" id="arduino-baudrate">
                                    <option value="9600">9600</option>
                                    <option value="115200">115200</option>
                                    <option value="57600">57600</option>
                                    <option value="38400">38400</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Rotation Settings -->
                    <div class="mb-3">
                        <h4>Rotations-Einstellungen</h4>
                        <div class="row">
                            <div class="col-md-6">
                                <label for="rotation-degrees" class="form-label">Standard Drehwinkel</label>
                                <input type="number" class="form-control" id="rotation-degrees" 
                                       min="1" max="90" value="15">
                                <div class="form-text">Standardwinkel pro Rotationsschritt</div>
                            </div>
                            <div class="col-md-6">
                                <label for="rotation-interval" class="form-label">Foto-Intervall</label>
                                <input type="number" class="form-control" id="rotation-interval" 
                                       min="1" max="60" value="5">
                                <div class="form-text">Sekunden zwischen Fotos</div>
                            </div>
                        </div>
                    </div>


                    <!-- Camera Resolution Settings -->
                    <div class="mb-3">
                        <h4>Kamera-Auflösung</h4>
                        <div class="row g-3">
                            <div class="col-md-4">
                                <label for="camera-width" class="form-label">Breite (Pixel)</label>
                                <input type="number" class="form-control" id="camera-width" 
                                       placeholder="z.B. 1280" min="160" max="3840">
                            </div>
                            <div class="col-md-4">
                                <label for="camera-height" class="form-label">Höhe (Pixel)</label>
                                <input type="number" class="form-control" id="camera-height" 
                                       placeholder="z.B. 720" min="120" max="2160">
                            </div>
                            <div class="col-md-4">
                                <label for="camera-resolution-preset" class="form-label">Voreinstellungen</label>
                                <select class="form-select" id="camera-resolution-preset">
                                    <option value="custom">Benutzerdefiniert</option>
                                    <option value="640x480">640x480 (VGA)</option>
                                    <option value="1280x720">1280x720 (HD)</option>
                                    <option value="1920x1080">1920x1080 (Full HD)</option>
                                    <option value="2560x1440">2560x1440 (QHD)</option>
                                    <option value="3840x2160">3840x2160 (4K)</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- Simulator Controls -->
                    <div class="mt-4">
                        <h4>Simulator Einstellungen</h4>
                        <div class="row g-3">
                            <div class="col-md-4">
                                <label class="form-label">Simulator-Modus</label>
                                <div>
                                    <div class="form-check form-check-inline">
                                        <input class="form-check-input" type="radio" name="simulator-mode" id="simulator-on" value="true">
                                        <label class="form-check-label" for="simulator-on">
                                            Ein
                                        </label>
                                    </div>
                                    <div class="form-check form-check-inline">
                                        <input class="form-check-input" type="radio" name="simulator-mode" id="simulator-off" value="false">
                                        <label class="form-check-label" for="simulator-off">
                                            Aus
                                        </label>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-8">
                                <label class="form-label">Simulator-Tools</label>
                                <div>
                                    <button type="button" id="generate-sample-images" class="btn btn-secondary me-2">
                                        <i class="bi bi-image me-2"></i>Beispielbilder generieren
                                    </button>
                                    <button type="button" id="test-webcam-simulator" class="btn btn-info">
                                        <i class="bi bi-camera me-2"></i>Webcam-Simulator testen
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="d-grid gap-2 d-md-flex justify-content-md-end mt-4">
                        <a href="/" class="btn btn-secondary">
                            <i class="bi bi-x-circle me-2"></i>Abbrechen
                        </a>
                        <button type="submit" class="btn btn-primary">
                            <i class="bi bi-save me-2"></i>Speichern
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS and dependencies -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/settings.js"></script>
</body>
</html>
EOL

# templates/viewer.html
cat > "$TEMP_DIR/templates/viewer.html" << 'EOL'
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>360° Viewer - Drehteller Steuerung</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/viewer.css">
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h2 class="mb-0">360° Produktansicht</h2>
                <div>
                    <a href="/" class="btn btn-light btn-sm me-2">
                        <i class="bi bi-house"></i> Zurück zur Steuerung
                    </a>
                    <button id="fullscreen-btn" class="btn btn-light btn-sm">
                        <i class="bi bi-fullscreen"></i>
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div id="viewer-container" class="position-relative">
                    <!-- Viewer wird hier per JavaScript eingefügt -->
                    <div id="spinner" class="position-absolute top-50 start-50 translate-middle">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Laden...</span>
                        </div>
                    </div>
                    <div id="product-viewer" class="viewer-360"></div>
                </div>
                
                <div class="mt-4 d-flex justify-content-between">
                    <div class="viewer-controls">
                        <button id="play-btn" class="btn btn-primary">
                            <i class="bi bi-play-fill"></i> Auto-Rotation
                        </button>
                        <button id="reset-btn" class="btn btn-secondary ms-2">
                            <i class="bi bi-arrow-counterclockwise"></i> Zurücksetzen
                        </button>
                    </div>
                    
                    <div class="zoom-controls">
                        <button id="zoom-in-btn" class="btn btn-outline-secondary">
                            <i class="bi bi-zoom-in"></i>
                        </button>
                        <button id="zoom-out-btn" class="btn btn-outline-secondary ms-2">
                            <i class="bi bi-zoom-out"></i>
                        </button>
                    </div>
                </div>
                
                <div class="mt-4">
                    <div class="project-info">
                        <h4 id="project-name">Projekt: <span></span></h4>
                        <p id="image-count">Bilder: <span></span></p>
                    </div>
                </div>
            </div>
            
            <div class="card-footer text-center">
                <p>Bewegen Sie die Maus oder wischen Sie auf dem Touchscreen, um das Objekt zu drehen.</p>
                <small class="text-muted">Erstellt mit Drehteller 360° Steuerung</small>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="/static/js/viewer.js"></script>
</body>
</html>
EOL

# CSS-Dateien
echo -e "${YELLOW}Erstelle CSS-Dateien...${NC}"

# static/css/index.css
cat > "$TEMP_DIR/static/css/index.css" << 'EOL'
body {
    background-color: #f4f4f4;
    padding-top: 50px;
}

.container {
    max-width: 800px;
}

.card {
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

#captured-image {
    max-width: 100%;
    max-height: 400px;
    object-fit: contain;
    margin-bottom: 20px;
}

.btn-play, .btn-stop {
    font-size: 2rem;
    padding: 10px 20px;
}

#progress-container {
    margin-top: 20px;
}

#rotation-settings {
    margin-top: 20px;
}

@media (max-width: 768px) {
    body {
        padding-top: 20px;
    }
    .container {
        padding: 0 15px;
    }
}
EOL

# static/css/settings.css
cat > "$TEMP_DIR/static/css/settings.css" << 'EOL'
body {
    background-color: #f4f4f4;
    padding-top: 50px;
}

.container {
    max-width: 600px;
}

.card {
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

@media (max-width: 768px) {
    body {
        padding-top: 20px;
    }
    .container {
        padding: 0 15px;
    }
}

/* Optional: Add some subtle styling to form elements */
.form-control, .form-select {
    transition: border-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.form-control:focus, .form-select:focus {
    border-color: #0d6efd;
    box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
}

/* Simulator mode radio buttons */
.form-check-input:checked {
    background-color: #0d6efd;
    border-color: #0d6efd;
}

/* Clickable device items */
.clickable-device {
    cursor: pointer;
    transition: color 0.2s;
}
.clickable-device:hover {
    color: #0056b3 !important;
    text-decoration: underline;
}
EOL

# static/css/viewer.css
cat > "$TEMP_DIR/static/css/viewer.css" << 'EOL'
body {
    background-color: #f4f4f4;
    padding-top: 20px;
    padding-bottom: 20px;
}

.container {
    max-width: 1200px;
}

.card {
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

#viewer-container {
    position: relative;
    width: 100%;
    height: 500px;
    background-color: #fff;
    overflow: hidden;
    touch-action: none; /* Verhindert Browser-Scrolling bei Touch-Gesten */
}

.viewer-360 {
    width: 100%;
    height: 100%;
    position: relative;
    cursor: grab;
}

.viewer-360:active {
    cursor: grabbing;
}

.viewer-360 img {
    position: absolute;
    max-width: 100%;
    max-height: 100%;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    object-fit: contain;
    display: none;
}

.viewer-360 img.active {
    display: block;
}

/* Zoom-Effekt */
.viewer-360.zoomed {
    overflow: hidden;
}

/* Fullscreen-Modus */
.fullscreen {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 9999;
    background-color: #fff;
    padding: 20px;
}

.fullscreen #viewer-container {
    height: calc(100vh - 150px);
}

/* Spinner */
#spinner {
    z-index: 10;
}

/* Responsive Anpassungen */
@media (max-width: 768px) {
    #viewer-container {
        height: 350px;
    }
    
    .container {
        padding: 0 10px;
    }
    
    .viewer-controls, .zoom-controls {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
    }
}

@media (max-width: 576px) {
    #viewer-container {
        height: 300px;
    }
    
    .card-header {
        flex-direction: column;
        gap: 10px;
    }
    
    .btn-sm {
        padding: 5px 8px;
        font-size: 0.8rem;
    }
}
EOL

# JavaScript-Dateien
echo -e "${YELLOW}Erstelle JavaScript-Dateien...${NC}"

# static/js/index.js
cat > "$TEMP_DIR/static/js/index.js" << 'EOL'
// DOM Elements
const startButton = document.getElementById('start-360-rotation');
const stopButton = document.getElementById('stop-rotation');
const rotationIntervalInput = document.getElementById('rotation-interval');
const rotationDegreesInput = document.getElementById('rotation-degrees');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('rotation-progress');
const rotationStatus = document.getElementById('rotation-status');
const capturedImage = document.getElementById('captured-image');
const manualRotationForm = document.getElementById('manual-rotation-form');

// Rotation state
let isRotating = false;
let rotationAborted = false;

// 360° Rotation Function
async function start360Rotation() {
    const interval = parseInt(rotationIntervalInput.value);
    const stepDegrees = parseInt(rotationDegreesInput.value);
    const totalRotations = Math.floor(360 / stepDegrees);

    // Disable start button, show stop button
    startButton.disabled = true;
    stopButton.classList.remove('d-none');
    progressContainer.style.display = 'block';
    rotationStatus.textContent = 'Rotation gestartet...';
    isRotating = true;
    rotationAborted = false;

    // Reset progress
    progressBar.style.width = '0%';
    progressBar.classList.add('progress-bar-animated');

    try {
        for (let i = 0; i < totalRotations; i++) {
            // Check if rotation was aborted
            if (rotationAborted) {
                break;
            }

            // Update progress
            const progress = ((i + 1) / totalRotations) * 100;
            progressBar.style.width = `${progress}%`;
            rotationStatus.textContent = `Foto ${i + 1} von ${totalRotations}`;

            // Send rotation and photo capture request
            const response = await fetch('/rotate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `degrees=${stepDegrees}&interval=${interval}`
            });

            // Check if request was successful
            if (!response.ok) {
                throw new Error('Rotation fehlgeschlagen');
            }

            // Update image source with the latest photo
            const result = await response.text();
            capturedImage.src = result; // Assuming the response contains the photo path

            // Wait for the specified interval
            await new Promise(resolve => setTimeout(resolve, interval * 1000));
        }

        // Rotation complete
        if (!rotationAborted) {
            rotationStatus.textContent = 'Rotation abgeschlossen!';
            progressBar.classList.remove('progress-bar-animated');
        } else {
            rotationStatus.textContent = 'Rotation abgebrochen!';
            progressBar.classList.add('bg-warning');
        }
    } catch (error) {
        // Handle errors
        rotationStatus.textContent = `Fehler: ${error.message}`;
        progressBar.classList.add('bg-danger');
    } finally {
        // Re-enable start button, hide stop button
        startButton.disabled = false;
        stopButton.classList.add('d-none');
        isRotating = false;
    }
}

// Stop Rotation Function
function stopRotation() {
    if (isRotating) {
        rotationAborted = true;
        rotationStatus.textContent = 'Rotation wird gestoppt...';
    }
}

// Manual Rotation
manualRotationForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const degrees = document.getElementById('manual-degrees').value;

    try {
        const response = await fetch('/rotate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `degrees=${degrees}`
        });

        const result = await response.text();
        capturedImage.src = result; // Update image with latest photo
    } catch (error) {
        console.error('Rotation error:', error);
    }
});

// Event Listeners
startButton.addEventListener('click', start360Rotation);
stopButton.addEventListener('click', stopRotation);
EOL

# static/js/settings.js
cat > "$TEMP_DIR/static/js/settings.js" << 'EOL'
// Camera Resolution Preset Handling
const cameraWidthInput = document.getElementById('camera-width');
const cameraHeightInput = document.getElementById('camera-height');
const cameraResolutionPreset = document.getElementById('camera-resolution-preset');
const simulatorOnBtn = document.getElementById('simulator-on');
const simulatorOffBtn = document.getElementById('simulator-off');

// Resolution preset change handler
cameraResolutionPreset.addEventListener('change', (e) => {
    const preset = e.target.value;
    
    switch(preset) {
        case '640x480':
            cameraWidthInput.value = 640;
            cameraHeightInput.value = 480;
            break;
        case '1280x720':
            cameraWidthInput.value = 1280;
            cameraHeightInput.value = 720;
            break;
        case '1920x1080':
            cameraWidthInput.value = 1920;
            cameraHeightInput.value = 1080;
            break;
        case '2560x1440':
            cameraWidthInput.value = 2560;
            cameraHeightInput.value = 1440;
            break;
        case '3840x2160':
            cameraWidthInput.value = 3840;
            cameraHeightInput.value = 2160;
            break;
        case 'custom':
            // Clear inputs or keep current values
            break;
    }
});

// Geräteliste laden
async function loadDevices() {
    try {
        const response = await fetch('/api/devices');
        const devices = await response.json();
        
        updateDeviceUI(devices);
    } catch (error) {
        console.error('Fehler beim Laden der Geräte:', error);
    }
}

// Geräte-UI aktualisieren
function updateDeviceUI(devices) {
    // Bestehende Listen entfernen (um Duplikate zu vermeiden)
    document.querySelectorAll('.device-list').forEach(el => el.remove());
    
    // Webcams anzeigen
    const webcamList = document.createElement('div');
    webcamList.className = 'mt-2 small device-list';
    
    if (devices.cameras.webcams.length > 0) {
        devices.cameras.webcams.forEach(webcam => {
            const option = document.createElement('div');
            option.className = 'form-text text-primary clickable-device';
            option.innerHTML = `<i class="bi bi-camera-video"></i> ${webcam}`;
            option.addEventListener('click', () => {
                document.getElementById('camera-device-path').value = webcam;
            });
            webcamList.appendChild(option);
        });
    } else {
        webcamList.innerHTML = '<div class="form-text text-muted">Keine Webcams gefunden</div>';
    }
    
    // Nach dem Kamera-Device-Pfad einfügen
    const cameraInput = document.getElementById('camera-device-path');
    cameraInput.parentNode.appendChild(webcamList);
    
    // gPhoto2-Kameras anzeigen
    const gphotoList = document.createElement('div');
    gphotoList.className = 'mt-2 small device-list';
    
    if (devices.cameras.gphoto2.length > 0) {
        devices.cameras.gphoto2.forEach(camera => {
            const option = document.createElement('div');
            option.className = 'form-text text-primary';
            option.innerHTML = `<i class="bi bi-camera"></i> ${camera}`;
            gphotoList.appendChild(option);
        });
    } else {
        gphotoList.innerHTML = '<div class="form-text text-muted">Keine gphoto2-Kameras gefunden</div>';
    }
    
    // Nach dem Kameratyp einfügen
    const cameraType = document.getElementById('camera-type');
    cameraType.parentNode.appendChild(gphotoList);
    
    // Arduino-Geräte anzeigen
    const arduinoList = document.createElement('div');
    arduinoList.className = 'mt-2 small device-list';
    
    if (devices.arduinos.length > 0) {
        devices.arduinos.forEach(arduino => {
            const option = document.createElement('div');
            option.className = 'form-text text-primary clickable-device';
            option.innerHTML = `<i class="bi bi-cpu"></i> ${arduino.port} - ${arduino.description}`;
            option.addEventListener('click', () => {
                document.getElementById('arduino-port').value = arduino.port;
            });
            arduinoList.appendChild(option);
        });
    } else {
        arduinoList.innerHTML = '<div class="form-text text-muted">Keine Arduino-Geräte gefunden</div>';
    }
    
    // Nach dem Arduino-Port einfügen
    const arduinoInput = document.getElementById('arduino-port');
    arduinoInput.parentNode.appendChild(arduinoList);
}

// Add existing code from previous settings.js here...
document.addEventListener('DOMContentLoaded', () => {
    // Geräteliste laden
    loadDevices();
    
    // Konfiguration vom Server laden
    fetch('/get_config')
        .then(response => response.json())
        .then(config => {
            console.log('Geladene Konfiguration:', config);
            
            // Kamera-Einstellungen
            if (config.camera) {
                document.getElementById('camera-device-path').value = config.camera.device_path || '';
                document.getElementById('camera-type').value = config.camera.type || 'webcam';
                
                // Kamera-Auflösung setzen
                const cameraWidth = config.camera.resolution?.width;
                const cameraHeight = config.camera.resolution?.height;
                
                if (cameraWidth && cameraHeight) {
                    cameraWidthInput.value = cameraWidth;
                    cameraHeightInput.value = cameraHeight;
                    
                    // Set preset dropdown
                    const presetValue = `${cameraWidth}x${cameraHeight}`;
                    const presetOption = Array.from(cameraResolutionPreset.options)
                        .find(option => option.value === presetValue);
                    
                    if (presetOption) {
                        cameraResolutionPreset.value = presetValue;
                    } else {
                        cameraResolutionPreset.value = 'custom';
                    }
                }
            }
            
            // Arduino-Einstellungen
            if (config.arduino) {
                document.getElementById('arduino-port').value = config.arduino.port || '';
                document.getElementById('arduino-baudrate').value = config.arduino.baudrate || 9600;
            }
            
            // Rotations-Einstellungen
            if (config.rotation) {
                document.getElementById('rotation-degrees').value = config.rotation.default_degrees || 15;
                document.getElementById('rotation-interval').value = config.rotation.default_interval || 5;
            }
            
            // Simulator-Einstellungen
            if (config.simulator !== undefined) {
                // Hier ist der Fehler - wir müssen den richtigen Radio-Button auswählen
                if (config.simulator.enabled) {
                    simulatorOnBtn.checked = true;
                } else {
                    simulatorOffBtn.checked = true;
                }
            }
        })
        .catch(error => {
            console.error('Fehler beim Laden der Konfiguration:', error);
        });
});

// Aktualisierungsknopf für Geräteliste
const deviceRefreshButton = document.createElement('button');
deviceRefreshButton.type = 'button';
deviceRefreshButton.className = 'btn btn-outline-secondary mt-3';
deviceRefreshButton.innerHTML = '<i class="bi bi-arrow-clockwise"></i> Geräte aktualisieren';
deviceRefreshButton.addEventListener('click', loadDevices);

// CSS für klickbare Geräte
const style = document.createElement('style');
style.textContent = `
    .clickable-device {
        cursor: pointer;
        transition: color 0.2s;
    }
    .clickable-device:hover {
        color: #0056b3 !important;
        text-decoration: underline;
    }
`;
document.head.appendChild(style);

// Knopf zum Formular hinzufügen (nach dem Laden der Seite)
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('settings-form').insertBefore(
        deviceRefreshButton,
        document.querySelector('.d-grid.gap-2.d-md-flex')
    );
});

// Formular-Abschicken
document.getElementById('settings-form').addEventListener('submit', (e) => {
    e.preventDefault();

    // Prepare configuration object
    const config = {
        camera: {
            device_path: document.getElementById('camera-device-path').value,
            type: document.getElementById('camera-type').value,
            resolution: {
                width: parseInt(cameraWidthInput.value || 0),
                height: parseInt(cameraHeightInput.value || 0)
            }
        },
        arduino: {
            port: document.getElementById('arduino-port').value,
            baudrate: parseInt(document.getElementById('arduino-baudrate').value)
        },
        rotation: {
            default_degrees: parseInt(document.getElementById('rotation-degrees').value),
            default_interval: parseInt(document.getElementById('rotation-interval').value)
        },
        simulator: {
            enabled: document.getElementById('simulator-on').checked
        }
    };

    console.log("Einstellungen zum Speichern:", config);

    // Send configuration to server
    fetch('/save_config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('Netzwerkfehler beim Speichern');
        }
    })
    .then(data => {
        if (data.status === 'success') {
            // Show success message
            alert('Einstellungen erfolgreich gespeichert!');
            // Redirect to main page
            window.location.href = '/';
        } else {
            alert('Fehler beim Speichern der Einstellungen: ' + (data.message || 'Unbekannter Fehler'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Fehler beim Speichern der Einstellungen: ' + error.message);
    });
});
EOL

# static/js/viewer.js
cat > "$TEMP_DIR/static/js/viewer.js" << 'EOL'
/**
 * 360° Produktansicht Viewer
 * Interaktiver Viewer für 360-Grad-Produktansichten
 */

// DOM-Elemente
const viewerContainer = document.getElementById('product-viewer');
const spinner = document.getElementById('spinner');
const playButton = document.getElementById('play-btn');
const resetButton = document.getElementById('reset-btn');
const zoomInButton = document.getElementById('zoom-in-btn');
const zoomOutButton = document.getElementById('zoom-out-btn');
const fullscreenButton = document.getElementById('fullscreen-btn');
const projectNameElement = document.querySelector('#project-name span');
const imageCountElement = document.querySelector('#image-count span');

// Viewer-Konfiguration
let config = {
    images: [],            // Bildpfade
    currentImageIndex: 0,  // Aktueller Bildindex
    autoRotate: false,     // Automatische Rotation
    autoRotateSpeed: 100,  // Rotationsgeschwindigkeit in ms
    zoom: 1.0,             // Zoomstufe
    maxZoom: 2.5,          // Maximale Zoomstufe
    minZoom: 1.0,          // Minimale Zoomstufe
    zoomStep: 0.1,         // Zoom-Schritt pro Klick
    dragging: false,       // Maus/Touch-Status
    lastX: 0,              // Letzte X-Position
    autoRotateTimer: null  // Timer für Auto-Rotation
};

// Projekt-ID aus URL-Parametern holen
const urlParams = new URLSearchParams(window.location.search);
const projectId = urlParams.get('project');

/**
 * Lädt die Projektdaten vom Server
 */
async function loadProject() {
    if (!projectId) {
        showError('Keine Projekt-ID angegeben');
        return;
    }
    
    try {
        const response = await fetch(`/api/project/${projectId}`);
        
        if (!response.ok) {
            throw new Error('Projekt konnte nicht geladen werden');
        }
        
        const projectData = await response.json();
        
        // Projektdaten anzeigen
        projectNameElement.textContent = projectData.name;
        imageCountElement.textContent = projectData.image_count;
        
        // Bilder laden
        config.images = projectData.images.map(img => `/static/projects/${projectId}/${img}`);
        
        if (config.images.length > 0) {
            initViewer();
        } else {
            showError('Keine Bilder im Projekt gefunden');
        }
    } catch (error) {
        console.error('Fehler beim Laden des Projekts:', error);
        showError('Fehler beim Laden des Projekts');
    }
}

/**
 * Initialisiert den 360° Viewer
 */
function initViewer() {
    // Bilder vorladen
    preloadImages().then(() => {
        // Spinner ausblenden
        spinner.style.display = 'none';
        
        // Erstes Bild anzeigen
        showImage(0);
        
        // Event-Listener hinzufügen
        setupEventListeners();
        
        // Automatische Rotation starten
        startAutoRotate();
    });
}

/**
 * Lädt alle Bilder vor
 */
async function preloadImages() {
    const preloadPromises = config.images.map(src => {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve();
            img.onerror = () => reject();
            img.src = src;
            img.className = 'product-image';
            img.style.display = 'none';
            img.draggable = false;
            viewerContainer.appendChild(img);
        });
    });
    
    return Promise.all(preloadPromises);
}

/**
 * Zeigt das Bild mit dem angegebenen Index an
 */
function showImage(index) {
    // Aktuelles Bild ausblenden
    const currentImage = viewerContainer.querySelector('.active');
    if (currentImage) {
        currentImage.classList.remove('active');
    }
    
    // Neues Bild anzeigen
    const newImage = viewerContainer.querySelectorAll('img')[index];
    if (newImage) {
        newImage.classList.add('active');
        config.currentImageIndex = index;
    }
}

/**
 * Richtet Event-Listener für Maus/Touch-Interaktionen ein
 */
function setupEventListeners() {
    // Maus-Events
    viewerContainer.addEventListener('mousedown', startDrag);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', endDrag);
    
    // Touch-Events
    viewerContainer.addEventListener('touchstart', startDrag);
    document.addEventListener('touchmove', drag);
    document.addEventListener('touchend', endDrag);
    
    // Zoom-Events
    zoomInButton.addEventListener('click', zoomIn);
    zoomOutButton.addEventListener('click', zoomOut);
    viewerContainer.addEventListener('wheel', handleWheel);
    
    // Steuerungs-Buttons
    playButton.addEventListener('click', toggleAutoRotate);
    resetButton.addEventListener('click', resetViewer);
    fullscreenButton.addEventListener('click
