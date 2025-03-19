#!/usr/bin/env python3
# Speichern als test_config.py im Hauptverzeichnis

import os
import json
import sys

# Projektverzeichnis ermitteln
project_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(project_dir, 'config.json')

print(f"Projektverzeichnis: {project_dir}")
print(f"Konfigurationspfad: {config_path}")
print(f"Datei existiert: {os.path.exists(config_path)}")

# Wenn die Datei nicht existiert, erstellen wir sie
if not os.path.exists(config_path):
    print("Erstelle neue Konfigurationsdatei...")
    default_config = {
        'camera': {
            'device_path': '/dev/video0',
            'type': 'webcam',
            'resolution': {
                'width': 1280,
                'height': 720
            }
        },
        'arduino': {
            'port': '/dev/ttyACM0',
            'baudrate': 9600
        },
        'rotation': {
            'default_degrees': 15,
            'default_interval': 5
        }
    }
    
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(default_config, f, indent=4)
    
    print("Konfigurationsdatei erstellt.")
else:
    # Versuchen die Datei zu lesen
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print("Konfiguration erfolgreich geladen:")
        print(json.dumps(config, indent=2))
    except Exception as e:
        print(f"Fehler beim Laden der Konfiguration: {e}")
