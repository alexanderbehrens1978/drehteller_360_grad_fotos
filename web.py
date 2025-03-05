from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import json
import time
import subprocess

# Import config manager
from config_manager import config_manager

# Import the Arduino reconnection manager
from arduino_reconnect import ArduinoReconnectManager

# Import other modules
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

# Global Arduino connection manager instance
arduino_manager = None

def get_arduino_manager():
    """
    Get or create the Arduino connection manager
    """
    global arduino_manager
    
    # If simulator is enabled, return None
    if USE_SIMULATOR:
        return None
    
    # Create the connection manager if it doesn't exist
    if arduino_manager is None:
        port = config_manager.get('arduino.port', '/dev/ttyACM0')
        baudrate = config_manager.get('arduino.baudrate', 9600)
        arduino_manager = ArduinoReconnectManager(port, baudrate)
    
    return arduino_manager

def rotate_teller(degrees):
    """
    Rotate the platform
    
    :param degrees: Rotation angle
    """
    if USE_SIMULATOR:
        print(f"Simulated rotation: {degrees} degrees")
        return True
    
    # Get Arduino manager and ensure it's connected
    arduino = get_arduino_manager()
    if arduino is None:
        print("Arduino manager not available")
        return False
    
    if not arduino.ensure_connection():
        print("Arduino not connected and reconnection failed")
        return False
    
    # Calculate rotation time based on degrees (0.8° per second)
    rotation_time = degrees / 0.8
    rotation_time_ms = int(rotation_time * 1000)
    
    # Use the rotation duration method from the manager
    success = arduino.rotate_for_duration(rotation_time_ms)
    
    if success:
        print(f"Drehteller um {degrees} Grad gedreht.")
    else:
        print(f"Fehler beim Drehen des Tellers um {degrees} Grad")
    
    return success

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

@app.route('/test_arduino_connection', methods=['POST'])
def test_arduino_connection():
    """
    Test the Arduino connection
    """
    try:
        # Get Arduino connection info from request
        port = request.form.get('port', config_manager.get('arduino.port', '/dev/ttyACM0'))
        baudrate = int(request.form.get('baudrate', config_manager.get('arduino.baudrate', 9600)))
        
        # Create temporary manager to test the connection
        test_manager = ArduinoReconnectManager(port, baudrate)
        connected = test_manager.ensure_connection()
        
        # Run a short test if connected
        test_result = False
        if connected:
            test_result = test_manager.rotate_for_duration(1000)  # 1 second test
        
        # Disconnect the test manager
        test_manager.disconnect()
        
        # Return result
        return jsonify({
            "status": "success" if connected else "error",
            "connected": connected,
            "test_result": test_result,
            "message": "Arduino connected and tested successfully" if test_result else 
                      "Arduino connected but test failed" if connected else 
                      "Could not connect to Arduino"
        })
    except Exception as e:
        print(f"Error testing Arduino connection: {e}")
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
            # Get current Arduino configuration
            old_port = config_manager.get('arduino.port')
            old_baudrate = config_manager.get('arduino.baudrate')
            
            # Check if Arduino configuration has changed
            new_port = new_config.get('arduino', {}).get('port')
            new_baudrate = new_config.get('arduino', {}).get('baudrate')
            
            if (new_port and new_port != old_port) or (new_baudrate and new_baudrate != old_baudrate):
                # Reset the Arduino manager so it will reconnect with new settings
                global arduino_manager
                if arduino_manager:
                    arduino_manager.disconnect("Configuration changed")
                    arduino_manager = None
            
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
    
    # Rotate platform with improved error handling
    rotation_success = rotate_teller(degrees)
    
    if not rotation_success:
        return 'Error rotating platform', 500
    
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

@app.route('/arduino_status', methods=['GET'])
def arduino_status():
    """Check the current status of the Arduino connection"""
    
    if USE_SIMULATOR:
        return jsonify({
            "status": "simulator",
            "message": "Simulator is enabled, no Arduino connection needed"
        })
    
    arduino = get_arduino_manager()
    if arduino is None:
        return jsonify({
            "status": "error",
            "message": "Arduino manager is not available"
        })
    
    connected = arduino.ensure_connection()
    
    return jsonify({
        "status": "connected" if connected else "disconnected",
        "port": arduino.port,
        "baudrate": arduino.baudrate,
        "message": "Arduino is connected and ready" if connected else "Arduino is not connected"
    })

# When the flask application exits, clean up the Arduino connection
@app.teardown_appcontext
def teardown_arduino(exception):
    global arduino_manager
    if arduino_manager:
        arduino_manager.disconnect("Application shutdown")

if __name__ == '__main__':
    # Ensure static directories exist
    os.makedirs('static/photos', exist_ok=True)
    os.makedirs('static/sample_images', exist_ok=True)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
