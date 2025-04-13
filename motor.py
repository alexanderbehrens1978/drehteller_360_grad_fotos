#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kommandozeilen-Tool zur Steuerung eines einfachen Motors.
Verwendung:
    - motor.py start  - Schaltet den Motor ein
    - motor.py stop   - Schaltet den Motor aus
    - motor.py status - Zeigt den Status an
"""

import sys
import time
import logging
from motor_control import motor_controller
from device_detector import device_detector

# Logger konfigurieren
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("drehteller360.motor_cli")

def print_usage():
    """Zeigt die Verwendungshinweise an."""
    print("""
Motor-Steuerung
--------------
Verwendung:
    motor.py start    - Schaltet den Motor ein
    motor.py stop     - Schaltet den Motor aus
    motor.py status   - Zeigt den aktuellen Status an
    motor.py help     - Zeigt diese Hilfe an
    """)

def main():
    """Hauptfunktion des Skripts."""
    # Sicherstellen, dass der Device Detector läuft
    if not device_detector.running:
        device_detector.scan_devices()  # Einmaligen Scan durchführen
    
    # Befehlszeilenargumente verarbeiten
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help":
        print_usage()
    
    elif command == "start":
        if motor_controller.start_motor():
            print("Motor eingeschaltet")
        else:
            print("Fehler beim Einschalten des Motors")
    
    elif command == "stop":
        if motor_controller.stop_motor():
            print("Motor ausgeschaltet")
        else:
            print("Fehler beim Ausschalten des Motors")
    
    elif command == "status":
        if motor_controller.is_running():
            print("Motor ist eingeschaltet")
        else:
            print("Motor ist ausgeschaltet")
            
            # Geräte-Status prüfen
            devices = device_detector.get_devices()
            if not devices['arduinos']:
                print("WARNUNG: Kein Arduino gefunden!")
            else:
                print(f"Arduino verfügbar an: {devices['arduinos'][0]['port']}")
    
    else:
        print(f"Unbekannter Befehl: {command}")
        print_usage()

if __name__ == "__main__":
    main()
