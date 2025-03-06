from flask import Blueprint, jsonify, request
import subprocess
import traceback
import os
from app.utils.device_detector import device_detector
from app.services.config_manager import config_manager

device_bp = Blueprint('device', __name__)

@device_bp.route('/refresh', methods=['POST'])
def refresh_devices():
    """Aktualisiert die Liste der erkannten Geräte"""
    try:
        # Device Detector neu initialisieren und alle Geräte suchen
        device_detector.get_devices()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@device_bp.route('/update_config', methods=['POST'])
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
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)})

@device_bp.route('/restart_service', methods=['POST'])
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

@device_bp.route('/fix_permissions', methods=['POST'])
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

@device_bp.route('/test_gphoto2', methods=['POST'])
def test_gphoto2():
    """Testet die gphoto2-Verbindung zur Kamera"""
    try:
        # Teste, ob gphoto2 installiert ist
        result = subprocess.run(['gphoto2', '--version'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, 
                              text=True)
        
        if result.returncode != 0:
            return jsonify({
                "status": "error", 
                "message": "gphoto2 ist nicht installiert oder nicht im PATH"
            })
        
        # Erkenne angeschlossene Kameras
        detect_result = subprocess.run(['gphoto2', '--auto-detect'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, 
                                     text=True)
        
        if "No camera found" in detect_result.stdout or "No camera found" in detect_result.stderr:
            return jsonify({
                "status": "error", 
                "message": "Keine Kamera gefunden. Überprüfe die Verbindung und ob die Kamera eingeschaltet ist."
            })
        
        # Teste Fotoaufnahme in ein temporäres Verzeichnis
        test_dir = 'static/test'
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, f"test_{int(time.time())}.jpg")
        
        # Versuche, ein Testfoto zu machen
        cmd = [
            'gphoto2',
            '--force-overwrite',
            '--set-config', 'capturetarget=1',
            '--capture-image-and-download',
            '--filename', test_file
        ]
        
        capture_result = subprocess.run(cmd, 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE, 
                                      text=True,
                                      timeout=30)
        
        # Überprüfe, ob das Foto erstellt wurde
        if os.path.exists(test_file):
            return jsonify({
                "status": "success",
                "message": "Testfoto erfolgreich aufgenommen",
                "test_file": f"/static/test/{os.path.basename(test_file)}"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Testfoto konnte nicht erstellt werden",
                "stdout": capture_result.stdout,
                "stderr": capture_result.stderr
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "status": "error",
            "message": "Timeout beim Testen von gphoto2. Die Kamera reagiert nicht rechtzeitig."
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        })
