#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sucht nach Arduinos an USB-Ports und lädt den Hall-Sensor-Sketch hoch
"""

import os
import sys
import subprocess
import time
import serial.tools.list_ports
import re

# Farbcodes für Terminal-Ausgabe
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Formatiert Text als Überschrift"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.ENDC}")

def print_info(text):
    """Formatiert Text als Info"""
    print(f"{Colors.BLUE}INFO: {text}{Colors.ENDC}")

def print_success(text):
    """Formatiert Text als Erfolg"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    """Formatiert Text als Warnung"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

def print_error(text):
    """Formatiert Text als Fehler"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def find_arduino_ports():
    """Findet alle angeschlossenen Arduino-Geräte"""
    print_header("Suche nach angeschlossenen Arduinos")
    
    arduino_ports = []
    
    # Alle seriellen Ports durchsuchen
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        print_warning("Keine seriellen Geräte gefunden.")
        return []
    
    print(f"Gefundene serielle Geräte: {len(ports)}")
    
    # Ausgabe aller gefundenen Geräte
    for i, port in enumerate(ports):
        is_arduino = False
        port_type = "Unbekanntes Gerät"
        
        # Prüfen, ob es sich um ein Arduino handelt
        if "Arduino" in port.description:
            is_arduino = True
            port_type = "Arduino (offiziell)"
        elif "CH340" in port.description or "ch340" in port.hwid.lower():
            is_arduino = True
            port_type = "Arduino (CH340 Chip)"
        elif "USB Serial" in port.description:
            is_arduino = True
            port_type = "Arduino (generischer USB-Serial)"
        elif "ttyACM" in port.device or "ttyUSB" in port.device:
            # Wahrscheinlich ein Arduino oder ähnliches Gerät
            is_arduino = True
            port_type = "Wahrscheinlich Arduino"
        
        # Anzeigen des Ports mit farbiger Markierung, wenn es ein Arduino ist
        if is_arduino:
            print(f"{Colors.GREEN}[{i+1}] {port.device}{Colors.ENDC} - {port.description} ({port_type})")
            arduino_ports.append((port.device, port.description, port_type))
        else:
            print(f"[{i+1}] {port.device} - {port.description} ({port_type})")
    
    return arduino_ports

def is_arduino_cli_installed():
    """Prüft, ob die Arduino CLI installiert ist"""
    try:
        result = subprocess.run(["arduino-cli", "--version"], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE, 
                               text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def install_arduino_cli():
    """Installiert die Arduino CLI"""
    print_header("Arduino CLI Installation")
    print_info("Arduino CLI wird installiert...")
    
    try:
        # Temporäres Verzeichnis erstellen
        os.makedirs("/tmp/arduino-cli", exist_ok=True)
        os.chdir("/tmp/arduino-cli")
        
        # Arduino CLI herunterladen
        subprocess.run(["curl", "-fsSL", "https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh"], 
                      stdout=subprocess.PIPE, check=True)
        
        # Installer ausführen
        subprocess.run(["sh", "install.sh"], check=True)
        
        # In PATH hinzufügen (für aktuelle Sitzung)
        bin_dir = os.path.expanduser("~/.local/bin")
        if bin_dir not in os.environ["PATH"]:
            os.environ["PATH"] += f":{bin_dir}"
        
        # Boards aktualisieren
        subprocess.run(["arduino-cli", "core", "update-index"], check=True)
        
        print_success("Arduino CLI wurde erfolgreich installiert!")
        return True
    except Exception as e:
        print_error(f"Fehler bei der Installation der Arduino CLI: {str(e)}")
        return False

def upload_to_arduino(port, sketch_dir, board="arduino:avr:uno"):
    """Lädt den Arduino-Sketch auf den angegebenen Port hoch"""
    print_header(f"Upload auf Arduino ({port})")
    
    if not os.path.exists(sketch_dir):
        print_error(f"Sketch-Verzeichnis nicht gefunden: {sketch_dir}")
        return False
    
    try:
        # Kompilieren
        print_info("Kompiliere Sketch...")
        compile_cmd = ["arduino-cli", "compile", "--fqbn", board, sketch_dir]
        compile_result = subprocess.run(compile_cmd, 
                                      stdout=subprocess.PIPE, 
                                      stderr=subprocess.PIPE, 
                                      text=True)
        
        if compile_result.returncode != 0:
            print_error(f"Fehler beim Kompilieren: {compile_result.stderr}")
            return False
        
        print_success("Kompilierung erfolgreich!")
        
        # Hochladen
        print_info("Lade Sketch hoch...")
        upload_cmd = ["arduino-cli", "upload", "-p", port, "--fqbn", board, sketch_dir]
        upload_result = subprocess.run(upload_cmd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, 
                                     text=True)
        
        if upload_result.returncode != 0:
            print_error(f"Fehler beim Hochladen: {upload_result.stderr}")
            return False
        
        print_success("Upload erfolgreich!")
        return True
    except Exception as e:
        print_error(f"Fehler: {str(e)}")
        return False

def start_serial_monitor(port, baudrate=9600):
    """Startet den seriellen Monitor für den angegebenen Port"""
    print_header(f"Serieller Monitor für {port}")
    print_info(f"Verbinde mit {port} bei {baudrate} Baud...")
    print_info("Drücke STRG+C zum Beenden")
    
    try:
        subprocess.run(["arduino-cli", "monitor", "-p", port, "-c", f"baudrate={baudrate}"])
        return True
    except KeyboardInterrupt:
        print_info("\nSerieller Monitor beendet.")
        return True
    except Exception as e:
        print_error(f"Fehler beim Starten des seriellen Monitors: {str(e)}")
        return False

def main():
    """Hauptfunktion"""
    print_header("Arduino Suche und Upload Tool")
    
    # Prüfen, ob die Arduino CLI installiert ist
    if not is_arduino_cli_installed():
        print_warning("Arduino CLI ist nicht installiert.")
        if input("Möchten Sie arduino-cli installieren? (j/n): ").lower() in ["j", "ja", "y", "yes"]:
            if not install_arduino_cli():
                print_error("Installation fehlgeschlagen. Bitte installieren Sie arduino-cli manuell.")
                return
        else:
            print_error("Arduino CLI wird benötigt. Programm wird beendet.")
            return
    
    # Pfad zur Hall-Sensor-Sketch
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sketch_dir = os.path.join(script_dir, "hall_sensor_arduino")
    
    if not os.path.exists(sketch_dir):
        print_error(f"Hall-Sensor-Sketch nicht gefunden: {sketch_dir}")
        return
    
    # Nach Arduinos suchen
    arduino_ports = find_arduino_ports()
    
    if not arduino_ports:
        print_error("Keine Arduinos gefunden. Bitte schließen Sie ein Arduino-Board an und versuchen Sie es erneut.")
        return
    
    # Arduino auswählen
    selected_port = None
    if len(arduino_ports) == 1:
        # Nur ein Arduino gefunden
        selected_port = arduino_ports[0][0]
        print_info(f"Arduino gefunden: {arduino_ports[0][1]} an {selected_port}")
    else:
        # Mehrere Arduinos gefunden, Benutzer nach Auswahl fragen
        print_info("Mehrere Arduinos gefunden. Bitte wählen Sie einen aus:")
        for i, (port, desc, port_type) in enumerate(arduino_ports):
            print(f"[{i+1}] {port} - {desc} ({port_type})")
            
        try:
            choice = int(input("Bitte geben Sie die Nummer des zu verwendenden Arduinos ein: "))
            if 1 <= choice <= len(arduino_ports):
                selected_port = arduino_ports[choice-1][0]
            else:
                print_error("Ungültige Auswahl.")
                return
        except ValueError:
            print_error("Ungültige Eingabe. Bitte geben Sie eine Zahl ein.")
            return
    
    # Sketch auf den ausgewählten Arduino hochladen
    print_info(f"Verwende Arduino an Port: {selected_port}")
    
    if upload_to_arduino(selected_port, sketch_dir):
        # Nach erfolgreicher Upload den seriellen Monitor starten
        if input("Möchten Sie den seriellen Monitor starten, um die Ausgabe des Hall-Sensors zu sehen? (j/n): ").lower() in ["j", "ja", "y", "yes"]:
            time.sleep(2)  # Kurz warten, damit der Arduino neu starten kann
            start_serial_monitor(selected_port)

if __name__ == "__main__":
    main()
