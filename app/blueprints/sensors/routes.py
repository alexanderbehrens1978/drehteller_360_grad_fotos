import json
import logging
import requests
import serial
import time
from flask import render_template, request, jsonify, current_app
from app.blueprints.sensors import sensors_bp
from app.utils.config_manager import config_manager

# Logger einrichten
logger = logging.getLogger(__name__)

@sensors_bp.route('/')
def sensors():
    """Zeigt die Sensor-Einstellungsseite an"""
    return render_template('sensors.html')

@sensors_bp.route('/get_config')
def get_config():
    """Gibt die aktuelle Sensor-Konfiguration zurück"""
    # Stelle sicher, dass sensor_arduino existiert
    if 'sensor_arduino' not in config_manager.config:
        config_manager.config['sensor_arduino'] = {
            'connection_type': 'ethernet',
            'ip_address': '192.168.188.177',
            'port': 80,
            'serial_port': '/dev/ttyACM0',
            'baudrate': 9600,
            'sensor_type': 'proximity',
            'proximity_pin': 2,
            'inverse_signal': False,
            'detection_delay': 100,
            'threshold': 120,
            'led_color': 'white'
        }
        
    return jsonify(config_manager.config)

@sensors_bp.route('/save_config', methods=['POST'])
def save_config():
    """Speichert die Sensor-Konfiguration"""
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
        logger.debug(f"Empfangene Sensor-Konfiguration: {json.dumps(new_config, indent=2)}")
        
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
            logger.info(f"Sensor-Konfiguration erfolgreich gespeichert: {config_manager.config_path}")
            return jsonify({
                "status": "success", 
                "message": "Sensor-Konfiguration erfolgreich gespeichert",
                "config": merged_config
            })
        else:
            return jsonify({
                "status": "error", 
                "message": "Fehler beim Speichern der Sensor-Konfiguration"
            }), 500
            
    except Exception as e:
        logger.error(f"Allgemeiner Fehler beim Speichern der Sensor-Konfiguration: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Allgemeiner Fehler: {str(e)}"
        }), 500

@sensors_bp.route('/test_sensor', methods=['POST'])
def test_sensor():
    """Testet den konfigurierten Sensor"""
    try:
        # Anfragedaten extrahieren
        data = request.json
        
        if not data or 'sensor_arduino' not in data:
            return jsonify({
                "status": "error",
                "message": "Keine gültigen Sensor-Konfigurationsdaten empfangen"
            }), 400
        
        sensor_config = data['sensor_arduino']
        
        # Verbindungsart prüfen
        connection_type = sensor_config.get('connection_type', 'ethernet')
        
        if connection_type == 'disabled':
            return jsonify({
                "status": "warning",
                "message": "Sensor-Arduino ist deaktiviert. Bitte aktivieren Sie ihn, um Tests durchzuführen."
            })
        
        # Sensorstatus abrufen
        sensor_status = None
        
        if connection_type == 'ethernet':
            # Ethernet-Verbindung testen
            ip_address = sensor_config.get('ip_address', '192.168.188.177')
            port = sensor_config.get('port', 80)
            
            # Timeout für die HTTP-Anfrage
            timeout = 5  # 5 Sekunden
            
            try:
                # HTTP-Anfrage an den Arduino senden
                url = f"http://{ip_address}:{port}/status"
                response = requests.get(url, timeout=timeout)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        sensor_status = data.get('sensor_active', False)
                        
                        return jsonify({
                            "status": "success",
                            "message": f"Verbindung zum Sensor-Arduino erfolgreich hergestellt (Ethernet: {ip_address}:{port})",
                            "sensor_active": sensor_status
                        })
                    except json.JSONDecodeError:
                        return jsonify({
                            "status": "error",
                            "message": f"Ungültiges JSON-Format von Arduino erhalten: {response.text}"
                        })
                else:
                    return jsonify({
                        "status": "error",
                        "message": f"HTTP-Fehler: {response.status_code} - {response.text}"
                    })
            except requests.exceptions.Timeout:
                return jsonify({
                    "status": "error",
                    "message": f"Timeout bei der Verbindung zu {ip_address}:{port}"
                })
            except requests.exceptions.ConnectionError:
                return jsonify({
                    "status": "error",
                    "message": f"Verbindungsfehler zu {ip_address}:{port}. Überprüfen Sie die IP-Adresse und Netzwerkverbindung."
                })
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": f"Fehler bei der Ethernet-Verbindung: {str(e)}"
                })
                
        elif connection_type == 'serial':
            # Serielle Verbindung testen
            serial_port = sensor_config.get('serial_port', '/dev/ttyACM0')
            baudrate = sensor_config.get('baudrate', 9600)
            
            try:
                # Serielle Verbindung öffnen
                ser = serial.Serial(serial_port, baudrate, timeout=2)
                
                # Kurz warten, damit die Verbindung hergestellt werden kann
                time.sleep(1)
                
                # Buffer leeren
                ser.reset_input_buffer()
                
                # Anfrage senden
                ser.write(b'status\n')
                
                # Antwort lesen
                response = ser.readline().decode('utf-8').strip()
                
                # Verbindung schließen
                ser.close()
                
                if response:
                    try:
                        # Antwort als JSON interpretieren
                        data = json.loads(response)
                        sensor_status = data.get('sensor_active', False)
                        
                        return jsonify({
                            "status": "success",
                            "message": f"Verbindung zum Sensor-Arduino erfolgreich hergestellt (Seriell: {serial_port} @ {baudrate})",
                            "sensor_active": sensor_status
                        })
                    except json.JSONDecodeError:
                        # Wenn es kein JSON ist, versuchen wir, einfachen Text zu interpretieren
                        if 'active' in response.lower():
                            sensor_status = True
                        elif 'inactive' in response.lower():
                            sensor_status = False
                            
                        if sensor_status is not None:
                            return jsonify({
                                "status": "success",
                                "message": f"Verbindung zum Sensor-Arduino erfolgreich hergestellt (Seriell: {serial_port} @ {baudrate})",
                                "sensor_active": sensor_status
                            })
                        else:
                            return jsonify({
                                "status": "warning",
                                "message": f"Antwort vom Arduino erhalten, aber Status unklar: {response}"
                            })
                else:
                    return jsonify({
                        "status": "error",
                        "message": f"Keine Antwort vom Arduino erhalten (Seriell: {serial_port} @ {baudrate})"
                    })
                    
            except serial.SerialException as e:
                return jsonify({
                    "status": "error",
                    "message": f"Fehler bei der seriellen Verbindung: {str(e)}"
                })
        
        # Fallback, wenn kein Status ermittelt werden konnte
        return jsonify({
            "status": "error",
            "message": "Sensor-Status konnte nicht ermittelt werden"
        })
        
    except Exception as e:
        logger.error(f"Allgemeiner Fehler beim Testen des Sensors: {e}")
        return jsonify({
            "status": "error",
            "message": f"Allgemeiner Fehler: {str(e)}"
        }), 500
