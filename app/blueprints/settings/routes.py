# app/blueprints/settings/routes.py
import json
import logging
from flask import render_template, request, jsonify, redirect, url_for
from app.blueprints.settings import settings_bp
from app.utils.config_manager import config_manager
from app import update_camera_controller

# Logger einrichten
logger = logging.getLogger(__name__)

@settings_bp.route('/')
def settings():
    """Zeigt die Einstellungsseite an"""
    return render_template('settings.html')

@settings_bp.route('/get_config')
def get_config():
    """Gibt die aktuelle Konfiguration zurück"""
    return jsonify(config_manager.config)

@settings_bp.route('/save_config', methods=['POST'])
def save_config():
    """Speichert die Konfiguration"""
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
        logger.debug(f"Empfangene Konfiguration: {json.dumps(new_config, indent=2)}")
        
        # Rekursive Aktualisierung der Konfiguration
        def recursive_update(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    recursive_update(target[key], value)
                else:
                    target[key] = value
        
        # Kopie der aktuellen Konfiguration erstellen
        merged_config = config_manager.config.copy()
        
        # Neue Konfiguration rekursiv zusammenführen
        recursive_update(merged_config, new_config)
        
        # Versuchen, die Konfiguration zu speichern
        config_save_success = config_manager.save_config(merged_config)
        
        if config_save_success:
            logger.info(f"Konfiguration erfolgreich gespeichert: {config_manager.config_path}")
            
            # CameraController aktualisieren, damit die neuen Einstellungen verwendet werden
            update_camera_controller()
            logger.info("Camera-Controller mit aktuellen Einstellungen aktualisiert")
            
            return jsonify({
                "status": "success", 
                "message": "Konfiguration erfolgreich gespeichert",
                "config": merged_config
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Fehler beim Speichern der Konfiguration"
            }), 500
            
    except Exception as e:
        logger.error(f"Allgemeiner Fehler beim Speichern der Konfiguration: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Allgemeiner Fehler: {str(e)}"
        }), 500

@settings_bp.route('/available_webcams')
def available_webcams():
    """Gibt eine Liste verfügbarer Webcams zurück"""
    try:
        import sys
        import os
        import cv2
        
        # Den Root-Pfad zum Projekt hinzufügen, damit der Import funktioniert
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
        
        from app.utils.webcam_detection_helper import find_working_webcam, get_camera_capabilities
        from app.controllers.camera_controller import CameraController
        
        # Liste der möglichen Video-Geräte
        devices = [f'/dev/video{i}' for i in range(10)]
        
        # Verfügbare Webcams ermitteln
        webcams = []
        for device in devices:
            if os.path.exists(device):
                try:
                    # Versuchen, Kamera-Eigenschaften abzurufen
                    capabilities = get_camera_capabilities(device)
                    
                    # Wenn Auflösungen gefunden wurden, ist das wahrscheinlich eine Webcam
                    if capabilities.get('supported_resolutions'):
                        webcam_info = {
                            'path': device,
                            'name': f'Webcam {device.split("/")[-1]}',
                            'resolutions': capabilities.get('supported_resolutions', []),
                            'max_width': capabilities.get('max_width', 0),
                            'max_height': capabilities.get('max_height', 0)
                        }
                        webcams.append(webcam_info)
                except Exception as e:
                    logger.error(f"Fehler beim Prüfen von Webcam {device}: {e}")
        
        # Ergebnisse zurückgeben
        return jsonify({
            'status': 'success',
            'webcams': webcams
        })
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der verfügbaren Webcams: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'webcams': []
        }), 500

@settings_bp.route('/available_cameras')
def available_cameras():
    """Gibt eine Liste aller verfügbaren Kameras zurück (Webcams und DSLR)"""
    try:
        import sys
        import os
        import glob
        import cv2
        import logging
        import subprocess
        import re
        
        logger = logging.getLogger(__name__)
        
        # Rückgabestruktur initialisieren
        result = {
            'status': 'success',
            'webcams': [],
            'gphoto2': []
        }
        
        # Webcam-Modelle ermitteln mit v4l2-ctl
        webcam_models = {}
        try:
            result_devices = subprocess.run(['v4l2-ctl', '--list-devices'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      text=True,
                                      timeout=5)
            
            if result_devices.returncode == 0:
                lines = result_devices.stdout.strip().split('\n')
                current_model = None
                
                for line in lines:
                    if not line.startswith('\t') and line.strip():
                        # Das ist ein Modellname
                        current_model = line.strip().rstrip(':')
                    elif line.startswith('\t') and current_model and '/dev/video' in line:
                        # Das ist ein Gerätepfad
                        device_path = line.strip()
                        webcam_models[device_path] = current_model
                        
                logger.info(f"Gefundene Webcam-Modelle: {webcam_models}")
        except Exception as e:
            logger.error(f"Fehler bei der v4l2-Modellerkennung: {str(e)}")
        
        # Auflösungen der Webcams ermitteln
        def get_webcam_resolutions(device):
            resolutions = []
            try:
                # Standardauflösungen testen
                standard_resolutions = [
                    (640, 480),    # VGA
                    (800, 600),    # SVGA 
                    (1024, 768),   # XGA
                    (1280, 720),   # HD
                    (1280, 960),   # SXGA-
                    (1280, 1024),  # SXGA
                    (1440, 1080),  # HD+
                    (1600, 1200),  # UXGA
                    (1920, 1080),  # Full HD
                    (2048, 1536),  # QXGA
                    (2560, 1440),  # QHD
                    (3840, 2160)   # 4K UHD
                ]

                cap = cv2.VideoCapture(device)
                if cap.isOpened():
                    # Höchste unterstützte Auflösung finden
                    for width, height in standard_resolutions:
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                        actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                        actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                        
                        # Wenn die Auflösung ungefähr stimmt (Toleranz für Rundungsfehler)
                        if (abs(actual_width - width) < 10) and (abs(actual_height - height) < 10):
                            resolution_str = f"{int(actual_width)}x{int(actual_height)}"
                            logger.debug(f"Webcam {device} unterstützt Auflösung: {resolution_str}")
                            if resolution_str not in [r['resolution'] for r in resolutions]:
                                resolutions.append({
                                    'resolution': resolution_str,
                                    'width': int(actual_width),
                                    'height': int(actual_height)
                                })
                    
                    # Falls keine Auflösungen gefunden wurden, Standardwerte hinzufügen
                    if not resolutions:
                        # Wenn keine der Standardauflösungen funktioniert, aktuelle Werte nehmen
                        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
                        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                        resolution_str = f"{int(width)}x{int(height)}"
                        logger.debug(f"Keine Standardauflösungen für Webcam {device} gefunden, verwende: {resolution_str}")
                        resolutions.append({
                            'resolution': resolution_str,
                            'width': int(width),
                            'height': int(height)
                        })
                        
                        # Füge mindestens VGA und HD hinzu, wenn nichts gefunden wurde
                        logger.debug(f"Füge Standardauflösungen für Webcam {device} hinzu")
                        for res in [(640, 480), (1280, 720), (1920, 1080)]:
                            w, h = res
                            res_str = f"{w}x{h}"
                            if res_str not in [r['resolution'] for r in resolutions]:
                                resolutions.append({
                                    'resolution': res_str,
                                    'width': w,
                                    'height': h
                                })
                            
                    cap.release()
                    logger.info(f"Erkannte Auflösungen für {device}: {resolutions}")
            except Exception as e:
                logger.error(f"Fehler beim Ermitteln der Auflösungen für {device}: {str(e)}")
                # Standardauflösungen zurückgeben, wenn ein Fehler auftritt
                for res in [(640, 480), (1280, 720), (1920, 1080)]:
                    w, h = res
                    res_str = f"{w}x{h}"
                    resolutions.append({
                        'resolution': res_str,
                        'width': w,
                        'height': h
                    })
                logger.info(f"Verwende Standardauflösungen für {device}: {resolutions}")
            
            return resolutions
        
        # Webcams mit direktem OpenCV-Zugriff testen
        video_devices = glob.glob('/dev/video*')
        logger.info(f"Gefundene Video-Geräte: {video_devices}")
        
        for device in video_devices:
            try:
                logger.debug(f"Teste Gerät: {device}")
                cap = cv2.VideoCapture(device)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None and frame.size > 0:
                        # Modell und Name bestimmen
                        model = webcam_models.get(device, "Generische Webcam")
                        name = model
                        
                        # Microsoft-Webcam erkennen
                        if "microsoft" in model.lower():
                            name = f"Microsoft Webcam ({device})"
                        
                        # Auflösungen ermitteln
                        resolutions = get_webcam_resolutions(device)
                        
                        # Funktioniert!
                        result['webcams'].append({
                            'path': device,
                            'name': name,
                            'model': model,
                            'status': 'working',
                            'resolutions': resolutions
                        })
                        logger.info(f"Funktionierende Webcam gefunden: {name} ({device})")
                    else:
                        logger.warning(f"Webcam {device} öffnet sich, liefert aber kein gültiges Bild")
                    cap.release()
                else:
                    logger.warning(f"Webcam {device} konnte nicht geöffnet werden")
            except Exception as e:
                logger.error(f"Fehler beim Testen von {device}: {str(e)}")

        # DSLR-Kameras mit gphoto2 erkennen
        try:
            result_gphoto = subprocess.run(['gphoto2', '--auto-detect'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      text=True,
                                      timeout=5)
            
            if result_gphoto.returncode == 0:
                # Ausgabezeilen verarbeiten
                lines = result_gphoto.stdout.strip().split('\n')
                
                # Ersten paar Zeilen überspringen (Header)
                camera_lines = [line for line in lines if "usb:" in line.lower()]
                
                for line in camera_lines:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        # Letzter Teil ist der Gerätepfad
                        model = ' '.join(parts[:-1])
                        device = parts[-1]
                        
                        # DSLR-Auflösungen ermitteln
                        resolutions = []
                        try:
                            # Verfügbare Bildgrößen abfragen
                            result_sizes = subprocess.run(['gphoto2', '--port', device, '--get-config', 'imagesize'],
                                                    stdout=subprocess.PIPE,
                                                    stderr=subprocess.PIPE,
                                                    text=True,
                                                    timeout=5)
                            
                            if result_sizes.returncode == 0:
                                # Suche nach Auflösungen im Format "WidthxHeight"
                                size_lines = result_sizes.stdout.strip().split('\n')
                                
                                for size_line in size_lines:
                                    # Suche nach Auflösungsangaben wie 640x480, 1920x1080 usw.
                                    resolution_match = re.search(r'(\d+)x(\d+)', size_line)
                                    if resolution_match:
                                        width = int(resolution_match.group(1))
                                        height = int(resolution_match.group(2))
                                        resolutions.append({
                                            'resolution': f"{width}x{height}",
                                            'width': width,
                                            'height': height
                                        })
                        except Exception as e:
                            logger.error(f"Fehler beim Ermitteln der DSLR-Auflösungen: {str(e)}")
                        
                        # Wenn keine Auflösungen gefunden wurden, Standardwerte verwenden
                        if not resolutions:
                            resolutions = [
                                {'resolution': '4608x3456', 'width': 4608, 'height': 3456},  # Typische DSLR
                                {'resolution': '5184x3456', 'width': 5184, 'height': 3456},  # Canon EOS
                                {'resolution': '6000x4000', 'width': 6000, 'height': 4000}   # Nikon
                            ]
                        
                        result['gphoto2'].append({
                            'device': device,
                            'name': model,
                            'model': model,
                            'status': 'working',
                            'resolutions': resolutions
                        })
                        logger.info(f"DSLR-Kamera gefunden: {model} ({device})")
        except Exception as e:
            logger.error(f"Fehler bei DSLR-Erkennung: {str(e)}")
            
        logger.info(f"Kamera-Erkennungs-Ergebnis: {result}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der verfügbaren Kameras: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'webcams': [],
            'gphoto2': []
        }), 500

@settings_bp.route('/test_camera', methods=['POST'])
def test_camera():
    """Nimmt ein Testfoto mit der ausgewählten Kamera auf"""
    try:
        import json
        import time
        import os
        import subprocess
        import uuid
        import cv2
        import logging
        from flask import current_app
        
        logger = logging.getLogger(__name__)
        
        # Pfad für Testfotos
        test_photo_dir = os.path.join(current_app.static_folder, 'test_photos')
        os.makedirs(test_photo_dir, exist_ok=True)
        
        # Anfragedaten extrahieren
        data = request.json
        camera_type = data.get('camera_type', 'webcam')
        camera_path = data.get('camera_path', '')
        width = data.get('width', 1280)
        height = data.get('height', 720)
        
        # Eindeutigen Dateinamen generieren
        timestamp = int(time.time())
        filename = f"test_{camera_type}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
        output_path = os.path.join(test_photo_dir, filename)
        relative_path = f"/static/test_photos/{filename}"
        
        # Je nach Kameratyp unterschiedliche Aufnahmemethode
        success = False
        message = ""
        
        if camera_type == 'webcam':
            try:
                # Mit OpenCV aufnehmen
                cap = cv2.VideoCapture(camera_path)
                if not cap.isOpened():
                    return jsonify({'status': 'error', 'message': 'Webcam konnte nicht geöffnet werden'}), 400
                
                # Auflösung einstellen
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                # Bild aufnehmen
                ret, frame = cap.read()
                cap.release()
                
                if ret:
                    cv2.imwrite(output_path, frame)
                    success = True
                    message = "Testbild erfolgreich aufgenommen"
                else:
                    message = "Fehler beim Aufnehmen des Testbilds"
            except Exception as e:
                logger.error(f"Fehler bei Webcam-Aufnahme: {str(e)}")
                message = f"Fehler: {str(e)}"
        
        elif camera_type == 'gphoto2':
            try:
                # Mit gphoto2 aufnehmen
                cmd = [
                    'gphoto2',
                    '--port', camera_path,
                    '--capture-image-and-download',
                    '--filename', output_path,
                    '--force-overwrite'
                ]
                
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0 and os.path.exists(output_path):
                    success = True
                    message = "Testbild erfolgreich aufgenommen"
                else:
                    message = f"gphoto2 Fehler: {result.stderr}"
            except Exception as e:
                logger.error(f"Fehler bei DSLR-Aufnahme: {str(e)}")
                message = f"Fehler: {str(e)}"
        
        else:
            message = f"Ungültiger Kameratyp: {camera_type}"
        
        # Ergebnis zurückgeben
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'image_path': relative_path
            })
        else:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
            
    except Exception as e:
        logger.error(f"Fehler beim Testfoto: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Unerwarteter Fehler: {str(e)}"
        }), 500
