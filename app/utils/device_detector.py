"""
Device Detector - Verbesserte Erkennung für Arduino und Kameras
"""

import os
import subprocess
from serial.tools import list_ports

class DeviceDetector:
    """Klasse zur Erkennung von Geräten (Arduino, Webcams, Kameras)"""
    
    def __init__(self):
        self.devices = {
            'arduino': [],
            'webcam': [],
            'gphoto2': []
        }
    
    def find_arduino_devices(self):
        """Erkennt angeschlossene Arduino-Geräte"""
        arduino_devices = []
        
        # Methode 1: Serial Tools
        for port in list_ports.comports():
            desc = port.description.lower()
            device = port.device
            
            # Weitreichendere Kriterien für Arduino-Erkennung
            if ("arduino" in desc or 
                "acm" in device.lower() or 
                "usb" in desc.lower() and "serial" in desc.lower()):
                
                arduino_devices.append({
                    'port': device,
                    'description': port.description,
                    'hwid': port.hwid
                })
        
        # Methode 2: Direktes Prüfen von typischen Arduino-Ports
        for i in range(10):
            potential_port = f"/dev/ttyACM{i}"
            if potential_port not in [d['port'] for d in arduino_devices] and os.path.exists(potential_port):
                arduino_devices.append({
                    'port': potential_port,
                    'description': f"Potential Arduino on {potential_port}",
                    'hwid': 'unknown'
                })
            
            potential_port = f"/dev/ttyUSB{i}"
            if potential_port not in [d['port'] for d in arduino_devices] and os.path.exists(potential_port):
                arduino_devices.append({
                    'port': potential_port,
                    'description': f"Potential Arduino on {potential_port}",
                    'hwid': 'unknown'
                })
        
        self.devices['arduino'] = arduino_devices
        return arduino_devices
    
    def find_webcam_devices(self):
        """Erkennt angeschlossene Webcams"""
        webcam_devices = []
        
        # Methode 1: Prüfen auf /dev/video* Geräte
        for i in range(10):
            video_path = f"/dev/video{i}"
            if os.path.exists(video_path):
                webcam_devices.append({
                    'device': video_path,
                    'description': f"Video device {i}"
                })
        
        # Methode 2: v4l2-ctl für detailliertere Informationen
        try:
            output = subprocess.check_output(
                ["v4l2-ctl", "--list-devices"], 
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Verarbeite Output, um Gerätename zu extrahieren
            # (vereinfachte Implementierung - kann erweitert werden)
            current_device = None
            for line in output.split('\n'):
                if ":" in line and not line.strip().startswith('/dev/'):
                    current_device = line.strip().rstrip(':')
                elif line.strip().startswith('/dev/video'):
                    device_path = line.strip()
                    # Überprüfe, ob dieses Gerät bereits erkannt wurde
                    if not any(d['device'] == device_path for d in webcam_devices):
                        webcam_devices.append({
                            'device': device_path,
                            'description': current_device if current_device else f"Camera on {device_path}"
                        })
                        
        except (subprocess.SubprocessError, FileNotFoundError):
            # Falls v4l2-ctl nicht verfügbar ist, ignorieren
            pass
        
        self.devices['webcam'] = webcam_devices
        return webcam_devices
    
    def find_gphoto2_cameras(self):
        """Erkennt angeschlossene DSLR-Kameras, die mit gphoto2 kompatibel sind"""
        gphoto2_devices = []
        
        try:
            # Prüfe, ob gphoto2 verfügbar ist
            output = subprocess.check_output(
                ["gphoto2", "--auto-detect"], 
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Verarbeite die Ausgabe, um Kameramodelle zu extrahieren
            lines = output.strip().split('\n')
            in_camera_list = False
            
            for line in lines:
                line = line.strip()
                
                # Überspringe Header-Zeilen
                if "Model" in line and "Port" in line:
                    in_camera_list = True
                    continue
                
                if in_camera_list and line and "|" not in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        # Extrahiere Modell und Port
                        port = parts[-1]
                        model = " ".join(parts[:-1])
                        
                        gphoto2_devices.append({
                            'model': model,
                            'port': port
                        })
        
        except (subprocess.SubprocessError, FileNotFoundError):
            # Falls gphoto2 nicht verfügbar ist, ignorieren
            pass
        
        self.devices['gphoto2'] = gphoto2_devices
        return gphoto2_devices
    
    def get_devices(self):
        """Gibt alle erkannten Geräte zurück"""
        # Aktualisiere die Geräteliste
        self.find_arduino_devices()
        self.find_webcam_devices()
        self.find_gphoto2_cameras()
        
        return self.devices
    
    def get_available_ports(self):
        """Gibt eine Liste der verfügbaren Arduino-Ports zurück"""
        self.find_arduino_devices()
        return [device['port'] for device in self.devices['arduino']]
    
    def get_available_webcams(self):
        """Gibt eine Liste der verfügbaren Webcams zurück"""
        self.find_webcam_devices()
        return [device['device'] for device in self.devices['webcam']]
    
    def get_available_cameras(self):
        """Gibt eine Liste der verfügbaren DSLR-Kameras zurück"""
        self.find_gphoto2_cameras()
        return [device['model'] for device in self.devices['gphoto2']]

# Instanz erstellen
device_detector = DeviceDetector()
