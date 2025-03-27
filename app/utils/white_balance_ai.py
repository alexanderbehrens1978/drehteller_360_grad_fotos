#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/utils/white_balance_ai.py
KI-basierte Weißabgleich-Korrektur für einheitliche Produktfotos
"""

import os
import cv2
import numpy as np
import logging
from pathlib import Path
import json
from scipy.spatial import KDTree

# Logger einrichten
logger = logging.getLogger(__name__)

class WhiteBalanceAI:
    """KI-basierte Weißabgleichkorrektur für konsistente Farbgebung in 360° Aufnahmen"""
    
    def __init__(self, config_path=None):
        """
        Initialisiert die Weißabgleich-KI
        
        Args:
            config_path: Pfad zur Konfigurationsdatei für gespeicherte Referenzwerte
        """
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                                     'config', 'white_balance.json')
        
        # Referenz-Werte für Weißabgleich
        self.reference_values = None
        self.color_references = []
        self.reference_image = None
        
        # Modell-Daten
        self.color_map = None
        self.kdtree = None
        
        # Lade gespeicherte Referenzwerte wenn verfügbar
        self._load_config()
        
        self.logger.info("WhiteBalanceAI initialisiert")
    
    def _load_config(self):
        """Lädt gespeicherte Referenzwerte"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                if 'reference_values' in config:
                    self.reference_values = np.array(config['reference_values'])
                    self.logger.info(f"Referenzwerte für Weißabgleich geladen: {self.config_path}")
                    
                    # KD-Tree für schnellen Farbabgleich erstellen
                    if self.reference_values is not None and len(self.reference_values) > 0:
                        unique_colors = np.array(config.get('color_map', {}).get('colors', []))
                        mapped_colors = np.array(config.get('color_map', {}).get('mapped_colors', []))
                        
                        if len(unique_colors) > 0 and len(unique_colors) == len(mapped_colors):
                            self.color_map = {
                                'colors': unique_colors,
                                'mapped_colors': mapped_colors
                            }
                            
                            # KD-Tree für effiziente nächste-Nachbarn-Suche erstellen
                            self.kdtree = KDTree(unique_colors)
                            self.logger.info(f"Farbkorrektur-Modell mit {len(unique_colors)} Farben geladen")
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Weißabgleich-Konfiguration: {str(e)}")
    
    def _save_config(self):
        """Speichert aktuelle Referenzwerte"""
        try:
            # Stelle sicher, dass das Verzeichnis existiert
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            config = {
                'reference_values': self.reference_values.tolist() if self.reference_values is not None else None,
            }
            
            # Füge Farbmap hinzu, wenn vorhanden
            if self.color_map is not None:
                config['color_map'] = {
                    'colors': self.color_map['colors'].tolist(),
                    'mapped_colors': self.color_map['mapped_colors'].tolist()
                }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f)
                
            self.logger.info(f"Weißabgleich-Konfiguration gespeichert: {self.config_path}")
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Weißabgleich-Konfiguration: {str(e)}")
    
    def set_reference_image(self, image_path):
        """
        Setzt ein Referenzbild für den Weißabgleich
        
        Args:
            image_path: Pfad zum Referenzbild
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            # Lade Bild
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"Konnte Referenzbild nicht laden: {image_path}")
                return False
            
            # Berechne Farbwerte und -verteilung
            self._analyze_and_create_model(image)
            
            # Referenzbild speichern
            self.reference_image = image_path
            
            # Konfiguration speichern
            self._save_config()
            
            self.logger.info(f"Referenzbild für Weißabgleich gesetzt: {image_path}")
            return True
        except Exception as e:
            self.logger.error(f"Fehler beim Setzen des Referenzbildes: {str(e)}")
            return False
    
    def _analyze_and_create_model(self, image):
        """
        Analysiert ein Bild und erstellt ein Farbkorrekturmodell
        
        Args:
            image: Eingabebild (numpy.ndarray)
        """
        # Verwende die dominanten Farben im Bild als Referenz
        self.reference_values = self._calculate_color_statistics(image)
        
        # Erstelle Farb-Mapping-Modell
        lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Farben auf Cluster reduzieren für effizientes Mapping
        pixels = lab_image.reshape(-1, 3)
        
        # Wähle repräsentative Sample von Pixeln (maximal 10000 für Performance)
        if len(pixels) > 10000:
            indices = np.random.choice(len(pixels), 10000, replace=False)
            pixel_samples = pixels[indices]
        else:
            pixel_samples = pixels
        
        # Diese Farben werden als Referenz verwendet
        unique_colors = np.array(pixel_samples, dtype=np.float32)
        
        # Das Mapping ist anfangs identisch (wird später bei der Anwendung angepasst)
        mapped_colors = unique_colors.copy()
        
        self.color_map = {
            'colors': unique_colors,
            'mapped_colors': mapped_colors
        }
        
        # KD-Tree für schnelle Nachbarsuche erstellen
        self.kdtree = KDTree(unique_colors)
        
        self.logger.info(f"Farbkorrektur-Modell mit {len(unique_colors)} Farben erstellt")
    
    def _calculate_color_statistics(self, image):
        """
        Berechnet Farbstatistiken für ein Bild
        
        Args:
            image: Eingabebild (numpy.ndarray)
            
        Returns:
            Farbstatistiken als numpy.ndarray
        """
        # Konvertiere zu LAB-Farbraum (besser für Farbwahrnehmung)
        lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # Berechne Durchschnittswerte für jeden Kanal
        l_avg = np.mean(lab_image[:,:,0])
        a_avg = np.mean(lab_image[:,:,1])
        b_avg = np.mean(lab_image[:,:,2])
        
        # Standardabweichungen
        l_std = np.std(lab_image[:,:,0])
        a_std = np.std(lab_image[:,:,1])
        b_std = np.std(lab_image[:,:,2])
        
        # Perzentile für bessere Verteilungserfassung
        l_perc = np.percentile(lab_image[:,:,0], [10, 50, 90])
        a_perc = np.percentile(lab_image[:,:,1], [10, 50, 90])
        b_perc = np.percentile(lab_image[:,:,2], [10, 50, 90])
        
        # Kombiniere alle Werte in einen Vektor
        color_stats = np.array([
            l_avg, a_avg, b_avg,
            l_std, a_std, b_std,
            *l_perc, *a_perc, *b_perc
        ])
        
        return color_stats
    
    def correct_white_balance(self, image, strength=0.8):
        """
        Korrigiert den Weißabgleich eines Bildes basierend auf den Referenzwerten
        
        Args:
            image: Eingabebild (Pfad oder numpy.ndarray)
            strength: Stärke der Korrektur (0.0 bis 1.0)
            
        Returns:
            Korrigiertes Bild (numpy.ndarray)
        """
        # Wenn keine Referenzwerte vorhanden sind, gib das Originalbild zurück
        if self.reference_values is None or self.kdtree is None:
            self.logger.warning("Keine Referenzwerte für Weißabgleich vorhanden")
            return image if isinstance(image, np.ndarray) else cv2.imread(image)
        
        # Lade Bild wenn ein Pfad angegeben wurde
        if not isinstance(image, np.ndarray):
            image = cv2.imread(image)
            if image is None:
                self.logger.error(f"Konnte Bild nicht laden: {image}")
                return None
        
        try:
            # Konvertiere in LAB-Farbraum
            lab_image = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            
            # Bild-Form für spätere Wiederherstellung speichern
            original_shape = lab_image.shape
            
            # Zu Pixelarray umformen
            pixels = lab_image.reshape(-1, 3)
            
            # KI-basierte Farbkorrektur
            corrected_pixels = np.zeros_like(pixels, dtype=np.float32)
            
            # Batch-Verarbeitung für bessere Performance
            batch_size = 10000
            for i in range(0, len(pixels), batch_size):
                batch = pixels[i:i+batch_size]
                
                # Nächste Nachbarn im KD-Tree finden (Farbähnlichkeit)
                distances, indices = self.kdtree.query(batch, k=3)
                
                # Gewichtete Summe der Farbzuordnungen für Farbkorrektur
                weights = 1.0 / (distances + 1e-10)  # Vermeidung von Division durch Null
                weights = weights / np.sum(weights, axis=1, keepdims=True)
                
                # Für jeden Pixel im Batch
                for j in range(len(batch)):
                    # Original-Farbe
                    orig_color = batch[j]
                    
                    # Korrigierte Farbe im Referenzmodell
                    ref_colors = self.color_map['mapped_colors'][indices[j]]
                    corrected_color = np.sum(weights[j, :, np.newaxis] * ref_colors, axis=0)
                    
                    # Anwenden der Korrektur mit gewünschter Stärke
                    corrected_pixels[i+j] = orig_color * (1 - strength) + corrected_color * strength
            
            # L-Kanal separat anpassen für verbesserte Helligkeit
            target_l_mean = np.mean(self.color_map['mapped_colors'][:, 0])
            current_l_mean = np.mean(corrected_pixels[:, 0])
            
            # Helligkeit anpassen
            l_adjustment = (target_l_mean - current_l_mean) * strength
            corrected_pixels[:, 0] = np.clip(corrected_pixels[:, 0] + l_adjustment, 0, 255)
            
            # Zurück in Bildform bringen
            corrected_lab = corrected_pixels.reshape(original_shape)
            
            # Zurück zu BGR konvertieren
            corrected_image = cv2.cvtColor(corrected_lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
            
            return corrected_image
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Weißabgleich-Korrektur: {str(e)}")
            return image
    
    def batch_correct_project_images(self, project_folder, output_folder=None, strength=0.8):
        """
        Korrigiert den Weißabgleich für alle Bilder in einem Projektordner
        
        Args:
            project_folder: Pfad zum Projektordner mit Bildern
            output_folder: Pfad zum Ausgabeordner (optional, sonst wird ein 'processed' Unterordner erstellt)
            strength: Stärke der Korrektur (0.0 bis 1.0)
            
        Returns:
            Liste der korrigierten Bildpfade
        """
        if self.reference_values is None:
            self.logger.warning("Keine Referenzwerte für Weißabgleich vorhanden")
            return []
        
        try:
            # Stelle sicher, dass der Projektordner existiert
            if not os.path.exists(project_folder):
                self.logger.error(f"Projektordner existiert nicht: {project_folder}")
                return []
            
            # Wenn kein Ausgabeordner angegeben ist, erstelle einen Unterordner 'processed'
            if output_folder is None:
                output_folder = os.path.join(project_folder, 'processed')
            
            # Stelle sicher, dass der Ausgabeordner existiert
            os.makedirs(output_folder, exist_ok=True)
            
            # Finde alle Bilder im Projektordner
            image_files = []
            for ext in ['jpg', 'jpeg', 'png']:
                image_files.extend(list(Path(project_folder).glob(f'*.{ext}')))
                image_files.extend(list(Path(project_folder).glob(f'*.{ext.upper()}')))
            
            # Sortiere die Bilder (wichtig für die Reihenfolge in der 360°-Ansicht)
            image_files.sort()
            
            # Korrigiere jedes Bild
            corrected_paths = []
            for img_path in image_files:
                # Ausgabepfad erstellen
                rel_path = os.path.relpath(img_path, project_folder)
                output_path = os.path.join(output_folder, rel_path)
                
                # Korrigiere das Bild
                if self.correct_image(img_path, output_path, strength):
                    corrected_paths.append(output_path)
            
            self.logger.info(f"{len(corrected_paths)} Bilder mit einheitlichem Weißabgleich korrigiert")
            return corrected_paths
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Batch-Korrektur: {str(e)}")
            return []
    
    def correct_image(self, input_path, output_path, strength=0.8):
        """
        Korrigiert den Weißabgleich eines einzelnen Bildes und speichert es
        
        Args:
            input_path: Pfad zum Eingabebild
            output_path: Pfad zum Ausgabebild
            strength: Stärke der Korrektur (0.0 bis 1.0)
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            # Stelle sicher, dass die Ausgabeordner existieren
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Überprüfe, ob Eingabebild existiert
            if not os.path.exists(input_path):
                self.logger.error(f"Eingabebild existiert nicht: {input_path}")
                return False
            
            # Bild laden
            image = cv2.imread(input_path)
            if image is None:
                self.logger.error(f"Konnte Bild nicht laden: {input_path}")
                return False
            
            # Bild korrigieren
            corrected = self.correct_white_balance(image, strength)
            
            # Korrigiertes Bild speichern
            cv2.imwrite(output_path, corrected)
            
            self.logger.debug(f"Bild korrigiert: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Bildkorrektur: {str(e)}")
            return False
