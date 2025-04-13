#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hall-Sensor basierte Motorsteuerung
Steuert den Drehteller-Motor basierend auf Hall-Sensor-Signalen.
Der Hall-Sensor ist auf einem separaten Arduino angeschlossen.
"""

import sys
import time
import logging
import serial
import traceback  # Für detaillierte Fehlerprotokolle
import os

# Prüfen, ob wir im /d360/dev Verzeichnis sind
if os.path.basename(os.getcwd()) != 'dev':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

# Logger konfigurieren
logging.basicConfig(level=logging.DEBUG,  # Auf DEBUG-Level für mehr Details
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Ausgabe auf die Konsole
                    ])
logger = logging.getLogger("drehteller360.hall_motor_controller")

class HallMotorController:
    """Controller für die Steuerung eines Motors basierend auf Hall-Sensor-Signalen"""
    
    def __init__(self, motor_port=None, hall_port="/dev/ttyACM1", baudrate=9600):
        """
        Initialisiert den Hall-Motor-Controller.
        
        Args:
            motor_port: Serieller Port für den Motor-Arduino (wenn None, wird automatisch erkannt)
            hall_port: Serieller Port für den Hall-Sensor-Arduino
            baudrate: Baudrate für die serielle Kommunikation
        """
        try:
            # Versuche, den ArduinoController zu importieren
            # Variante 1: Direkt (wenn im sys.path)
            try:
                from app.controllers.arduino_controller import ArduinoController
                self.arduino_controller_class = ArduinoController
                logger.info("ArduinoController aus app.controllers importiert")
            except ImportError:
                # Variante 2: Relativer Import (wenn wir im /d360/dev Verzeichnis sind)
                try:
                    sys.path.append(os.getcwd())
                    from app.controllers.arduino_controller import ArduinoController
                    self.arduino_controller_class = ArduinoController
                    logger.info("ArduinoController nach Pfadanpassung importiert")
                except ImportError:
                    logger.warning("ArduinoController konnte nicht importiert werden - direkter Serieller Zugriff wird verwendet")
                    self.arduino_controller_class = None
        except Exception as e:
            logger.error(f"Fehler beim Import von ArduinoController: {e}")
            logger.error(traceback.format_exc())
            self.arduino_controller_class = None
        
        # Motor-Controller initialisieren
        self.motor_port = motor_port
        self.motor_arduino = None
        if self.arduino_controller_class and self.motor_port:
            try:
                self.motor_arduino = self.arduino_controller_class(port=self.motor_port)
                logger.info(f"Motor-Arduino auf Port {self.motor_port} initialisiert")
            except Exception as e:
                logger.error(f"Fehler beim Initialisieren des Motor-Arduino: {e}")
                logger.error(traceback.format_exc())
        
        # Hall-Sensor-Einstellungen
        self.hall_port = hall_port
        self.hall_serial = None
        self.baudrate = baudrate
        self.is_running = False
        
        logger.info(f"HallMotorController initialisiert: hall_port={hall_port}, motor_port={motor_port}")
    
    def connect_hall_sensor(self):
        """Verbindet mit dem Arduino des Hall-Sensors."""
        try:
            logger.info(f"Versuche Verbindung zum Hall-Sensor auf Port {self.hall_port}")
            self.hall_serial = serial.Serial(self.hall_port, self.baudrate, timeout=1)
            time.sleep(2)  # Warten auf Arduino-Reset nach Verbindungsaufbau
            logger.info(f"Verbindung zum Hall-Sensor-Arduino hergestellt: {self.hall_port}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Verbinden mit Hall-Sensor-Arduino: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def check_hall_signal(self, timeout=5):
        """
        Überprüft, ob ein Hall-Sensor-Signal empfangen wird.
        
        Args:
            timeout: Timeout in Sekunden
            
        Returns:
            True, wenn ein niedriger Sensorwert empfangen wird (<30), sonst False
        """
        if not self.hall_serial:
            if not self.connect_hall_sensor():
                logger.error("Kann Hall-Sensor nicht überprüfen: Keine Verbindung")
                return False
        
        # Hall-Sensor-Arduino zurücksetzen, um sicherzustellen, dass neue Daten gesendet werden
        try:
            self.hall_serial.setDTR(False)
            time.sleep(0.1)
            self.hall_serial.setDTR(True)
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Konnte DTR nicht setzen: {e}")
        
        logger.info("Überprüfe Hall-Sensor-Signal...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if self.hall_serial.in_waiting > 0:
                    line = self.hall_serial.readline().decode('utf-8', errors='replace').strip()
                    logger.debug(f"Empfangene Daten: {line}")
                    
                    # Versuchen, den Sensorwert zu extrahieren
                    # Erwartet ein Format wie "Hall sensor value: 25"
                    try:
                        if ":" in line:
                            value = int(line.split(":")[-1].strip())
                            logger.info(f"Hall-Sensor-Wert: {value}")
                            return value < 30  # True, wenn unter dem Schwellwert
                    except ValueError:
                        pass
            except Exception as e:
                logger.error(f"Fehler beim Lesen der Hall-Sensor-Daten: {e}")
                return False
            
            time.sleep(0.1)
            
        logger.warning(f"Timeout: Kein Hall-Sensor-Signal innerhalb von {timeout} Sekunden empfangen")
        return False
    
    def turn_motor_on(self):
        """Schaltet den Motor ein."""
        if self.motor_arduino:
            try:
                logger.info("Versuche Motor über ArduinoController einzuschalten")
                result = self.motor_arduino.turn_motor_on()
                logger.info(f"Motor eingeschaltet: {result}")
                return result
            except Exception as e:
                logger.error(f"Fehler beim Einschalten des Motors über ArduinoController: {e}")
                logger.error(traceback.format_exc())
                return False
        else:
            logger.error("Kein Motor-Arduino-Controller verfügbar")
            return False
    
    def turn_motor_off(self):
        """Schaltet den Motor aus."""
        if self.motor_arduino:
            try:
                logger.info("Versuche Motor über ArduinoController auszuschalten")
                result = self.motor_arduino.turn_motor_off()
                logger.info(f"Motor ausgeschaltet: {result}")
                return result
            except Exception as e:
                logger.error(f"Fehler beim Ausschalten des Motors über ArduinoController: {e}")
                logger.error(traceback.format_exc())
                return False
        else:
            logger.error("Kein Motor-Arduino-Controller verfügbar")
            return False
    
    def wait_for_hall_signal(self, state, timeout=30):
        """
        Wartet auf ein spezifisches Hall-Sensor-Signal.
        
        Args:
            state: True für niedrigen Wert (<30), False für hohen Wert (>=30)
            timeout: Timeout in Sekunden
            
        Returns:
            True, wenn das gewünschte Signal empfangen wurde, sonst False
        """
        logger.info(f"Warte auf {'niedrigen' if state else 'hohen'} Hall-Sensor-Wert...")
        start_time = time.time()
        
        # Warten auf mehrere konsistente Messungen, um falsche Signale zu vermeiden
        consecutive_readings = 0
        required_consecutive_readings = 2
        
        while time.time() - start_time < timeout:
            try:
                if self.hall_serial.in_waiting > 0:
                    line = self.hall_serial.readline().decode('utf-8', errors='replace').strip()
                    logger.debug(f"Empfangene Daten (wait): {line}")
                    
                    try:
                        if ":" in line:
                            value = int(line.split(":")[-1].strip())
                            signal_state = value < 30
                            logger.debug(f"Hall-Wert: {value}, Status: {'niedrig' if signal_state else 'hoch'}")
                            
                            if signal_state == state:
                                consecutive_readings += 1
                                logger.debug(f"Konsistente Lesung #{consecutive_readings}/{required_consecutive_readings}")
                                
                                if consecutive_readings >= required_consecutive_readings:
                                    logger.info(f"Gewünschtes Hall-Sensor-Signal empfangen: {value} (nach {consecutive_readings} Lesungen)")
                                    return True
                            else:
                                consecutive_readings = 0
                    except ValueError as ve:
                        logger.warning(f"Konnte Wert nicht konvertieren: {line} - {ve}")
                        consecutive_readings = 0
                        pass
            except Exception as e:
                logger.error(f"Fehler beim Lesen der Hall-Sensor-Daten: {e}")
                logger.error(traceback.format_exc())
                return False
            
            time.sleep(0.1)
            
        logger.warning(f"Timeout: Gewünschtes Hall-Sensor-Signal nicht innerhalb von {timeout} Sekunden empfangen")
        return False
    
    def rotate_to_next_signal(self):
        """
        Dreht den Motor bis zum nächsten Hall-Sensor-Signal.
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self.hall_serial:
            if not self.connect_hall_sensor():
                logger.error("Kann Hall-Sensor nicht überwachen: Keine Verbindung")
                return False
            
        # KOMPLETT VEREINFACHTER ANSATZ
        # 1. Leere alle Puffer
        self.hall_serial.reset_input_buffer()
        self.hall_serial.reset_output_buffer()
        
        # 2. Aktuelle Position bestimmen - befinden wir uns auf einem Magneten?
        logger.info("Prüfe, ob wir uns aktuell auf einem Magneten befinden...")
        # Mehrere Messungen durchführen
        magnet_readings = []
        for _ in range(5):
            time.sleep(0.2)  # Kurze Verzögerung zwischen Messungen
            while self.hall_serial.in_waiting > 0:
                try:
                    line = self.hall_serial.readline().decode('utf-8', errors='replace').strip()
                    if "Hall sensor value:" in line:
                        value = int(line.split(":")[-1].strip())
                        magnet_readings.append(value)
                        logger.debug(f"Hall-Sensor-Wert: {value}")
                except:
                    pass
        
        # Wenn Messungen vorhanden, Durchschnitt berechnen
        on_magnet = False
        if magnet_readings:
            avg_value = sum(magnet_readings) / len(magnet_readings)
            on_magnet = avg_value < 30
            logger.info(f"Durchschnittlicher Hall-Sensor-Wert: {avg_value:.1f} - {'Auf Magnet' if on_magnet else 'Kein Magnet'}")
        
        # 3. Falls wir auf einem Magneten sind, drehen wir bis wir weg sind
        if on_magnet:
            logger.info("Wir befinden uns auf einem Magneten. Drehe weg...")
            if not self.turn_motor_on():
                logger.error("Fehler beim Starten des Motors")
                return False
            
            # Warte auf Mindestdrehung (feste Zeit)
            time.sleep(2)
            
            # Prüfe erneut (sollten jetzt weg sein)
            self.hall_serial.reset_input_buffer()
            time.sleep(0.5)
            
            away_from_magnet = False
            for _ in range(3):
                while self.hall_serial.in_waiting > 0:
                    try:
                        line = self.hall_serial.readline().decode('utf-8', errors='replace').strip()
                        if "Hall sensor value:" in line:
                            value = int(line.split(":")[-1].strip())
                            away_from_magnet = value >= 30
                            if away_from_magnet:
                                logger.info(f"Erfolgreich vom Magneten weggedreht. Wert: {value}")
                                break
                    except:
                        pass
                if away_from_magnet:
                    break
                time.sleep(0.2)
            
            if not away_from_magnet:
                logger.warning("Konnte nicht vom Magneten wegdrehen - setze trotzdem fort")
        
        # 4. Puffer leeren und Motor starten
        self.hall_serial.reset_input_buffer()
        time.sleep(0.2)
        
        logger.info("Starte Motor und warte auf den nächsten Magneten...")
        if not self.turn_motor_on():
            logger.error("Fehler beim Starten des Motors")
            return False
        
        self.is_running = True
        
        # 5. Initialen Teil der Drehung überspringen (feste Zeit)
        logger.info("Verzögerung für initiale Drehung...")
        time.sleep(2.0)  # Feste Anfangsverzögerung
        
        # 6. Puffer leeren und auf Magneten warten
        self.hall_serial.reset_input_buffer()
        time.sleep(0.2)
        
        logger.info("Warte auf den nächsten Magneten...")
        start_time = time.time()
        magnet_detected = False
        
        try:
            # 7. Einfache Schleife mit festen Verzögerungen
            while time.time() - start_time < 30:  # Timeout nach 30 Sekunden
                # Lese alle verfügbaren Daten
                while self.hall_serial.in_waiting > 0:
                    try:
                        line = self.hall_serial.readline().decode('utf-8', errors='replace').strip()
                        if "Hall sensor value:" in line:
                            value = int(line.split(":")[-1].strip())
                            logger.debug(f"Hall-Wert: {value}")
                            
                            # Wenn ein niedriger Wert erkannt wird = Magnet
                            if value < 30:
                                logger.info(f"Magnet erkannt! Wert: {value}")
                                # Sofort stoppen!
                                if not self.turn_motor_off():
                                    logger.error("Fehler beim Stoppen des Motors")
                                    return False
                                
                                self.is_running = False
                                
                                # Kurz warten und überprüfen, ob wir wirklich auf einem Magneten sind
                                time.sleep(0.1)  # 100ms statt 500ms
                                
                                # Sofort nach Stoppen 10 Messungen durchführen
                                confirm_readings = []
                                for _ in range(10):  # Mehr Messungen (10 statt 3)
                                    # Den Puffer sofort leeren, um immer die aktuellsten Werte zu bekommen
                                    while self.hall_serial.in_waiting > 0:
                                        try:
                                            confirm_line = self.hall_serial.readline().decode('utf-8', errors='replace').strip()
                                            if "Hall sensor value:" in confirm_line:
                                                confirm_value = int(confirm_line.split(":")[-1].strip())
                                                confirm_readings.append(confirm_value)
                                                # Wenn wir mehrere niedrige Werte in Folge erhalten, sind wir auf dem Magneten
                                                if confirm_value < 30:
                                                    logger.info(f"Niedrige Bestätigungsmessung: {confirm_value} - auf Magnet bestätigt!")
                                        except:
                                            pass
                                    # Kürzere Wartezeit zwischen Messungen
                                    time.sleep(0.02)
                                
                                # Erfolg, wenn mindestens eine Messung unter 30 ist
                                if any(v < 30 for v in confirm_readings):
                                    logger.info(f"Erfolgreiche Positionierung bestätigt! Werte: {confirm_readings}")
                                    magnet_detected = True
                                    return True
                                
                                # Überprüfe die Bestätigungsmessungen
                                if confirm_readings:
                                    avg_confirm = sum(confirm_readings) / len(confirm_readings)
                                    logger.info(f"Bestätigungsmessung nach Stopp: {avg_confirm:.1f}")
                                    logger.warning("Motor gestoppt, aber Magnet nicht mehr erkannt. Setze fort...")
                                    if not self.turn_motor_on():
                                        logger.error("Fehler beim Neustarten des Motors")
                                        return False
                                    self.is_running = True
                                else:
                                    logger.warning("Keine Bestätigungsmessungen erhalten. Setze fort...")
                                    if not self.turn_motor_on():
                                        logger.error("Fehler beim Neustarten des Motors")
                                        return False
                                    self.is_running = True
                    except Exception as e:
                        logger.error(f"Fehler beim Lesen der Hall-Sensor-Daten: {e}")
                        logger.error(traceback.format_exc())
                
                time.sleep(0.05)  # Kurze Verzögerung in der Schleife
            
            # Timeout - kein Magnet gefunden
            logger.error("Timeout: Kein Magnet innerhalb von 30 Sekunden erkannt")
            if self.is_running:
                self.turn_motor_off()
                self.is_running = False
            return False
            
        except Exception as e:
            logger.error(f"Fehler während der Rotation: {e}")
            logger.error(traceback.format_exc())
            # Sicherstellen, dass der Motor gestoppt wird
            if self.is_running:
                try:
                    self.turn_motor_off()
                except:
                    pass
                self.is_running = False
            return False

def main():
    """Hauptfunktion des Skripts."""
    try:
        # Kommandozeilen-Argumente verarbeiten
        if len(sys.argv) > 1 and sys.argv[1].lower() == "check":
            # Nur Hall-Sensor überprüfen
            controller = HallMotorController()
            if controller.connect_hall_sensor():
                signal = controller.check_hall_signal(timeout=10)
                print(f"Hall-Sensor-Signal: {'Niedrig (Magnet erkannt)' if signal else 'Hoch (kein Magnet)'}")
            else:
                print("Verbindung zum Hall-Sensor-Arduino konnte nicht hergestellt werden.")
        elif len(sys.argv) > 1 and sys.argv[1].lower() == "motor":
            # Nur Motorsteuerung testen
            motor_port = "/dev/ttyACM0"  # Standard Motor-Arduino-Port
            if len(sys.argv) > 2:
                motor_port = sys.argv[2]
            
            print(f"Teste Motorsteuerung auf Port {motor_port}...")
            controller = HallMotorController(motor_port=motor_port)
            
            print("Schalte Motor für 2 Sekunden ein...")
            if controller.turn_motor_on():
                time.sleep(2)
                print("Schalte Motor aus...")
                controller.turn_motor_off()
                print("Motortest abgeschlossen")
            else:
                print("Fehler beim Einschalten des Motors")
        else:
            # Volle Rotation zum nächsten Signal
            print("Drehe zum nächsten Hall-Sensor-Signal...")
            
            # Motor-Arduino konfigurieren
            motor_port = "/dev/ttyACM0"  # Standard Motor-Arduino-Port
            
            # Hall-Motor-Controller mit Motor-Arduino initialisieren
            controller = HallMotorController(motor_port=motor_port)
            success = controller.rotate_to_next_signal()
            
            if success:
                print("Erfolgreich zum nächsten Hall-Sensor-Signal gedreht.")
            else:
                print("Fehler beim Drehen zum nächsten Hall-Sensor-Signal.")
    except Exception as e:
        logger.error(f"Unerwarteter Fehler: {e}")
        logger.error(traceback.format_exc())
        print(f"Fehler: {e}")

if __name__ == "__main__":
    main()
