#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
drehteller360/hall_motor_controller.py
Controller für die Hall-Sensor-basierte Steuerung des Drehtellers
"""

import time
import serial
import logging
import traceback
from app.controllers.arduino_controller import ArduinoController
from app.utils.config_manager import config_manager

# Logger einrichten
logger = logging.getLogger(__name__)

class HallMotorController:
    """Controller für die Hall-Sensor-basierte Drehteller-Steuerung"""
    
    def __init__(self, hall_port='/dev/ttyACM1', motor_port='/dev/ttyACM0', threshold=30):
        """
        Initialisiert den Hall-Motor-Controller
        
        Args:
            hall_port: Serieller Port des Hall-Sensor-Arduino
            motor_port: Serieller Port des Motor-Arduino
            threshold: Schwellenwert für die Hall-Sensor-Erkennung
        """
        self.logger = logging.getLogger(__name__)
        self.hall_port = hall_port
        self.motor_port = motor_port
        self.threshold = threshold
        self.hall_serial = None
        self.is_running = False
        self.arduino_controller = None
        
        # Zeit für eine vollständige Umdrehung (in Millisekunden)
        self.full_rotation_time_ms = config_manager.config.get('rotation', {}).get('full_rotation_time_ms', 45000)
        
        # Arduino-Controller importieren und initialisieren
        try:
            logger.info("ArduinoController aus app.controllers importiert")
            self.arduino_controller = ArduinoController(port=motor_port, baudrate=9600)
            logger.info(f"Motor-Arduino auf Port {motor_port} initialisiert")
        except Exception as e:
            logger.error(f"Fehler beim Initialisieren des Arduino-Controllers: {e}")
            logger.error(traceback.format_exc())
            raise
            
        # Verbindung zum Hall-Sensor herstellen
        self.connect_to_hall_sensor()
        
        logger.info(f"HallMotorController initialisiert: hall_port={hall_port}, motor_port={motor_port}, full_rotation_time={self.full_rotation_time_ms}ms")
    
    def connect_to_hall_sensor(self):
        """
        Stellt eine Verbindung zum Hall-Sensor-Arduino her
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            logger.info(f"Versuche Verbindung zum Hall-Sensor auf Port {self.hall_port}")
            self.hall_serial = serial.Serial(self.hall_port, 9600, timeout=2)
            time.sleep(2)  # Warten, bis der Arduino bereit ist
            
            # Puffer leeren
            self.hall_serial.reset_input_buffer()
            self.hall_serial.reset_output_buffer()
            
            logger.info(f"Verbindung zum Hall-Sensor-Arduino hergestellt: {self.hall_port}")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Verbinden mit dem Hall-Sensor: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def turn_motor_on(self):
        """
        Schaltet den Motor ein
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            logger.info("Versuche Motor über ArduinoController einzuschalten")
            result = self.arduino_controller.turn_motor_on()
            logger.info(f"Motor eingeschaltet: {result}")
            return result
        except Exception as e:
            logger.error(f"Fehler beim Einschalten des Motors: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def turn_motor_off(self):
        """
        Schaltet den Motor aus
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            logger.info("Versuche Motor über ArduinoController auszuschalten")
            result = self.arduino_controller.turn_motor_off()
            logger.info(f"Motor ausgeschaltet: {result}")
            return result
        except Exception as e:
            logger.error(f"Fehler beim Ausschalten des Motors: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def calibrate_rotation_time(self):
        """
        Kalibriert die Zeit für eine vollständige Umdrehung.
        Dreht den Teller vom Hall-Sensor-Signal bis zum nächsten Signal und misst die Zeit.
        
        Returns:
            Die gemessene Zeit in Millisekunden bei Erfolg, None bei Fehler
        """
        try:
            if not self.hall_serial:
                logger.error("Keine Verbindung zum Hall-Sensor")
                return None
            
            # Puffer leeren
            self.hall_serial.reset_input_buffer()
            self.hall_serial.reset_output_buffer()
            
            # Zuerst zur Heimposition fahren
            if not self.move_to_home_position():
                logger.error("Fehler beim Fahren zur Heimposition")
                return None
            
            logger.info("Starte Kalibrierung der Rotationszeit...")
            logger.info("Heimposition erreicht. Starte Zeitmessung für vollständige Umdrehung.")
            
            # Start der Zeitmessung
            start_time = time.time()
            
            # Motor starten
            if not self.turn_motor_on():
                logger.error("Fehler beim Starten des Motors")
                return None
            
            self.is_running = True
            signal_detected = False
            max_wait_time = 60  # Maximale Wartezeit in Sekunden
            
            # Warten auf das nächste Signal (nach der ersten Umdrehung)
            logger.info("Warte auf nächstes Hall-Sensor-Signal...")
            
            while self.is_running and (time.time() - start_time) < max_wait_time:
                if self.hall_serial.in_waiting > 0:
                    try:
                        line = self.hall_serial.readline().decode('utf-8', errors='replace').strip()
                        if "Hall sensor value:" in line:
                            value = int(line.split(":")[-1].strip())
                            
                            # Wenn der Wert unter dem Schwellenwert liegt, haben wir das Heimsignal gefunden
                            if value < self.threshold:
                                # Ende der Zeitmessung
                                end_time = time.time()
                                rotation_time_ms = int((end_time - start_time) * 1000)
                                
                                logger.info(f"Hall-Sensor-Signal erkannt! Stoppt Motor. Rotationszeit: {rotation_time_ms}ms")
                                
                                # Motor stoppen
                                if not self.turn_motor_off():
                                    logger.error("Fehler beim Stoppen des Motors")
                                    return None
                                
                                self.is_running = False
                                signal_detected = True
                                
                                # Ergebnis speichern
                                self.full_rotation_time_ms = rotation_time_ms
                                
                                # In der Konfiguration speichern
                                config = config_manager.config.copy()
                                if 'rotation' not in config:
                                    config['rotation'] = {}
                                
                                config['rotation']['full_rotation_time_ms'] = rotation_time_ms
                                config_manager.save_config(config)
                                
                                logger.info(f"Kalibrierung erfolgreich. Vollständige Umdrehung: {rotation_time_ms}ms")
                                return rotation_time_ms
                    except Exception as e:
                        logger.error(f"Fehler beim Verarbeiten der Hall-Sensor-Daten: {e}")
                
                # Kurze Pause, um CPU-Last zu reduzieren
                time.sleep(0.01)
            
            # Timeout-Prüfung
            if (time.time() - start_time) >= max_wait_time:
                logger.warning(f"Timeout nach {max_wait_time} Sekunden. Kein Hall-Signal gefunden.")
                self.turn_motor_off()
                return None
            
            return None
            
        except Exception as e:
            logger.error(f"Fehler bei der Kalibrierung der Rotationszeit: {e}")
            logger.error(traceback.format_exc())
            
            # Im Fehlerfall versuchen, den Motor auszuschalten
            try:
                self.turn_motor_off()
                self.is_running = False
            except:
                pass
            
            return None
    
    def move_to_home_position(self):
        """
        Fährt den Drehteller zur Heimposition (Hall-Sensor-Signal)
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            if not self.hall_serial:
                logger.error("Keine Verbindung zum Hall-Sensor")
                return False
            
            # Puffer leeren
            self.hall_serial.reset_input_buffer()
            self.hall_serial.reset_output_buffer()
            
            # Prüfen, ob wir bereits auf der Heimposition sind
            logger.info("Prüfe aktuelle Position...")
            home_position_found = False
            
            # Einige Messungen durchführen
            for _ in range(5):
                if self.hall_serial.in_waiting > 0:
                    try:
                        line = self.hall_serial.readline().decode('utf-8', errors='replace').strip()
                        if "Hall sensor value:" in line:
                            value = int(line.split(":")[-1].strip())
                            logger.debug(f"Hall-Sensor-Wert: {value}")
                            
                            if value < self.threshold:
                                logger.info(f"Bereits auf Heimposition! Hall-Wert: {value}")
                                home_position_found = True
                                break
                    except Exception as e:
                        logger.error(f"Fehler beim Lesen des Hall-Sensors: {e}")
                time.sleep(0.1)
            
            # Wenn wir bereits auf der Heimposition sind, nichts weiter tun
            if home_position_found:
                return True
            
            # Motor einschalten und auf das Hall-Sensor-Signal warten
            logger.info("Nicht auf Heimposition. Fahre zur Heimposition...")
            if not self.turn_motor_on():
                logger.error("Fehler beim Starten des Motors")
                return False
            
            self.is_running = True
            signal_detected = False
            max_wait_time = 45  # Maximale Wartezeit in Sekunden (etwas länger als eine Umdrehung)
            start_time = time.time()
            
            while self.is_running and (time.time() - start_time) < max_wait_time:
                if self.hall_serial.in_waiting > 0:
                    try:
                        line = self.hall_serial.readline().decode('utf-8', errors='replace').strip()
                        if "Hall sensor value:" in line:
                            value = int(line.split(":")[-1].strip())
                            
                            # Wenn der Wert unter dem Schwellenwert liegt, haben wir das Heimsignal gefunden
                            if value < self.threshold:
                                logger.info(f"Heimposition gefunden! Hall-Wert: {value}")
                                
                                # Motor stoppen
                                if not self.turn_motor_off():
                                    logger.error("Fehler beim Stoppen des Motors")
                                    return False
                                
                                self.is_running = False
                                signal_detected = True
                                
                                # Mehrere Bestätigungsmessungen durchführen
                                confirm_values = []
                                for _ in range(3):
                                    time.sleep(0.1)
                                    while self.hall_serial.in_waiting > 0:
                                        try:
                                            confirm_line = self.hall_serial.readline().decode('utf-8', errors='replace').strip()
                                            if "Hall sensor value:" in confirm_line:
                                                confirm_value = int(confirm_line.split(":")[-1].strip())
                                                confirm_values.append(confirm_value)
                                        except Exception as e:
                                            logger.error(f"Fehler beim Lesen der Bestätigungsmessung: {e}")
                                
                                # Prüfen, ob wir wirklich auf der Heimposition sind
                                if confirm_values and any(v < self.threshold for v in confirm_values):
                                    logger.info(f"Heimposition bestätigt: {confirm_values}")
                                    return True
                                else:
                                    # Falls nicht, weitermachen
                                    logger.warning("Heimposition nicht bestätigt. Setze Suche fort...")
                                    if not self.turn_motor_on():
                                        logger.error("Fehler beim Neustarten des Motors")
                                        return False
                                    self.is_running = True
                    except Exception as e:
                        logger.error(f"Fehler beim Verarbeiten der Hall-Sensor-Daten: {e}")
                
                # Kurze Pause, um CPU-Last zu reduzieren
                time.sleep(0.01)
            
            # Timeout-Prüfung
            if (time.time() - start_time) >= max_wait_time:
                logger.warning(f"Timeout nach {max_wait_time} Sekunden. Heimposition nicht gefunden.")
                self.turn_motor_off()
                return False
            
            return signal_detected
            
        except Exception as e:
            logger.error(f"Fehler beim Fahren zur Heimposition: {e}")
            logger.error(traceback.format_exc())
            
            # Im Fehlerfall versuchen, den Motor auszuschalten
            try:
                self.turn_motor_off()
                self.is_running = False
            except:
                pass
            
            return False
    
    def move_degrees(self, degrees):
        """
        Bewegt den Drehteller um einen bestimmten Winkel
        
        Args:
            degrees: Winkel in Grad
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Eingabevalidierung
            if not isinstance(degrees, (int, float)) or degrees <= 0 or degrees > 360:
                logger.error(f"Ungültiger Drehwinkel: {degrees}°")
                return False
                
            # Berechne die Drehzeit in Millisekunden
            rotation_time_ms = int((degrees / 360.0) * self.full_rotation_time_ms)
            
            # Bei sehr kleinen Winkeln ein Minimum setzen, um Unterdrehung zu vermeiden
            # Aber auch nicht zu viel drehen lassen für 1°
            min_ms = 100  # Mindestens 100ms drehen
            
            # Lese Drehteller-Konfiguration aus den Einstellungen
            turntable_size = config_manager.config.get('rotation', {}).get('turntable_size', 'large')
            
            # Verwende unterschiedliche Divisoren je nach Drehtellergröße
            if turntable_size == 'small':  # Kleiner Testteller (12cm Umfang, 1:36 Übersetzung)
                max_ms_for_1_degree = int(self.full_rotation_time_ms / 180.0)  # Feiner Divisor für präzise Kontrolle
                logger.debug(f"Verwende small turntable settings (Divisor: 180.0)")
            else:  # Großer Teller (113cm Umfang, Standard-Übersetzung)
                max_ms_for_1_degree = int(self.full_rotation_time_ms / 45.0)  # Gröberer Divisor für merkbare Bewegung
                logger.debug(f"Verwende large turntable settings (Divisor: 45.0)")
            
            # Bei sehr kleinen Winkeln ein Minimum setzen, um Unterdrehung zu vermeiden
            # Aber auch nicht zu viel drehen lassen für 1°
            if degrees <= 1.0:
                # Für sehr kleine Winkel (<= 1°) besonderen Schutz einbauen
                rotation_time_ms = max(min_ms, min(rotation_time_ms, max_ms_for_1_degree))
                logger.info(f"Kleine Drehung angepasst: {degrees}° -> {rotation_time_ms}ms (begrenzt auf max {max_ms_for_1_degree}ms)")
                
            else:
                # Für normale Winkel nur eine Mindestzeit setzen
                rotation_time_ms = max(min_ms, rotation_time_ms)
                logger.info(f"Drehe um {degrees}° (Dauer: {rotation_time_ms}ms, basierend auf {self.full_rotation_time_ms}ms für 360°)")
            
            # Motor einschalten
            if not self.turn_motor_on():
                logger.error("Fehler beim Starten des Motors")
                return False
            
            # Warten für die berechnete Zeit
            time.sleep(rotation_time_ms / 1000.0)
            
            # Motor ausschalten
            if not self.turn_motor_off():
                logger.error("Fehler beim Stoppen des Motors")
                return False
            
            logger.info(f"Drehung um {degrees}° abgeschlossen")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Drehen um {degrees}°: {e}")
            logger.error(traceback.format_exc())
            
            # Im Fehlerfall versuchen, den Motor auszuschalten
            try:
                self.turn_motor_off()
            except:
                pass
            
            return False
    
    def close(self):
        """
        Schließt alle Verbindungen
        """
        try:
            # Motor ausschalten
            if self.is_running:
                self.turn_motor_off()
                self.is_running = False
            
            # Serial-Verbindung schließen
            if self.hall_serial:
                self.hall_serial.close()
                self.hall_serial = None
                
            # Arduino-Controller schließen
            if self.arduino_controller:
                self.arduino_controller.disconnect()
                
            logger.info("HallMotorController geschlossen")
        except Exception as e:
            logger.error(f"Fehler beim Schließen des HallMotorControllers: {e}")
            logger.error(traceback.format_exc())
