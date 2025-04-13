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

    # Konstanten für den Drehteller (0,8° pro Sekunde bei diesem Motor)
    MOTOR_DEGREE_PER_SECOND = 0.8
    
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
        
        # Steuerungsmodus aus Konfiguration lesen
        self.control_mode = config_manager.config.get('rotation', {}).get('control_mode', 'standard')
        
        self.logger.debug(f"TurntableController initialisiert: Winkelschritt={self.default_angle_step}°, Modus={self.control_mode}")

    def calculate_rotation_time(self, degrees):
        """
        Berechnet die Zeit, die für eine Rotation um einen bestimmten Winkel benötigt wird
        
        Args:
            degrees: Winkel in Grad
            
        Returns:
            Zeit in Millisekunden
        """
        # Die Zeit wird in Millisekunden zurückgegeben
        return int((degrees / self.MOTOR_DEGREE_PER_SECOND) * 1000)

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
            # Überprüfen, ob nach mehreren Aufnahmen eine Neukalibrierung nötig ist
            # (Ursache für "munter drauf los drehen")
            # WICHTIG: Nur kalibrieren, wenn wir NICHT bereits auf Position 0 sind
            control_mode = config_manager.config.get('rotation', {}).get('control_mode', 'standard')
            if control_mode == 'hall' and project.current_position >= 360 and self.current_position != 0:
                self.logger.info("Vollständige Umdrehung erkannt, führe Heimpositions-Reset durch...")
                # Zur Heimposition fahren, um Drift zu vermeiden
                self._move_degrees_hall_sensor(0)
                # Die aktuelle Position auf 0 setzen, wurde von der Heimpositionsfunktion bereits gemacht
                # Keine weiteren Anpassungen notwendig
            
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

            # Drehteller auf Position 0 zurücksetzen (ohne Bewegung)
            self.reset_position()

            # Anzahl der benötigten Schritte berechnen
            total_steps = math.floor(360 / project.angle_step)

            self.logger.info(f"Starte Fotosession mit {total_steps} Schritten alle {project.angle_step}°")

            # WICHTIGE ÄNDERUNG: Erst Foto, dann drehen!
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
                    self.logger.debug(f"Drehe um {project.angle_step}° zur nächsten Position")
                    self.move_degrees(project.angle_step)
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
