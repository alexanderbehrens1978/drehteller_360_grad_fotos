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

@app.route('/projects')
def projects_page():
    """Zeigt die Projektverwaltungsseite an."""
    return render_template('projects.html')

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
        # Prüfen, ob JSON-Daten empfangen wurden
        if not request.is_json:
            return jsonify({
                "status": "error",
                "message": "Keine JSON-Daten empfangen. Content-Type muss application/json sein."
            }), 400

        # JSON-Daten abrufen
        new_config = request.json

        if not new_config:
            return jsonify({
                "status": "error",
                "message": "Leere Konfigurationsdaten empfangen"
            }), 400

        # Konfigurationsdaten ausgeben für Debugging
        print("Empfangene Konfiguration:", json.dumps(new_config, indent=2))

        # Versuchen, die Konfiguration zu speichern
        try:
            # Konfiguration mit bestehender Konfiguration zusammenführen
            # (Direkte Implementierung ohne die fehlende _merge_configs-Methode)
            merged_config = {}

            # Erst die bestehende Konfiguration kopieren
            for key, value in config_manager.config.items():
                merged_config[key] = value

            # Dann die neue Konfiguration einarbeiten (rekursiv)
            def recursive_update(target, source):
                for key, value in source.items():
                    if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                        recursive_update(target[key], value)
                    else:
                        target[key] = value

            recursive_update(merged_config, new_config)

            # Aktualisierte Konfiguration speichern
            config_manager.config = merged_config

            # In Datei speichern
            with open(config_manager.config_path, 'w') as f:
                json.dump(merged_config, f, indent=4)

            print(f"Konfiguration gespeichert in: {config_manager.config_path}")
            return jsonify({"status": "success"})
        except Exception as config_error:
            print(f"Fehler beim Speichern der Konfiguration: {config_error}")
            return jsonify({
                "status": "error",
                "message": f"Fehler beim Speichern: {str(config_error)}"
            }), 500

    except Exception as e:
        print(f"Allgemeiner Fehler beim Speichern der Konfiguration: {e}")
        return jsonify({
            "status": "error",
            "message": f"Allgemeiner Fehler: {str(e)}"
        }), 500

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

@app.route('/api/projects')
def get_projects():
    """Liefert eine Liste aller verfügbaren Projekte."""
    try:
        projects_dir = 'static/projects'
        projects = []

        # Verzeichnisse durchsuchen
        for project_id in os.listdir(projects_dir):
            project_path = os.path.join(projects_dir, project_id)

            # Nur Verzeichnisse berücksichtigen
            if os.path.isdir(project_path):
                metadata_path = os.path.join(project_path, 'metadata.json')

                # Prüfen, ob Metadaten existieren
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)

                    # Projekt-ID hinzufügen
                    metadata['id'] = project_id
                    projects.append(metadata)
                else:
                    # Fallback, wenn keine Metadaten existieren
                    images = [f for f in os.listdir(project_path)
                             if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                    projects.append({
                        'id': project_id,
                        'name': f"Projekt {project_id}",
                        'created': os.path.getctime(project_path),
                        'images': images,
                        'image_count': len(images)
                    })

        return jsonify(projects)
    except Exception as e:
        print(f"Fehler beim Laden der Projekte: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/project/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Löscht ein Projekt und alle zugehörigen Bilder."""
    try:
        # Pfad zum Projektverzeichnis
        project_dir = os.path.join('static/projects', project_id)
        
        if not os.path.exists(project_dir):
            return jsonify({"error": "Projekt nicht gefunden"}), 404
        
        # Metadaten lesen, um Bildinformationen zu erhalten
        metadata_path = os.path.join(project_dir, 'metadata.json')
        images_to_delete = []
        
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Unterverzeichnisse wie sessions/sessions_id/images prüfen
                if 'sessions' in metadata:
                    for session in metadata.get('sessions', []):
                        session_photos = session.get('photos', {})
                        for photo_path in session_photos.values():
                            if os.path.exists(photo_path) and os.path.isfile(photo_path):
                                images_to_delete.append(photo_path)
            except Exception as metadata_error:
                print(f"Warnung: Konnte Metadaten nicht lesen: {metadata_error}")
        
        # Verzeichnisstruktur des Projekts durchsuchen
        for root, dirs, files in os.walk(project_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    file_path = os.path.join(root, file)
                    images_to_delete.append(file_path)
        
        # Zuerst die einzelnen Bilddateien löschen
        for image_path in images_to_delete:
            try:
                if os.path.exists(image_path) and os.path.isfile(image_path):
                    os.remove(image_path)
                    print(f"Gelöschtes Bild: {image_path}")
            except Exception as image_error:
                print(f"Warnung: Konnte Bild nicht löschen: {image_error}")
        
        # Dann das gesamte Projektverzeichnis löschen
        import shutil
        shutil.rmtree(project_dir)
        print(f"Projekt {project_id} und alle zugehörigen Dateien wurden gelöscht.")
        
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Fehler beim Löschen des Projekts: {e}")
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
    os.makedirs('static/projects', exist_ok=True)

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
