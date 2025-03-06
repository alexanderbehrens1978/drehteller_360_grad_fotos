import os
import subprocess
import time
import shutil
import re
import tempfile
from app.services.config_manager import config_manager

def take_photo(filename=None):
    """
    Nimmt ein Foto auf und gibt den Dateinamen zurück
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
            timestamp = int(time.time())
            filename = f"photo_{timestamp}.jpg"
        
        # Vollständiger Ausgabepfad
        output_path = os.path.join(photo_dir, filename)
        
        # Kamera-Einstellungen aus Konfiguration holen
        camera_type = config_manager.get('camera.type', 'webcam')
        camera_device = config_manager.get('camera.device_path', '/dev/video0')
        
        # Je nach Kameratyp unterschiedliche Aufnahmemethode
        if camera_type == 'gphoto2':
            print(f"Versuche, Foto mit gphoto2 aufzunehmen in: {output_path}")
            
            # Methode 1: Direktes Aufnehmen und Herunterladen in ein temporäres Verzeichnis
            # um Konflikte zu vermeiden
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, f"temp_{int(time.time())}.jpg")
            
            cmd = [
                'gphoto2',
                '--force-overwrite',
                '--capture-image-and-download',
                '--filename', temp_file
            ]
            
            # Führe den Befehl noninteraktiv aus 
            try:
                # Setze stdin auf subprocess.DEVNULL, um interaktive Abfragen zu verhindern
                result = subprocess.run(
                    cmd,
                    timeout=30,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    stdin=subprocess.DEVNULL  # Verhindert interaktive Abfragen
                )
                
                print("gphoto2 Befehl abgeschlossen")
                print(f"Ausgabe: {result.stdout}")
                
                if result.stderr:
                    print(f"Fehler: {result.stderr}")
                
                # Prüfen, ob die temporäre Datei existiert
                found_files = []
                if os.path.exists(temp_dir):
                    found_files = os.listdir(temp_dir)
                    
                if found_files:
                    print(f"Gefundene Dateien im Temp-Verzeichnis: {found_files}")
                    # Kopiere die erste Datei (normalerweise die JPG)
                    for file in found_files:
                        if file.lower().endswith('.jpg'):
                            source_file = os.path.join(temp_dir, file)
                            # Kopiere die Datei an den Zielort
                            shutil.copy2(source_file, output_path)
                            print(f"Datei kopiert: {source_file} -> {output_path}")
                            break
                
                # Bereinige das temporäre Verzeichnis
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                # Prüfe, ob die Zieldatei existiert
                if not os.path.exists(output_path):
                    # Fallback-Methode: Aufnahme direkt ins Ausgabeverzeichnis
                    print("Temporäre Datei nicht gefunden, versuche direktes Speichern...")
                    
                    # Versuche mit einem zusätzlichen Wrapper-Skript
                    wrapper_script = """#!/bin/bash
echo yes | gphoto2 --force-overwrite --capture-image-and-download --filename "$1"
"""
                    script_path = '/tmp/gphoto2_wrapper.sh'
                    with open(script_path, 'w') as f:
                        f.write(wrapper_script)
                    os.chmod(script_path, 0o755)
                    
                    # Führe das Wrapper-Skript aus
                    subprocess.run([script_path, output_path], timeout=30)
                
                if not os.path.exists(output_path):
                    raise Exception("Konnte kein Foto aufnehmen und speichern")
                
            except subprocess.TimeoutExpired:
                print("Timeout bei gphoto2 - Kamera reagiert nicht")
                
                # Bereinige gphoto2-Prozesse
                subprocess.run(['pkill', '-f', 'gphoto2'], 
                              stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE)
                
                raise Exception("Timeout beim Fotografieren")
            
        else:
            # Webcam mit OpenCV
            print(f"Versuche, Foto mit OpenCV aufzunehmen: {camera_device}")
            try:
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
                    raise Exception(f"Fehler beim Auslesen der Kamera: {camera_device}")
                    
                # Foto speichern
                cv2.imwrite(output_path, frame)
                cap.release()
            except ImportError:
                print("OpenCV nicht installiert, verwende fswebcam als Fallback")
                
                # Fallback zu fswebcam, wenn OpenCV nicht verfügbar ist
                try:
                    subprocess.run([
                        'fswebcam',
                        '--no-banner',
                        '--resolution', f"{width}x{height}",
                        '-d', camera_device,
                        output_path
                    ], check=True)
                except subprocess.CalledProcessError as e:
                    raise Exception(f"Fehler bei fswebcam: {e}")
                
        print(f"Foto aufgenommen und gespeichert als: {filename}")
        
        # Ausgabe ist der relative Pfad
        return filename
    except Exception as e:
        print(f"Fehler beim Aufnehmen des Fotos: {e}")
        import traceback
        traceback.print_exc()
        return None
