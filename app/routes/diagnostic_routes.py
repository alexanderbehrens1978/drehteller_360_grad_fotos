from flask import Blueprint, render_template, jsonify
import os
import sys
import platform
import subprocess
import time
import serial
from app.utils.device_detector import device_detector
from app.services.config_manager import config_manager

diagnostic_bp = Blueprint('diagnostic', __name__)

@diagnostic_bp.route('/')
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
    
    # Teste gphoto2, wenn vorhanden
    try:
        gphoto2_output = subprocess.run(['gphoto2', '--auto-detect'], 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE, 
                                      text=True)
        diagnostic_data['gphoto2'] = {
            'available': True,
            'output': gphoto2_output.stdout,
            'error': gphoto2_output.stderr if gphoto2_output.stderr else None
        }
    except Exception as e:
        diagnostic_data['gphoto2'] = {
            'available': False,
            'error': str(e)
        }
    
    return render_template('diagnostics.html', data=diagnostic_data)
