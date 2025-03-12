#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/utils/webcam_detection_helper.py
Hilfsfunktionen zur Erkennung und zum Testen von Webcams
"""

import cv2
import os
import time
import subprocess
import warnings
import logging

# Logger einrichten
logger = logging.getLogger(__name__)

def find_working_webcam(preferred_devices=None):
    """
    Findet eine funktionierende Webcam
    
    Args:
        preferred_devices: Liste bevorzugter Geräte (optional)
        
    Returns:
        Pfad zum funktionierenden Gerät oder None
    """
    # Bevorzugte Geräte, falls nicht angegeben
    if preferred_devices is None:
        preferred_devices = ['/dev/video0', '/dev/video1']

    # Zuerst fswebcam verwenden, um die Gerätefunktionalität zu testen
    for device in preferred_devices:
        try:
            # fswebcam-Test ausführen
            result = subprocess.run([
                'fswebcam',
                '-d', device,
                '--no-banner',
                '/dev/null'  # Ausgabe verwerfen
            ], capture_output=True, text=True, timeout=3)

            # Wenn fswebcam erfolgreich ist, dieses Gerät zurückgeben
            if result.returncode == 0:
                logger.info(f"Funktionierende Webcam gefunden (fswebcam): {device}")
                return device
        except subprocess.TimeoutExpired:
            logger.debug(f"Zeitüberschreitung bei fswebcam für {device}")
            continue
        except Exception as e:
            logger.debug(f"Fehler bei fswebcam für {device}: {str(e)}")
            continue

    # Fallback auf OpenCV-Erkennung
    for device in preferred_devices:
        try:
            # OpenCV-Capture testen
            cap = cv2.VideoCapture(device)
            ret, frame = cap.read()
            if ret and frame is not None and frame.size > 0:
                cap.release()
                logger.info(f"Funktionierende Webcam gefunden (OpenCV): {device}")
                return device
            cap.release()
        except Exception as e:
            logger.debug(f"Fehler bei OpenCV für {device}: {str(e)}")
            pass

    # Umfassende Suche als letzter Ausweg
    try:
        # v4l2-ctl verwenden, um alle Videogeräte aufzulisten
        result = subprocess.run(['v4l2-ctl', '--list-devices'],
                                capture_output=True,
                                text=True)

        # Alle /dev/video*-Geräte extrahieren
        devices = [
            line.strip()
            for line in result.stdout.split('\n')
            if line.startswith('/dev/video')
        ]

        # Jedes entdeckte Gerät testen
        for device in devices:
            try:
                # Zuerst fswebcam testen
                result = subprocess.run([
                    'fswebcam',
                    '-d', device,
                    '--no-banner',
                    '/dev/null'
                ], capture_output=True, text=True, timeout=3)

                if result.returncode == 0:
                    logger.info(f"Funktionierende Webcam gefunden (umfassende Suche): {device}")
                    return device

                # Alternativ OpenCV testen
                cap = cv2.VideoCapture(device)
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    cap.release()
                    logger.info(f"Funktionierende Webcam gefunden (umfassende Suche): {device}")
                    return device
                cap.release()
            except Exception:
                continue
    except Exception as e:
        logger.error(f"Fehler bei der umfassenden Webcam-Suche: {str(e)}")

    logger.warning("Keine funktionierende Webcam gefunden")
    return None


def get_camera_capabilities(device_path):
    """
    Ruft die Fähigkeiten einer Kamera ab
    
    Args:
        device_path: Pfad zum Kameragerät
        
    Returns:
        Dictionary mit den Fähigkeiten der Kamera
    """
    capabilities = {
        'supported_resolutions': [],
        'max_width': 0,
        'max_height': 0
    }

    try:
        # v4l2-ctl verwenden, um detaillierte Geräteinformationen zu erhalten
        result = subprocess.run([
            'v4l2-ctl',
            '-d', device_path,
            '--list-formats-ext'
        ], capture_output=True, text=True, timeout=3)

        # Ausgabe parsen, um Auflösungen zu extrahieren
        resolutions = []
        for line in result.stdout.split('\n'):
            if 'Size' in line:
                try:
                    # Auflösung wie '640x480' extrahieren
                    resolution = line.split(':')[-1].strip()
                    width, height = map(int, resolution.split('x'))
                    resolutions.append((width, height))

                    # Maximale Auflösung aktualisieren
                    capabilities['max_width'] = max(capabilities['max_width'], width)
                    capabilities['max_height'] = max(capabilities['max_height'], height)
                except Exception as e:
                    logger.debug(f"Fehler beim Parsen der Auflösung: {str(e)}")
                    pass

        capabilities['supported_resolutions'] = sorted(set(resolutions))
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Kamera-Fähigkeiten: {str(e)}")

    return capabilities


def test_webcam_capture(device_path, width=None, height=None):
    """
    Versucht, ein Bild vom angegebenen Gerät aufzunehmen
    
    Args:
        device_path: Pfad zum Kameragerät
        width: Gewünschte Breite (optional)
        height: Gewünschte Höhe (optional)
        
    Returns:
        Tupel (Erfolg, Pfad zum aufgenommenen Bild)
    """
    try:
        # Ausgabeverzeichnis sicherstellen
        os.makedirs('static/photos', exist_ok=True)

        # Eindeutigen Dateinamen generieren
        filename = f'webcam_test_{int(time.time())}.jpg'
        full_path = os.path.join('static/photos', filename)

        # fswebcam-Befehl vorbereiten
        cmd = ['fswebcam',
               '-d', device_path,
               '--no-banner']

        # Auflösung hinzufügen, falls angegeben
        if width and height:
            cmd.extend(['-r', f'{width}x{height}'])

        cmd.append(full_path)

        # Zuerst fswebcam versuchen
        subprocess.run(cmd, check=True, timeout=5)

        # Prüfen, ob die Datei erstellt wurde
        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            logger.info(f"Testbild mit fswebcam aufgenommen: {full_path}")
            return True, full_path

        # Fallback auf OpenCV mit Auflösung
        cap = cv2.VideoCapture(device_path)

        # Auflösung einstellen, falls angegeben
        if width and height:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        ret, frame = cap.read()
        cap.release()
        
        if ret:
            cv2.imwrite(full_path, frame)
            logger.info(f"Testbild mit OpenCV aufgenommen: {full_path}")
            return True, full_path

        logger.warning(f"Konnte kein Bild von {device_path} aufnehmen")
        return False, None

    except subprocess.TimeoutExpired:
        logger.error(f"Zeitüberschreitung bei der Aufnahme von {device_path}")
        return False, None
    except Exception as e:
        logger.error(f"Fehler bei der Webcam-Aufnahme: {str(e)}")
        return False, None


# Standalone-Verwendungsbeispiel
if __name__ == '__main__':
    # Logger konfigurieren
    logging.basicConfig(level=logging.DEBUG)
    
    # Funktionierende Webcam finden
    working_device = find_working_webcam()

    if working_device:
        print(f"Funktionierende Webcam gefunden: {working_device}")

        # Kamera-Fähigkeiten abrufen
        capabilities = get_camera_capabilities(working_device)
        print("\nKamera-Fähigkeiten:")
        print(f"Unterstützte Auflösungen: {capabilities['supported_resolutions']}")
        print(f"Maximale Auflösung: {capabilities['max_width']}x{capabilities['max_height']}")

        # Testbild aufnehmen
        success, image_path = test_webcam_capture(working_device, 1280, 720)

        if success:
            print(f"\nTestbild aufgenommen: {image_path}")
        else:
            print("\nFehler beim Aufnehmen des Testbilds")
    else:
        print("Keine funktionierende Webcam gefunden")
