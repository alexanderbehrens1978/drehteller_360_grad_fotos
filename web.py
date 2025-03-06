from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import json
import time
import serial
import platform
import sys
import subprocess
from config_manager import config_manager
from device_detector import device_detector

app = Flask(__name__)

# Globale Variablen
arduino = None


def init_arduino():
    """
    Initialisiert die Arduino-Verbindung
    """
    global arduino

    # Simulator-Modus prüfen
    if config_manager.get('simulator.enabled', True):
        print("Simulator-Modus aktiv, keine Arduino-Verbindung erforderlich")
        return None

    try:
        # Arduino-Port aus Konfiguration holen
        port = config_manager.get('arduino.port', '/dev/ttyACM0')
        baudrate = config_manager.get('arduino.baudrate', 9600)

        # Neue Verbindung öffnen
        arduino = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)  # Warten auf Arduino Reset

        print(f"Arduino-Verbindung hergestellt: {port} ({baudrate} Baud)")
        return arduino
    except Exception as e:
        print(f"Fehler beim Initialisieren der Arduino-Verbindung: {e}")
        return None


def rotate_teller(degrees):
    """
    Rotiert den Drehteller um die angegebenen Grad.
    Öffnet für jeden Befehl eine frische Verbindung.
    """
    # Wenn Simulator-Modus aktiv ist
    if config_manager.get('simulator.enabled', True):
        print(f"Simulator: Rotation um {degrees} Grad")
        return True

    try:
        # Arduino-Port aus Konfiguration holen
        port = config_manager.get('arduino.port', '/dev/ttyACM0')
        baudrate = config_manager.get('arduino.baudrate', 9600)

        # Neue Verbindung öffnen
        print(f"Öffne Arduino-Verbindung: {port}")
        arduino_conn = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)  # Warten auf Arduino Reset

        # Befehl zum Einschalten senden
        print("Sende '1' (Relais ein)")
        arduino_conn.write(b'1')

        # Berechnete Zeit für die Drehung warten
        rotation_time = abs(degrees) / 0.8  # 0.8° pro Sekunde
        print(f"Warte auf Rotation ({rotation_time} Sekunden)")
        time.sleep(rotation_time)

        # Befehl zum Ausschalten senden
        print("Sende '0' (Relais aus)")
        arduino_conn.write(b'0')
        time.sleep(0.5)

        # Verbindung schließen
        arduino_conn.close()

        print(f"Drehteller um {degrees} Grad gedreht.")
        return True
    except Exception as e:
        print(f"Fehler beim Drehen des Tellers: {e}")
        # Versuchen, die Verbindung zu schließen, falls sie noch offen ist
        try:
            if 'arduino_conn' in locals() and arduino_conn.is_open:
                arduino_conn.close()
        except:
            pass
        return False


def take_photo(filename=None):
    """
    Nimmt ein Foto auf
    """
    # Wenn Simulator-Modus aktiv ist
    if config_manager.get('simulator.enabled', True):
        print("Simulator: Foto aufnehmen")
        # Hier würde der Simulator-Code stehen
        return "simulation.jpg"

    try:
        # Pfad für das Speichern von Fotos
        photo_dir = 'static/photos'
        os.makedirs(photo_dir, exist_ok=True)

        # Falls kein Dateiname angegeben wurde, einen generieren
        if not filename:
            filename = f"photo_{int(time.time())}.jpg"

        # Kamera-Einstellungen aus Konfiguration holen
        camera_type = config_manager.get('camera.type', 'webcam')
        camera_device = config_manager.get('camera.device_path', '/dev/video0')

        # Je nach Kameratyp unterschiedliche Aufnahmemethode
        if camera_type == 'gphoto2':
            # DSLR mit gphoto2
            output_path = os.path.join(photo_dir, filename)
            subprocess.run(['gphoto2', '--capture-image-and-download', '--filename', output_path])
        else:
            # Webcam mit OpenCV
            import cv2
            cap = cv2.VideoCapture(camera_device)

            # Auflösung einstellen
            width = config_manager.get('camera.resolution.width', 1280)
            height = config_manager.get('camera.resolution.height', 720)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            # Foto aufnehmen
            ret, frame = cap.read()
            if not ret:
                raise Exception("Fehler beim Auslesen der Kamera")

            # Foto speichern
            output_path = os.path.join(photo_dir, filename)
            cv2.imwrite(output_path, frame)
            cap.release()

        print(f"Foto aufgenommen und gespeichert als: {filename}")
        return filename
    except Exception as e:
        print(f"Fehler beim Aufnehmen des Fotos: {e}")
        return None


# Routen
@app.route('/')
def index():
    """Hauptseite"""
    return render_template('index.html')


@app.route('/settings')
def settings():
    """Einstellungsseite"""
    return render_template('settings.html')


@app.route('/rotate', methods=['POST'])
def rotate():
    """Rotiert den Drehteller und macht ein Foto"""
    try:
        # Daten aus der Anfrage holen
        degrees = int(request.form['degrees'])

        # Drehteller rotieren
        rotation_success = rotate_teller(degrees)
        if not rotation_success:
            return 'Fehler bei der Rotation', 500

        # Foto aufnehmen
        photo = take_photo()
        if not photo:
            return 'Fehler beim Aufnehmen des Fotos', 500

        # Erfolg zurückgeben
        return f'/static/photos/{photo}'
    except Exception as e:
        print(f"Fehler bei der Rotation: {e}")
        return str(e), 500


@app.route('/get_config')
def get_config():
    """Gibt die aktuelle Konfiguration zurück"""
    return jsonify(config_manager.config)


@app.route('/save_config', methods=['POST'])
def save_config():
    """Speichert die Konfiguration"""
    try:
        # Check if request contains JSON data
        if not request.is_json:
            print("Request is not JSON")
            return jsonify({"status": "error", "message": "Missing JSON data"}), 400

        new_config = request.json
        if not new_config:
            print("Empty JSON data")
            return jsonify({"status": "error", "message": "Empty configuration data"}), 400

        print("Received configuration:", json.dumps(new_config, indent=2))

        # Use direct file writing instead of config_manager.save_config
        try:
            # Load current config file
            config_path = config_manager.config_path

            # Read current config
            with open(config_path, 'r') as f:
                current_config = json.load(f)

            # Update configuration with new values
            def update_config(target, source):
                for key, value in source.items():
                    if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                        update_config(target[key], value)
                    else:
                        target[key] = value

            # Merge configs
            update_config(current_config, new_config)

            # Write back to file
            with open(config_path, 'w') as f:
                json.dump(current_config, f, indent=4)

            # Update config_manager's config
            config_manager.config = current_config

            print("Configuration saved successfully")
            return jsonify({"status": "success"})
        except Exception as e:
            import traceback
            print("Error saving configuration:", str(e))
            traceback.print_exc()
            return jsonify({"status": "error", "message": f"Error saving config: {str(e)}"}), 500

    except Exception as e:
        import traceback
        print("General error:", str(e))
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/static/photos/<filename>')
def serve_photo(filename):
    """Liefert ein Foto aus"""
    return send_from_directory('static/photos', filename)


# --- NEUE DIAGNOSE-FUNKTIONEN ---

@app.route('/diagnostics')
def diagnostics():
    """Diagnoseseite, die Informationen zu den angeschlossenen Geräten anzeigt"""
    diagnostic_data = {
        'system': {
            'python_version': sys.version,
            'platform': platform.platform(),
            'user': os.getlogin(),
            'current_directory': os.getcwd()
        },
        'devices': device_detector.get_devices(),
        'config': config_manager.config
    }

    # Füge Infos über serielle Ports hinzu
    try:
        import serial.tools.list_ports
        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append({
                'device': port.device,
                'name': port.name,
                'description': port.description,
                'hwid': port.hwid,
                'vid': hex(port.vid) if port.vid is not None else None,
                'pid': hex(port.pid) if port.pid is not None else None
            })
        diagnostic_data['serial_ports'] = ports
    except Exception as e:
        diagnostic_data['serial_ports_error'] = str(e)

    # Überprüfe Dateiberechtigungen
    config_path = config_manager.config_path
    diagnostic_data['file_permissions'] = {
        'config_path': config_path,
        'exists': os.path.exists(config_path),
        'readable': os.access(config_path, os.R_OK) if os.path.exists(config_path) else None,
        'writable': os.access(config_path, os.W_OK) if os.path.exists(config_path) else None,
        'permissions': oct(os.stat(config_path).st_mode)[-3:] if os.path.exists(config_path) else None
    }

    # Versuche, die Arduino-Verbindung zu testen
    if diagnostic_data['devices']['arduino']:
        arduino_port = diagnostic_data['devices']['arduino'][0]['port']
        try:
            with serial.Serial(arduino_port, 9600, timeout=1) as ser:
                time.sleep(2)  # Warte auf Arduino Reset
                ser.write(b'1')  # Sende Test-Befehl
                time.sleep(0.5)
                ser.write(b'0')
                diagnostic_data['arduino_test'] = 'success'
        except Exception as e:
            diagnostic_data['arduino_test'] = f'error: {str(e)}'

    return render_template('diagnostics.html', data=diagnostic_data)


@app.route('/refresh_devices', methods=['POST'])
def refresh_devices():
    """Aktualisiert die Liste der erkannten Geräte"""
    try:
        # Device Detector neu initialisieren und alle Geräte suchen
        device_detector.get_devices()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/update_config_from_devices', methods=['POST'])
def update_config_from_devices():
    """Aktualisiert die Konfiguration basierend auf erkannten Geräten"""
    try:
        # Aktuelle Konfiguration laden
        current_config = config_manager.config.copy()

        # Geräte erkennen
        devices = device_detector.get_devices()

        # Arduino-Konfiguration aktualisieren, wenn Geräte gefunden wurden
        if devices['arduino']:
            if 'arduino' not in current_config:
                current_config['arduino'] = {}
            current_config['arduino']['port'] = devices['arduino'][0]['port']

        # Kamera-Konfiguration aktualisieren, wenn Geräte gefunden wurden
        if 'camera' not in current_config:
            current_config['camera'] = {}

        if devices['webcam']:
            current_config['camera']['device_path'] = devices['webcam'][0]['device']
            current_config['camera']['type'] = 'webcam'
        elif devices['gphoto2']:
            current_config['camera']['device_path'] = 'auto'
            current_config['camera']['type'] = 'gphoto2'

        # Simulator deaktivieren, wenn echte Geräte gefunden wurden
        if devices['arduino'] or devices['webcam'] or devices['gphoto2']:
            if 'simulator' not in current_config:
                current_config['simulator'] = {}
            current_config['simulator']['enabled'] = False

        # Konfiguration speichern
        result = config_manager.save_config(current_config)

        if result:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Fehler beim Speichern der Konfiguration"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)})


@app.route('/restart_service', methods=['POST'])
def restart_service():
    """Startet den Drehteller-Service neu (erfordert sudo-Rechte)"""
    try:
        # Prüfen, ob wir sudo-Rechte haben
        result = subprocess.run(['systemctl', 'is-active', 'drehteller360.service'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Service neustarten
        subprocess.run(['sudo', 'systemctl', 'restart', 'drehteller360.service'],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/fix_permissions', methods=['POST'])
def fix_permissions():
    """Repariert die Berechtigungen für die Konfigurationsdatei"""
    try:
        config_path = config_manager.config_path

        # Prüfen, ob die Datei existiert
        if not os.path.exists(config_path):
            # Verzeichnis erstellen, falls es nicht existiert
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            # Leere Konfiguration erstellen
            with open(config_path, 'w') as f:
                json.dump({}, f)

        # Berechtigungen setzen
        # Achtung: Dies funktioniert nur, wenn der Webserver-Prozess entsprechende Rechte hat
        os.chmod(config_path, 0o644)

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    # Stelle sicher, dass die Verzeichnisse existieren
    os.makedirs('static/photos', exist_ok=True)
    os.makedirs('static/test', exist_ok=True)

    # Initialisiere Arduino-Verbindung
    init_arduino()

    # Starte die Flask-App
    host = config_manager.get('web.host', '0.0.0.0')
    port = config_manager.get('web.port', 5000)
    debug = config_manager.get('web.debug', True)

    app.run(host=host, port=port, debug=debug)
