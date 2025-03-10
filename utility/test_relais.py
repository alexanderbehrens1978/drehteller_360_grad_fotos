import serial
import time

try:
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    time.sleep(5)  # Wartezeit für die Initialisierung
    print("Arduino verbunden!")
    arduino.write(b'1')  # Relais einschalten
    time.sleep(5)
    arduino.write(b'0')  # Relais ausschalten
except Exception as e:
    print(f"Fehler: {e}")
