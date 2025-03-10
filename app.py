# !/usr/bin/env python3
# Datei: app.py
# Hauptanwendungsmodul für die 360° Drehteller Anwendung

import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from config.settings import Settings
from controllers.arduino_controller import ArduinoController
from controllers.camera_controller import CameraController
from controllers.turntable_controller import TurntableController
from models.project import Project, ProjectManager
from utils.arduino_finder import ArduinoFinder
from utils.camera_finder import CameraFinder
from utils.path_manager import PathManager
from utils.image_processor import ImageProcessor
from utils.background_remover import BackgroundRemover

# Logger konfigurieren
logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Flask-App initialisieren
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Pfadmanager initialisieren
path_manager = PathManager()
path_manager.ensure_directories()

# Einstellungen laden
settings = Settings()

# Controller initialisieren
arduino_finder = ArduinoFinder()
camera_finder = CameraFinder()
arduino_controller = None
camera_controller = None
turntable_controller = None

# Projektverwaltung initialisieren
project_manager = ProjectManager(path_manager.projects_dir)

# Bildverarbeitung initialisieren
image_processor = ImageProcessor(path_manager)
background_remover = BackgroundRemover()


@app.route('/')
def index():
    """Hauptseite der Anwendung"""
    projects = project_manager.get_all_projects()
    return render_template('index.html', projects=projects)


@app.route('/project/new', methods=['GET', 'POST'])
def new_project():
    """Neues Projekt erstellen"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        angle_step = int(request.form.get('angle_step', 5))

        project = Project(name=name, description=description, angle_step=angle_step)
        project_manager.save_project(project)

        return redirect(url_for('index'))
    return render_template('project.html', mode='new')


@app.route('/project/<project_id>')
def view_project(project_id):
    """Ein vorhandenes Projekt anzeigen"""
    project = project_manager.get_project(project_id)
    if not project:
        return redirect(url_for('index'))
    return render_template('project.html', mode='view', project=project)


@app.route('/project/<project_id>/edit', methods=['GET', 'POST'])
def edit_project(project_id):
    """Ein vorhandenes Projekt bearbeiten"""
    project = project_manager.get_project(project_id)
    if not project:
        return redirect(url_for('index'))

    if request.method == 'POST':
        project.name = request.form.get('name')
        project.description = request.form.get('description')
        project.angle_step = int(request.form.get('angle_step', 5))
        project_manager.save_project(project)
        return redirect(url_for('view_project', project_id=project_id))

    return render_template('project.html', mode='edit', project=project)


@app.route('/project/<project_id>/delete')
def delete_project(project_id):
    """Ein Projekt löschen"""
    project_manager.delete_project(project_id)
    return redirect(url_for('index'))


@app.route('/project/<project_id>/capture', methods=['GET', 'POST'])
def capture_session(project_id):
    """Eine neue Aufnahmesession für ein Projekt starten"""
    global arduino_controller, camera_controller, turntable_controller

    project = project_manager.get_project(project_id)
    if not project:
        return redirect(url_for('index'))

    if not arduino_controller:
        arduino_controller = ArduinoController(settings.arduino_port, settings.arduino_baudrate)

    if not camera_controller:
        camera_controller = CameraController(settings.camera_type, settings.camera_device)

    if not turntable_controller:
        turntable_controller = TurntableController(arduino_controller, project.angle_step)

    if request.method == 'POST':
        # Session starten und Fotos machen
        if turntable_controller.start_session(project, camera_controller):
            return redirect(url_for('view_project', project_id=project_id))
        else:
            error = "Fehler beim Starten der Aufnahmesession"
            return render_template('capture.html', project=project, error=error)

    return render_template('capture.html', project=project)


@app.route('/settings', methods=['GET', 'POST'])
def app_settings():
    """Anwendungseinstellungen verwalten"""
    if request.method == 'POST':
        # Arduino-Einstellungen
        settings.arduino_port = request.form.get('arduino_port')
        settings.arduino_baudrate = int(request.form.get('arduino_baudrate', 9600))

        # Kamera-Einstellungen
        settings.camera_type = request.form.get('camera_type')
        settings.camera_device = request.form.get('camera_device')
        settings.camera_resolution = request.form.get('camera_resolution')

        # Einstellungen speichern
        settings.save()

        return redirect(url_for('index'))

    # Arduino-Ports finden
    arduino_ports = arduino_finder.find_arduino_ports()

    # Kameras finden
    cameras = camera_finder.find_cameras()
    gphoto_cameras = camera_finder.find_gphoto_cameras()

    return render_template('settings.html',
                           settings=settings,
                           arduino_ports=arduino_ports,
                           cameras=cameras,
                           gphoto_cameras=gphoto_cameras)


@app.route('/viewer/<project_id>/<session_id>')
def view_360(project_id, session_id):
    """360°-Viewer für eine Fotosession anzeigen"""
    project = project_manager.get_project(project_id)
    if not project:
        return redirect(url_for('index'))

    session = project.get_session(session_id)
    if not session:
        return redirect(url_for('view_project', project_id=project_id))

    return render_template('viewer.html', project=project, session=session)


@app.route('/logs')
def view_logs():
    """Anzeige der Anwendungslogs"""
    log_file = os.path.join(os.path.dirname(__file__), 'app.log')
    logs = []

    try:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()
                logs.reverse()  # Neueste Logs zuerst
        else:
            logs = ["Keine Logdatei gefunden."]
    except Exception as e:
        logs = [f"Fehler beim Lesen der Logdatei: {str(e)}"]

    return render_template('logs.html', logs=logs)


@app.route('/project/<project_id>/session/<session_id>/background-removal')
def background_removal(project_id, session_id):
    """Hintergrundentfernung für eine Fotosession"""
    project = project_manager.get_project(project_id)
    if not project:
        return redirect(url_for('index'))

    session = project.get_session(session_id)
    if not session:
        return redirect(url_for('view_project', project_id=project_id))

    # KI-Verfügbarkeit prüfen
    ai_available = background_remover.is_available()
    ai_device = background_remover.device
    ai_model = background_remover.model_type if ai_available else None

    return render_template('background_removal.html',
                           project=project,
                           session=session,
                           ai_available=ai_available,
                           ai_device=ai_device,
                           ai_model=ai_model)


@app.route('/api/project/<project_id>/sessions')
def api_project_sessions(project_id):
    """API-Endpunkt zum Abrufen der Sessions eines Projekts"""
    project = project_manager.get_project(project_id)
    if not project:
        return jsonify({'error': 'Projekt nicht gefunden'}), 404

    sessions = [session.to_dict() for session in project.sessions]
    return jsonify(sessions)


@app.route('/api/turntable/move', methods=['POST'])
def api_move_turntable():
    """API-Endpunkt zum Bewegen des Drehtellers"""
    global arduino_controller, turntable_controller

    if not arduino_controller:
        arduino_controller = ArduinoController(settings.arduino_port, settings.arduino_baudrate)

    if not turntable_controller:
        turntable_controller = TurntableController(arduino_controller, 5)

    degrees = int(request.form.get('degrees', 5))
    success = turntable_controller.move_degrees(degrees)

    return jsonify({'success': success})


@app.route('/api/camera/capture', methods=['POST'])
def api_capture_photo():
    """API-Endpunkt zum Aufnehmen eines Fotos"""
    global camera_controller

    if not camera_controller:
        camera_controller = CameraController(settings.camera_type, settings.camera_device)

    project_id = request.form.get('project_id')
    session_id = request.form.get('session_id')
    angle = int(request.form.get('angle', 0))

    photo_path = path_manager.get_photo_path(project_id, session_id, angle)
    success = camera_controller.capture_photo(photo_path)

    return jsonify({'success': success, 'path': photo_path if success else None})


@app.route('/api/background/remove', methods=['POST'])
def api_remove_background():
    """API-Endpunkt zur Hintergrundentfernung für ein einzelnes Bild"""
    image_path = request.form.get('image_path')
    reference_path = request.form.get('reference_path', None)
    use_ai = request.form.get('use_ai', 'true').lower() == 'true'

    if not image_path or not os.path.exists(image_path):
        return jsonify({'error': 'Ungültiger Bildpfad'}), 400

    output_path = os.path.splitext(image_path)[0] + '_transparent.png'

    if reference_path and os.path.exists(reference_path):
        success = background_remover.remove_background_with_reference(image_path, reference_path, output_path)
    elif use_ai:
        success = background_remover.remove_background_with_ai(image_path, output_path)
    else:
        return jsonify({'error': 'Keine gültige Methode zur Hintergrundentfernung angegeben'}), 400

    return jsonify({
        'success': success,
        'image_path': image_path,
        'output_path': output_path if success else None
    })


@app.route('/api/project/<project_id>/session/<session_id>/background/remove', methods=['POST'])
def api_remove_project_backgrounds(project_id, session_id):
    """API-Endpunkt zur Hintergrundentfernung für alle Bilder einer Session"""
    project = project_manager.get_project(project_id)
    if not project:
        return jsonify({'error': 'Projekt nicht gefunden'}), 404

    session = project.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session nicht gefunden'}), 404

    reference_path = request.form.get('reference_path', None)
    use_ai = request.form.get('use_ai', 'true').lower() == 'true'

    result = background_remover.process_project_images(project, session, reference_path, use_ai)

    return jsonify(result)


@app.route('/api/status/arduino')
def api_arduino_status():
    """API-Endpunkt zum Abrufen des Arduino-Status"""
    global arduino_controller

    if not arduino_controller:
        try:
            arduino_controller = ArduinoController(settings.arduino_port, settings.arduino_baudrate)
        except Exception as e:
            logging.error(f"Fehler beim Initialisieren des Arduino-Controllers: {e}")
            return jsonify({'connected': False, 'error': str(e)})

    connected = arduino_controller.is_connected()

    return jsonify({
        'connected': connected,
        'port': settings.arduino_port,
        'baudrate': settings.arduino_baudrate
    })


@app.route('/api/status/camera')
def api_camera_status():
    """API-Endpunkt zum Abrufen des Kamera-Status"""
    global camera_controller

    if not camera_controller:
        try:
            camera_controller = CameraController(settings.camera_type, settings.camera_device)
        except Exception as e:
            logging.error(f"Fehler beim Initialisieren des Kamera-Controllers: {e}")
            return jsonify({'available': False, 'error': str(e)})

    # Kamera testen
    test_available = False
    if settings.camera_type == 'webcam':
        test_available = camera_finder.test_webcam(settings.camera_device)
    elif settings.camera_type == 'gphoto2':
        test_available = camera_finder.test_gphoto2_camera(settings.camera_device)

    return jsonify({
        'available': test_available,
        'type': settings.camera_type,
        'device': settings.camera_device,
        'resolution': settings.camera_resolution
    })


@app.route('/api/status/background-removal')
def api_background_removal_status():
    """API-Endpunkt zum Abrufen des Status der Hintergrundentfernung"""
    is_available = background_remover.is_available()

    return jsonify({
        'available': is_available,
        'device': background_remover.device,
        'model_type': background_remover.model_type if is_available else None
    })


@app.route('/api/test/arduino', methods=['POST'])
def api_test_arduino():
    """API-Endpunkt zum Testen des Arduino"""
    port = request.form.get('port', settings.arduino_port)
    baudrate = int(request.form.get('baudrate', settings.arduino_baudrate))

    # Temporärer Arduino-Controller für den Test
    test_controller = ArduinoController(port, baudrate)

    if test_controller.is_connected():
        # Kurzer Motor-Test
        success = test_controller.turn_motor_on()
        if success:
            # 1 Sekunde warten und dann Motor ausschalten
            import time
            time.sleep(1)
            test_controller.turn_motor_off()

        test_controller.disconnect()

        return jsonify({
            'success': success,
            'port': port,
            'baudrate': baudrate
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Konnte keine Verbindung zum Arduino herstellen'
        })


@app.route('/api/test/camera', methods=['POST'])
def api_test_camera():
    """API-Endpunkt zum Testen der Kamera"""
    camera_type = request.form.get('type', settings.camera_type)
    camera_device = request.form.get('device', settings.camera_device)
    resolution = request.form.get('resolution', settings.camera_resolution)

    # Temporärer Pfad für das Testbild
    test_image_path = os.path.join(path_manager.temp_dir, 'camera_test.jpg')

    # Temporärer Kamera-Controller für den Test
    test_controller = CameraController(camera_type, camera_device, resolution)

    success = test_controller.capture_photo(test_image_path)

    if success and os.path.exists(test_image_path):
        # Bild wurde erfolgreich aufgenommen
        image_url = f"/static/temp/camera_test.jpg?t={int(time.time())}"
        return jsonify({
            'success': True,
            'image_url': image_url,
            'type': camera_type,
            'device': camera_device
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Konnte kein Foto aufnehmen'
        })


@app.route('/api/test/background-removal', methods=['POST'])
def api_test_background_removal():
    """API-Endpunkt zum Testen der Hintergrundentfernung"""
    if not background_remover.is_available():
        return jsonify({
            'success': False,
            'error': 'Hintergrundentfernung nicht verfügbar'
        })

    image_path = request.form.get('image_path')
    if not image_path or not os.path.exists(image_path):
        return jsonify({
            'success': False,
            'error': 'Ungültiger Bildpfad'
        })

    output_path = os.path.join(path_manager.temp_dir, 'background_removal_test.png')

    success = background_remover.remove_background_with_ai(image_path, output_path)

    if success and os.path.exists(output_path):
        # Bild wurde erfolgreich verarbeitet
        image_url = f"/static/temp/background_removal_test.png?t={int(time.time())}"
        return jsonify({
            'success': True,
            'image_url': image_url,
            'model_type': background_remover.model_type
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Konnte Hintergrund nicht entfernen'
        })


@app.route('/api/logs')
def api_logs():
    """API-Endpunkt zum Abrufen der Anwendungslogs"""
    log_file = os.path.join(os.path.dirname(__file__), 'app.log')
    logs = []

    try:
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()
                logs.reverse()  # Neueste Logs zuerst

        # Optionales Filtern nach Level und Anzahl
        level = request.args.get('level')
        limit = request.args.get('limit')

        if level:
            logs = [log for log in logs if level.upper() in log]

        if limit and limit.isdigit():
            logs = logs[:int(limit)]

        return jsonify({
            'success': True,
            'logs': logs
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


if __name__ == '__main__':
    # Beim Start der Anwendung die Controller initialisieren
    try:
        arduino_controller = ArduinoController(settings.arduino_port, settings.arduino_baudrate)
        camera_controller = CameraController(settings.camera_type, settings.camera_device)
        turntable_controller = TurntableController(arduino_controller, 5)
    except Exception as e:
        print(f"Warnung: Controller konnten nicht initialisiert werden: {e}")
        print("Die Anwendung wird trotzdem gestartet. Bitte überprüfen Sie die Einstellungen.")

    # Webserver starten
    app.run(host='0.0.0.0', port=5000, debug=True)
