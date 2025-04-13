#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/controllers/turntable_controller.py
Controller für die Drehteller-Steuerung
"""

import time
import math
import logging
import os
import uuid
from pathlib import Path
from app.models.photo_session import PhotoSession
from app.utils.config_manager import config_manager

# Logger einrichten
logger = logging.getLogger(__name__)

class TurntableController:
    """Controller für die Drehteller-Steuerung mit dem Arduino"""

    # Status der aktuellen Fotosession
    is_session_running = False

    def __init__(self, arduino_controller, default_angle_step=5):
        """
        Initialisiert den Drehteller-Controller
        
        Args:
            arduino_controller: ArduinoController-Instanz
            default_angle_step: Standard-Winkelschritt in Grad (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.arduino = arduino_controller
        self.default_angle_step = default_angle_step
        self.current_position = 0  # Aktuelle Position in Grad (0-360)
        
        # Hall-Sensor-Controller (wird bei Bedarf initialisiert)
        self.hall_controller = None
        
        # Konfigurationswerte aus config_manager lesen
        self.control_mode = config_manager.config.get('rotation', {}).get('control_mode', 'standard')
        self.motor_degree_per_second = config_manager.config.get('rotation', {}).get('motor_degree_per_second', 0.8)
        
        self.logger.debug(f"TurntableController initialisiert: Winkelschritt={self.default_angle_step}°, Modus={self.control_mode}")

    def calculate_rotation_time(self, degrees):
        """
        Berechnet die Zeit, die für eine Rotation um einen bestimmten Winkel benötigt wird
        
        Args:
            degrees: Winkel in Grad
            
        Returns:
            Zeit in Millisekunden
        """
        # Aktuellen Wert aus der Konfiguration verwenden
        motor_speed = config_manager.config.get('rotation', {}).get('motor_degree_per_second', self.motor_degree_per_second)
        
        # Die Zeit wird in Millisekunden zurückgegeben
        return int((degrees / motor_speed) * 1000)

    def move_degrees(self, degrees):
        """
        Bewegt den Drehteller um einen bestimmten Winkel
        
        Args:
            degrees: Winkel in Grad
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        # Eingabevalidierung
        try:
            degrees = float(degrees)
            if degrees <= 0 or degrees > 360:
                self.logger.error(f"Ungültiger Drehwinkel: {degrees}°")
                return False
        except (TypeError, ValueError):
            self.logger.error(f"Ungültiger Wert für Drehwinkel: {degrees}")
            return False
            
        if not self.arduino or not self.arduino.is_connected():
            self.logger.error("Arduino ist nicht verbunden")
            return False
            
        # Steuerungsmodus aus der aktuellen Konfiguration neu laden (falls geändert)
        self.control_mode = config_manager.config.get('rotation', {}).get('control_mode', 'standard')
        
        # Bei kleinen Winkeln (1°) in der Fotosession besonders vorsichtig sein
        if degrees <= 1.1 and self.is_session_running:
            self.logger.info(f"Präzise 1°-Drehung während der Fotosession")
            return self._move_small_degree_precise()
        
        # Je nach Steuerungsmodus die entsprechende Methode verwenden
        if self.control_mode == 'hall':
            return self._move_degrees_hall_sensor(degrees)
        else:
            return self._move_degrees_standard(degrees)
            
    def _move_degrees_standard(self, degrees):
        """
        Bewegt den Drehteller um einen bestimmten Winkel im Standard-Modus (zeitgesteuert)
        
        Args:
            degrees: Winkel in Grad
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        # Rotation Zeit berechnen
        rotation_time_ms = self.calculate_rotation_time(degrees)
        
        self.logger.debug(f"Drehe um {degrees}° im Standard-Modus (Dauer: {rotation_time_ms} ms)")

        # DIREKTE MOTOR-STEUERUNG statt rotate_for_duration
        try:
            # Motor einschalten
            self.arduino.turn_motor_on()
            
            # Log-Ausgabe hinzufügen
            self.logger.debug(f"Motor eingeschaltet, warte {rotation_time_ms/1000.0} Sekunden")
            
            # Warten für die berechnete Zeit
            time.sleep(rotation_time_ms / 1000.0)
            
            # Motor ausschalten
            self.logger.debug("Schalte Motor aus")
            self.arduino.turn_motor_off()
            
            # Position aktualisieren
            self.current_position = (self.current_position + degrees) % 360
            self.logger.info(f"Drehteller um {degrees}° gedreht, neue Position: {self.current_position}°")
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Drehen des Tellers um {degrees}°: {e}")
            # Im Fehlerfall trotzdem versuchen, den Motor auszuschalten
            try:
                self.arduino.turn_motor_off()
            except Exception as e2:
                self.logger.error(f"Fehler beim Ausschalten des Motors nach fehlgeschlagener Rotation: {e2}")
            return False
            
    def _move_degrees_hall_sensor(self, degrees):
        """
        Bewegt den Drehteller um einen bestimmten Winkel im Hall-Sensor-Modus (magnetgesteuert)
        
        Args:
            degrees: Winkel in Grad
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Konfiguration aus config_manager holen
            hall_config = config_manager.config.get('hall_sensor', {})
            hall_port = hall_config.get('port', '/dev/ttyACM1')
            hall_threshold = hall_config.get('threshold', 30)
            
            # Hall-Controller initialisieren, falls noch nicht geschehen
            if not self.hall_controller:
                from drehteller360.hall_motor_controller import HallMotorController
                self.logger.info(f"Initialisiere Hall-Motor-Controller. Hall-Port: {hall_port}, Motor-Port: {self.arduino.port}")
                self.hall_controller = HallMotorController(
                    hall_port=hall_port,
                    motor_port=self.arduino.port,
                    threshold=hall_threshold
                )
            
            # Spezialfall: Heimposition (0 Grad)
            if degrees == 0:
                self.logger.info("Fahre zur Heimposition (0°)")
                success = self.hall_controller.move_to_home_position()
                
                if success:
                    # Bei Erfolg Position auf 0° setzen
                    self.current_position = 0
                    
                    # Auch alle aktiven Projekte auf Position 0 setzen
                    from app.models.project import ProjectManager
                    from app.utils.path_manager import PathManager
                    
                    path_manager = PathManager()
                    project_manager = ProjectManager(path_manager.projects_dir)
                    
                    # Alle Projekte durchlaufen und aktuelle Position auf 0 setzen
                    projects = project_manager.get_all_projects()
                    for project in projects:
                        project.current_position = 0
                        project.save()
                        self.logger.info(f"Position für Projekt {project.id} auf 0° gesetzt")
                    
                    self.logger.info("Heimposition erreicht. Position auf 0° gesetzt für alle Projekte.")
                    return True
                else:
                    self.logger.error("Fehler beim Fahren zur Heimposition")
                    return False
            
            # Normale Drehung mit hall_controller
            self.logger.info(f"Drehe um {degrees}° im Hall-Sensor-Modus")
            success = self.hall_controller.move_degrees(degrees)
            
            if success:
                # Position aktualisieren
                self.current_position = (self.current_position + degrees) % 360
                self.logger.info(f"Drehteller um {degrees}° gedreht, neue Position: {self.current_position}°")
                return True
            else:
                self.logger.error(f"Fehler beim Drehen um {degrees}° im Hall-Sensor-Modus")
                return False
                
        except Exception as e:
            self.logger.error(f"Fehler beim Hall-Sensor-gesteuerten Drehen des Tellers: {e}")
            # Im Fehlerfall trotzdem versuchen, den Motor auszuschalten
            try:
                if self.hall_controller:
                    self.hall_controller.turn_motor_off()
                else:
                    self.arduino.turn_motor_off()
            except Exception as e2:
                self.logger.error(f"Fehler beim Ausschalten des Motors nach fehlgeschlagener Rotation: {e2}")
            return False

    def _move_small_degree_precise(self):
        """
        Führt eine präzise 1°-Drehung während einer Fotosession durch.
        Diese Methode ist speziell für kleine Winkel optimiert und
        verhindert unerwünschte vollständige Drehungen.
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        try:
            # Für extrem kleine Winkel verwenden wir eine feste kurze Zeit
            # Bei 0,8° pro Sekunde brauchen wir für 1° ca. 1,25 Sekunden
            # Wir setzen etwas weniger um Überdrehung zu vermeiden
            rotation_time_ms = 900  # 900ms für ca. 1°
            
            self.logger.debug(f"Präzise 1°-Drehung mit fester Zeit: {rotation_time_ms}ms")

            # Motor einschalten
            self.arduino.turn_motor_on()
            
            # Kurze Wartezeit für die Rotation
            time.sleep(rotation_time_ms / 1000.0)
            
            # Motor ausschalten
            self.logger.debug("Schalte Motor aus")
            self.arduino.turn_motor_off()
            
            # Position aktualisieren
            self.current_position = (self.current_position + 1) % 360
            self.logger.info(f"Drehteller um 1° gedreht, neue Position: {self.current_position}°")
            return True
        except Exception as e:
            self.logger.error(f"Fehler bei der präzisen 1°-Drehung: {e}")
            # Im Fehlerfall trotzdem versuchen, den Motor auszuschalten
            try:
                self.arduino.turn_motor_off()
            except Exception as e2:
                self.logger.error(f"Fehler beim Ausschalten des Motors nach fehlgeschlagener Rotation: {e2}")
            return False

    def reset_position(self):
        """
        Setzt die aktuelle Position auf 0 Grad zurück (ohne Bewegung)
        
        Returns:
            True
        """
        self.current_position = 0
        self.logger.info("Drehteller-Position zurückgesetzt")
        return True

    def stop_session(self):
        """
        Stoppt die laufende Fotosession
        
        Returns:
            True
        """
        self.is_session_running = False
        self.logger.info("Fotosession wurde gestoppt")
        return True

    def start_session(self, project, camera_controller):
        """
        Startet eine Fotosession für ein Projekt
        
        Die Methode verwendet den Hall-Sensor, um die Zeit für eine volle Umdrehung zu messen.
        Basierend auf dieser Zeit und dem vom Benutzer definierten Winkel werden Zeitabschnitte
        für Teilrotationen berechnet. Die Heimposition wird zur Berechnung des Umfangs und der 
        Zeit für das Projekt verwendet. Während der Aufnahme findet keine Kalibrierung statt.
        
        Args:
            project: Project-Instanz
            camera_controller: CameraController-Instanz
            
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not self.arduino or not self.arduino.is_connected():
            self.logger.error("Arduino ist nicht verbunden")
            return False

        if not camera_controller:
            self.logger.error("Kamera-Controller ist nicht initialisiert")
            return False

        try:
            # Session als aktiv markieren
            self.is_session_running = True
            
            # Neue Session erstellen
            session_id = str(uuid.uuid4())
            session = PhotoSession(
                id=session_id,
                name=f"Session {time.strftime('%Y-%m-%d %H:%M')}",
                timestamp=time.time(),
                angle_step=project.angle_step
            )

            # Speicherpfad für die Fotos
            base_path = os.path.join(project.path, "sessions", session_id)
            os.makedirs(base_path, exist_ok=True)

            # Zur Heimposition fahren (falls nicht bereits dort)
            self.logger.info("Fahre zur Heimposition für Kalibrierung...")
            
            # Hall-Sensor Controller initialisieren
            if not self.hall_controller:
                hall_config = config_manager.config.get('hall_sensor', {})
                hall_port = hall_config.get('port', '/dev/ttyACM1')
                hall_threshold = hall_config.get('threshold', 30)
                
                from drehteller360.hall_motor_controller import HallMotorController
                self.logger.info(f"Initialisiere Hall-Motor-Controller. Hall-Port: {hall_port}, Motor-Port: {self.arduino.port}")
                self.hall_controller = HallMotorController(
                    hall_port=hall_port,
                    motor_port=self.arduino.port,
                    threshold=hall_threshold
                )
            
            # Zur Heimposition fahren (0°)
            if self.hall_controller.move_to_home_position():
                # Position im Controller und Projekt aktualisieren
                self.current_position = 0
                project.update_position(0)
                self.logger.info("Heimposition erreicht. Position auf 0° gesetzt für Controller und Projekt.")
            else:
                self.logger.error("Fehler beim Fahren zur Heimposition")
                return False
            
            # Zeit für eine komplette Umdrehung messen
            self.logger.info("Messe Zeit für eine vollständige Umdrehung...")
            
            # Initialisieren der Variablen für die Zeitmessung
            rotation_start_time = None
            full_rotation_time_ms = None
            hall_sensor_detected_count = 0
            
            # Hall-Sensor-Ereignis-Handler definieren
            def on_hall_sensor_event():
                nonlocal rotation_start_time, full_rotation_time_ms, hall_sensor_detected_count
                
                current_time = time.time() * 1000  # Zeit in Millisekunden
                
                hall_sensor_detected_count += 1
                
                if hall_sensor_detected_count == 1:
                    # Erste Erkennung - Start der Zeitmessung
                    rotation_start_time = current_time
                    self.logger.info("Hall-Sensor zum ersten Mal erkannt - Zeitmessung gestartet")
                
                elif hall_sensor_detected_count == 2:
                    # Zweite Erkennung - Ende der Zeitmessung
                    full_rotation_time_ms = current_time - rotation_start_time
                    self.logger.info(f"Hall-Sensor zum zweiten Mal erkannt - Volle Umdrehung: {full_rotation_time_ms} ms")
            
            # Hall-Sensor-Ereignis-Handler registrieren
            self.hall_controller.set_hall_sensor_callback(on_hall_sensor_event)
            
            # Motor starten für die Messung
            self.arduino.turn_motor_on()
            
            # Warten auf zwei Hall-Sensor-Erkennungen
            start_time = time.time()
            timeout = 60  # Timeout in Sekunden (für eine volle Drehung)
            
            while hall_sensor_detected_count < 2 and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            # Motor stoppen nach der Messung
            self.arduino.turn_motor_off()
            
            # Überprüfen, ob die Messung erfolgreich war
            if full_rotation_time_ms is None:
                self.logger.error("Fehler bei der Zeitmessung für die volle Umdrehung")
                self.is_session_running = False
                return False
            
            # Berechnen der Zeit für jeden Winkelschritt
            angle_step_time_ms = (project.angle_step / 360.0) * full_rotation_time_ms
            self.logger.info(f"Zeit pro {project.angle_step}° Schritt: {angle_step_time_ms} ms")
        
            # Zurück zur Heimposition für den Start der Aufnahmen
            self.logger.info("Fahre zur Heimposition für den Start der Aufnahmen...")
            if self.hall_controller.move_to_home_position():
                # Position im Controller und Projekt aktualisieren
                self.current_position = 0
                project.update_position(0)
                self.logger.info("Heimposition erreicht. Position auf 0° gesetzt für Controller und Projekt.")
            else:
                self.logger.error("Fehler beim Fahren zur Heimposition")
                return False
            
            # Hall-Sensor-Callback deaktivieren für die Aufnahmen
            self.hall_controller.set_hall_sensor_callback(None)
            
            # Anzahl der benötigten Schritte berechnen
            total_steps = math.floor(360 / project.angle_step)
            self.logger.info(f"Starte Fotosession mit {total_steps} Schritten alle {project.angle_step}°")
            
            # WICHTIG: Erst Foto aufnehmen, dann drehen
            for step in range(total_steps):
                # Prüfen, ob die Session gestoppt wurde
                if not self.is_session_running:
                    self.logger.info("Fotosession wurde unterbrochen")
                    break
                
                # Aktuelle Winkelposition
                angle = step * project.angle_step
                
                # Dateiname für das Foto
                photo_filename = os.path.join(base_path, f"angle_{angle:03d}.jpg")
                
                # Foto aufnehmen
                self.logger.info(f"Nehme Foto bei {angle}° auf")
                if not camera_controller.capture_photo(photo_filename):
                    self.logger.error(f"Fehler beim Aufnehmen des Fotos bei {angle}°")
                    self.is_session_running = False
                    return False
                
                # Session-Informationen aktualisieren
                session.add_photo(angle, photo_filename)
                
                # Wenn wir nicht beim letzten Schritt sind, drehen wir weiter
                if step < total_steps - 1 and self.is_session_running:
                    # Status für den nächsten Schritt
                    next_angle = (angle + project.angle_step) % 360
                    self.logger.debug(f"Drehe um {project.angle_step}° zur nächsten Position ({next_angle}°)")
                    
                    # Motor einschalten
                    self.arduino.turn_motor_on()
                    
                    # Für die berechnete Zeit warten
                    self.logger.debug(f"Warte für {angle_step_time_ms} ms")
                    time.sleep(angle_step_time_ms / 1000.0)
                    
                    # Motor ausschalten
                    self.arduino.turn_motor_off()
                    
                    # Position aktualisieren
                    self.current_position = next_angle
                    project.update_position(next_angle)
                    self.logger.debug(f"Position aktualisiert: Controller={self.current_position}°, Projekt={project.current_position}°")
                    
                    # Kurze Pause für Stabilisierung
                    time.sleep(2)
            
            # Session als abgeschlossen markieren, wenn sie nicht manuell gestoppt wurde
            session.completed = self.is_session_running
            self.is_session_running = False
            
            # Session zum Projekt hinzufügen
            project.add_session(session)
            
            self.logger.info(f"Fotosession erfolgreich abgeschlossen: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler während der Fotosession: {str(e)}")
            self.is_session_running = False
            return False
