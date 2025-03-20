#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/controllers/turntable_controller.py
Controller für die Drehteller-Steuerung - KORRIGIERTE VERSION
"""

import time
import math
import logging
import os
import uuid
from pathlib import Path
from app.models.photo_session import PhotoSession

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
        
        self.logger.debug(f"TurntableController initialisiert: Winkelschritt={self.default_angle_step}°")

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

        # Rotation Zeit berechnen
        rotation_time_ms = self.calculate_rotation_time(degrees)
        
        self.logger.debug(f"Drehe um {degrees}° (Dauer: {rotation_time_ms} ms)")

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
        KORRIGIERTE VERSION: Erst drehen, dann warten, dann Foto aufnehmen
        
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

            # Drehteller auf Position 0 zurücksetzen (ohne Bewegung)
            self.reset_position()

            # Anzahl der benötigten Schritte berechnen
            total_steps = math.floor(360 / project.angle_step)

            self.logger.info(f"Starte Fotosession mit {total_steps} Schritten alle {project.angle_step}°")

            # KORRIGIERTE REIHENFOLGE: Erst Foto bei Position 0 aufnehmen
            for step in range(total_steps):
                # Prüfen, ob die Session gestoppt wurde
                if not self.is_session_running:
                    self.logger.info("Fotosession wurde unterbrochen")
                    break
                
                # Aktuelle Winkelposition berechnen
                angle = step * project.angle_step
                
                # Dateiname für das Foto
                photo_filename = os.path.join(base_path, f"angle_{angle:03d}.jpg")
                
                # SCHRITT 1: Foto aufnehmen
                self.logger.info(f"Nehme Foto bei {angle}° auf")
                if not camera_controller.capture_photo(photo_filename):
                    self.logger.error(f"Fehler beim Aufnehmen des Fotos bei {angle}°")
                    self.is_session_running = False
                    return False
                
                # Session-Informationen aktualisieren
                session.add_photo(angle, photo_filename)
                
                # Wenn wir nicht beim letzten Schritt sind, drehe weiter
                if step < total_steps - 1 and self.is_session_running:
                    # SCHRITT 2: Drehen zur nächsten Position
                    self.logger.debug(f"Drehe um {project.angle_step}° zur nächsten Position")
                    if not self.move_degrees(project.angle_step):
                        self.logger.error(f"Fehler beim Drehen des Tellers um {project.angle_step}°")
                        self.is_session_running = False
                        return False
                    
                    # SCHRITT 3: Kurze Pause für Stabilisierung (2 Sekunden)
                    self.logger.debug("Warte 2 Sekunden für Stabilisierung...")
                    time.sleep(2)
                    
                    # Prüfen, ob die Session gestoppt wurde
                    if not self.is_session_running:
                        self.logger.info("Fotosession wurde während der Pause unterbrochen")
                        break
                    
                    # Kurzes Intervall vor dem nächsten Foto
                    # (Kann angepasst werden, falls ein längeres Intervall benötigt wird)
                    time.sleep(1)
                    
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
