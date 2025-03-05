#!/usr/bin/env python3
"""
Skript zur Behebung von Geräteerkennung-Problemen
"""

import os
import sys
import json
import serial
import subprocess
from serial.tools import list_ports


def find_arduino_devices():
    """Finde alle angeschlossenen Arduino-Geräte"""
    arduino_devices = []

    print("Suche nach Arduino-Geräten...")
    for port in list_ports.comports():
        desc = port.description.lower()
        device = port.device

        if ("arduino" in desc or
                "tty" in device.lower() or
                "acm" in device.lower() or
                "usb" in desc.lower()):
            arduino_devices.append({
                'port': device,
                'description': port.description
            })

    return arduino_devices


def find_webcam_devices():
    """Finde alle angeschlossenen Webcams"""
    webcam_devices = []

    print("Suche nach Webcam-Geräten...")

    # Methode 1: Überprüfe /dev/video* Geräte
    video_devices = [f"/dev/video{i}" for i in range(10) if os.path.exists(f"/dev/video{i}")]
    for device in video_devices:
        webcam_devices.append({
            'device': device,
            'description': f"Video device {device}"
        })

    # Methode 2: Versuche v4l2-ctl zu verwenden
    try:
        v4l2_output = subprocess.check_output(["v4l2-ctl", "--list-devices"],
                                              stderr=subprocess.STDOUT,
                                              universal_newlines=True)

        print("v4l2-ctl Ausgabe:")
        print(v4l2_output)

        # Verarbeite die Ausgabe
        # ... (komplexere Verarbeitung wenn nötig)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("v4l2-ctl ist nicht verfügbar oder ergab einen Fehler")

    return webcam_devices


def find_gphoto2_cameras():
    """Finde alle angeschlossenen gphoto2-kompatiblen Kameras"""
    gphoto2_devices = []

    print("Suche nach gphoto2-Kameras...")
    try:
        gphoto2_output = subprocess.check_output(["gphoto2", "--auto-detect"],
                                                 stderr=subprocess.STDOUT,
                                                 universal_newlines=True)

        print("gphoto2 Ausgabe:")
        print(gphoto2_output)

        # Verarbeite die Ausgabe, um Kameramodelle zu extrahieren
        lines = gphoto2_output.strip().split('\n')
        for line in lines:
            if "usb:" in line.lower():
                parts = line.split(',')
                if len(parts) >= 1:
                    model = parts[0].strip()
                    gphoto2_devices.append({
                        'model': model,
                        'port': 'auto'  # gphoto2 findet selbst den richtigen Port
                    })
    except (subprocess.SubprocessError, FileNotFoundError):
        print("gphoto2 ist nicht verfügbar oder ergab einen Fehler")

    return gphoto2_devices


def test_arduino_connection(port):
    """Teste die Verbindung zu einem Arduino"""
    try:
        print(f"Teste Arduino-Verbindung zu {port}...")
        ser = serial.Serial(port, 9600, timeout=2)
        time.sleep(2)  # Warten auf Arduino Reset

        # Sende Test-Befehle
        ser.write(b'1')
        time.sleep(0.5)
        ser.write(b'0')

        ser.close()
        print(f"Verbindung zu {port} erfolgreich getestet!")
        return True
    except Exception as e:
        print(f"Fehler beim Testen der Verbindung zu {port}: {e}")
        return False


def update_config_file(arduino_devices, webcam_devices, gphoto2_devices):
    """Aktualisiere die Konfigurationsdatei mit den erkannten Geräten"""
    config_path = "config.json"

    try:
        # Lade bestehende Konfiguration
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}

        # Setze Arduino-Konfiguration, wenn Geräte gefunden wurden
        if arduino_devices:
            if 'arduino' not in config:
                config['arduino'] = {}
            config['arduino']['port'] = arduino_devices[0]['port']
            config['arduino']['baudrate'] = 9600

        # Setze Kamera-Konfiguration, wenn Geräte gefunden wurden
        if 'camera' not in config:
            config['camera'] = {}

        if webcam_devices:
            config['camera']['device_path'] = webcam_devices[0]['device']
            config['camera']['type'] = 'webcam'
        elif gphoto2_devices:
            config['camera']['device_path'] = 'auto'
            config['camera']['type'] = 'gphoto2'

        # Stelle sicher, dass der Simulator deaktiviert ist, wenn Geräte gefunden wurden
        if arduino_devices or webcam_devices or gphoto2_devices:
            if 'simulator' not in config:
                config['simulator'] = {}
            config['simulator']['enabled'] = False

        # Speichere die aktualisierte Konfiguration
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)

        print(f"Konfiguration erfolgreich aktualisiert und in {config_path} gespeichert!")
        return True
    except Exception as e:
        print(f"Fehler beim Aktualisieren der Konfiguration: {e}")
        return False


def main():
    """Hauptfunktion: Suche Geräte und aktualisiere Konfiguration"""
    print("=== Drehteller 360 Geräterkennung-Reparatur ===")

    # Erkenne angeschlossene Geräte
    arduino_devices = find_arduino_devices()
    webcam_devices = find_webcam_devices()
    gphoto2_devices = find_gphoto2_cameras()

    # Zeige erkannte Geräte an
    print("\nErkannte Arduino-Geräte:")
    if arduino_devices:
        for i, device in enumerate(arduino_devices):
            print(f"{i + 1}. {device['port']} - {device['description']}")
    else:
        print("Keine Arduino-Geräte erkannt!")

    print("\nErkannte Webcams:")
    if webcam_devices:
        for i, device in enumerate(webcam_devices):
            print(f"{i + 1}. {device['device']} - {device['description']}")
    else:
        print("Keine Webcams erkannt!")

    print("\nErkannte gphoto2-Kameras:")
    if gphoto2_devices:
        for i, device in enumerate(gphoto2_devices):
            print(f"{i + 1}. {device['model']}")
    else:
        print("Keine gphoto2-Kameras erkannt!")

    # Aktualisiere die Konfigurationsdatei
    if arduino_devices or webcam_devices or gphoto2_devices:
        update_config_file(arduino_devices, webcam_devices, gphoto2_devices)
        print("\nDie Konfiguration wurde aktualisiert.")
        print("Bitte starte den Drehteller-Service neu mit:")
        print("sudo systemctl restart drehteller360.service")
    else:
        print("\nKeine Geräte erkannt. Überprüfe die Anschlüsse und Treiber.")


if __name__ == "__main__":
    main()