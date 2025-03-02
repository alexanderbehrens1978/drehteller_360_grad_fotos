from flask import Flask, render_template, request, send_from_directory, jsonify, redirect
import os
import json
import time
import serial
import subprocess
from datetime import datetime

# Import config manager
from config_manager import config_manager

# Import the webcam capture simulator
from webcam_simulator import WebcamCaptureSimulator
from sample_images_generator import SampleImagesGenerator
from webcam_detection_helper import find_working_webcam, get_camera_capabilities, test_webcam_capture

# Import project manager
from project_manager import ProjectManager

# Initialize Flask app
app = Flask(__name__)

# Initialize webcam capture simulator
webcam_simulator = WebcamCaptureSimulator()

# Initialize sample images generator (optional, run once to generate images)
if not os.path.exists('static/sample_images') or len(os.listdir('static/sample_images')) < 5:
    image_generator = SampleImagesGenerator()
    image_generator.generate_sample_images(10)

# Initialize project manager
project_manager = ProjectManager()

# Configuration retrieval
USE_SIMULATOR = config_manager.get('simulator.enabled', True)


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


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


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
        config_manager.save_config(new_config)
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error saving configuration: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


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


# Projekt-Routen
@app.route('/projects')
def projects():
    projects_list = project_manager.get_projects()
    return render_template('projects.html', projects=projects_list)


@app.route('/projects/create', methods=['POST'])
def create_project():
    name = request.form.get('name', 'Neues Projekt')
    description = request.form.get('description', '')

    project_path = project_manager.create_project(name, description)
    project_dir = os.path.basename(project_path)

    return redirect(f'/projects/edit/{project_dir}')


@app.route('/projects/edit/<project_dir>')
def edit_project(project_dir):
    project = project_manager.get_project(project_dir)
    if not project:
        return redirect('/projects')

    return render_template('project_edit.html', project=project)


@app.route('/viewer/<project_dir>')
def viewer(project_dir):
    project = project_manager.get_project(project_dir)
    if not project:
        return redirect('/projects')

    # Erzeuge URLs für alle Bilder im Projekt
    image_urls = []
    for image in project.get('images', []):
        image_urls.append(f'/projects/image/{project_dir}/{image}')

    return render_template('viewer.html',
                           project_name=project['name'],
                           created_date=project.get('created', '').split('T')[0],
                           image_count=project.get('image_count', 0),
                           image_urls=image_urls)


@app.route('/projects/image/<project_dir>/<filename>')
def project_image(project_dir, filename):
    project_path = os.path.join(project_manager.base_path, project_dir, 'images')
    return send_from_directory(project_path, filename)


@app.route('/add_rotation_to_project', methods=['POST'])
def add_rotation_to_project():
    project_dir = request.form.get('project_dir')
    degrees = int(request.form.get('degrees', 15))
    interval = float(request.form.get('interval', 5))

    # Führe Rotation durch
    rotate_teller(degrees)

    # Erfasse Foto
    filename = f'photo_{int(time.time())}_{degrees}.jpg'
    photo_path = take_photo(filename)

    if photo_path:
        # Füge das Bild zum Projekt hinzu
        full_photo_path = os.path.join('static/photos', os.path.basename(photo_path))
        project_manager.add_image_to_project(project_dir, full_photo_path)

        return jsonify({
            "status": "success",
            "message": f"Rotation und Foto erfolgreich hinzugefügt",
            "photo_path": f'/static/photos/{os.path.basename(photo_path)}'
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Fehler beim Aufnehmen des Fotos"
        }), 500


@app.route('/projects/delete/<project_dir>', methods=['POST'])
def delete_project(project_dir):
    success = project_manager.delete_project(project_dir)
    if success:
        return jsonify({"status": "success"})
    else:
        return jsonify({"status": "error", "message": "Projekt konnte nicht gelöscht werden"}), 500


@app.route('/projects/update_description', methods=['POST'])
def update_project_description():
    try:
        data = request.json
        project_dir = data.get('project_dir')
        description = data.get('description', '')

        project_path = os.path.join(project_manager.base_path, project_dir)
        metadata_path = os.path.join(project_path, 'metadata.json')

        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            metadata['description'] = description
            metadata['last_modified'] = datetime.now().isoformat()

            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)

            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Projektmetadaten nicht gefunden"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    # Ensure static directories exist
    os.makedirs('static/photos', exist_ok=True)
    os.makedirs('static/sample_images', exist_ok=True)

    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)