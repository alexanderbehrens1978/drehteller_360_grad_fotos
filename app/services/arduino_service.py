import serial
import time
from app.services.config_manager import config_manager

def init_arduino():
    """
    Initialisiert die Arduino-Verbindung
    Wird nur für persistente Verbindungen verwendet, nicht für die aktuelle Implementierung
    """
    # Simulator-Modus prüfen
    if config_manager.get('simulator.enabled', True):
        print("Simulator-Modus aktiv, keine Arduino-Verbindung erforderlich")
        return None
    
    try:
        # Arduino-Port aus Konfiguration holen
        port = config_manager.get('arduino.port', '/dev/ttyACM0')
        baudrate = config_manager.get('arduino.baudrate', 9600)
        
        # Neue Verbindung öffnen
        arduino = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)  # Warten auf Arduino Reset
        
        print(f"Arduino-Verbindung hergestellt: {port} ({baudrate} Baud)")
        return arduino
    except Exception as e:
        print(f"Fehler beim Initialisieren der Arduino-Verbindung: {e}")
        return None

def rotate_teller(degrees):
    """
    Rotiert den Drehteller um die angegebenen Grad.
    Verwendet die sichere Methode, die nachweislich funktioniert.
    """
    # Wenn Simulator-Modus aktiv ist
    if config_manager.get('simulator.enabled', True):
        print(f"Simulator: Rotation um {degrees} Grad")
        return True
        
    try:
        # Arduino-Port aus Konfiguration holen oder Standardwert verwenden
        port = config_manager.get('arduino.port', '/dev/ttyACM0')
        baudrate = config_manager.get('arduino.baudrate', 9600)
        
        # Neue Verbindung mit genau dem funktionierenden Muster
        print(f"Öffne Arduino-Verbindung: {port}")
        arduino = serial.Serial(port, baudrate, timeout=1)
        time.sleep(5)  # WICHTIG: 5 Sekunden warten für die Initialisierung
        
        # Befehl zum Einschalten senden
        print("Sende '1' (Relais ein)")
        arduino.write(b'1')
        
        # Berechnete Zeit für die Drehung warten
        rotation_time = abs(degrees) / 0.8  # 0.8° pro Sekunde
        print(f"Warte auf Rotation ({rotation_time} Sekunden)")
        time.sleep(rotation_time)
        
        # Befehl zum Ausschalten senden
        print("Sende '0' (Relais aus)")
        arduino.write(b'0')
        time.sleep(0.5)
        
        # Verbindung schließen
        arduino.close()
        
        print(f"Drehteller um {degrees} Grad gedreht.")
        return True
    except Exception as e:
        print(f"Fehler beim Drehen des Tellers: {e}")
        # Versuchen, die Verbindung zu schließen, falls sie noch offen ist
        try:
            if 'arduino' in locals() and arduino.is_open:
                arduino.close()
        except:
            pass
        return False
