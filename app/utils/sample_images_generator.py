#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/utils/sample_images_generator.py
Generiert Beispielbilder für den Simulator
"""

import os
import random
import math
import logging
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from app.utils.path_manager import PathManager

class SampleImagesGenerator:
    """Klasse zur Generierung von Beispielbildern"""
    
    def __init__(self, output_path=None, width=800, height=600):
        """
        Initialisiert den Beispielbilder-Generator
        
        Args:
            output_path: Ausgabeverzeichnis (optional)
            width: Bildbreite (optional)
            height: Bildhöhe (optional)
        """
        # Logger einrichten
        self.logger = logging.getLogger(__name__)
        
        # Verzeichnis festlegen
        path_manager = PathManager()
        self.output_path = output_path or os.path.join(path_manager.static_dir, 'sample_images')
        
        # Bildgröße
        self.width = width
        self.height = height

        # Sicherstellen, dass das Ausgabeverzeichnis existiert
        os.makedirs(self.output_path, exist_ok=True)
        self.logger.debug(f"Beispielbilder-Generator initialisiert: {self.output_path} ({self.width}x{self.height})")

    def generate_color_gradient_image(self, index):
        """
        Generiert ein Bild mit Farbverlauf
        
        Args:
            index: Index für den Bildnamen
            
        Returns:
            Pfad zum generierten Bild
        """
        # Neues Bild mit Farbverlauf erstellen
        image = Image.new('RGB', (self.width, self.height))
        draw = ImageDraw.Draw(image)

        # Farbverlauf generieren
        for y in range(self.height):
            r = int(255 * y / self.height)
            g = int(255 * (1 - y / self.height))
            b = int(128 + 127 * math.sin(y / 50))

            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        # Text hinzufügen, um das Bild zu identifizieren
        try:
            # Versuche die Standard-Schriftart zu laden
            font = ImageFont.load_default()
            
            # Als Alternative könnten wir versuchen, eine spezifische Schriftart zu laden
            # font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except IOError:
            # Fallback auf Standard-Schriftart
            font = ImageFont.load_default()

        text = f"Beispielbild {index}"
        
        # Textfarbe basierend auf dem Index wählen
        text_color = (255, 255, 255) if index % 2 == 0 else (50, 50, 50)
        
        # Text zeichnen (Kompatibel mit verschiedenen PIL-Versionen)
        # In neueren PIL-Versionen wurde textsize durch textbbox ersetzt
        try:
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width, text_height = draw.textsize(text, font=font)
            
            text_position = ((self.width - text_width) // 2, 50)
            draw.text(text_position, text, font=font, fill=text_color)
        except Exception as e:
            # Bei Problemen mit der Textdarstellung alternativen Ansatz verwenden
            self.logger.warning(f"Fehler bei der Textdarstellung: {e}")
            draw.text((50, 50), text, fill=text_color)
        
        # Winkelmarkierung hinzufügen (simuliert 360°-Aufnahmen)
        angle = (index % 36) * 10  # 0-350° in 10°-Schritten
        
        # Winkeltext
        angle_text = f"{angle}°"
        try:
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), angle_text, font=font)
                angle_text_width = bbox[2] - bbox[0]
                angle_text_height = bbox[3] - bbox[1]
            else:
                angle_text_width, angle_text_height = draw.textsize(angle_text, font=font)
            
            draw.text((self.width - angle_text_width - 50, self.height - angle_text_height - 50), 
                    angle_text, font=font, fill=text_color)
        except Exception as e:
            # Bei Problemen mit der Textdarstellung alternativen Ansatz verwenden
            self.logger.warning(f"Fehler bei der Textdarstellung des Winkels: {e}")
            draw.text((self.width - 100, self.height - 50), angle_text, fill=text_color)
        
        # Bild speichern
        filename = os.path.join(self.output_path, f'sample_image_{index}.jpg')
        image.save(filename)
        
        self.logger.debug(f"Beispielbild {index} erstellt: {filename}")
        return filename

    def generate_pattern_image(self, index):
        """
        Generiert ein Bild mit Muster
        
        Args:
            index: Index für den Bildnamen
            
        Returns:
            Pfad zum generierten Bild
        """
        # Neues Bild erstellen
        image = Image.new('RGB', (self.width, self.height), color=(240, 240, 240))
        draw = ImageDraw.Draw(image)
        
        # Muster basierend auf dem Index generieren
        pattern_type = index % 4
        
        if pattern_type == 0:
            # Gittermuster
            for x in range(0, self.width, 50):
                draw.line([(x, 0), (x, self.height)], fill=(200, 200, 200), width=1)
            for y in range(0, self.height, 50):
                draw.line([(0, y), (self.width, y)], fill=(200, 200, 200), width=1)
                
        elif pattern_type == 1:
            # Kreismuster
            for radius in range(50, int(max(self.width, self.height)), 100):
                draw.ellipse((self.width//2 - radius, self.height//2 - radius, 
                              self.width//2 + radius, self.height//2 + radius), 
                             outline=(200, 200, 200), width=2)
                
        elif pattern_type == 2:
            # Diagonales Muster
            for i in range(-self.height, self.width + self.height, 50):
                draw.line([(i, 0), (i + self.height, self.height)], fill=(200, 200, 200), width=1)
                
        else:
            # Zufällige Punkte
            for _ in range(500):
                x = random.randint(0, self.width)
                y = random.randint(0, self.height)
                size = random.randint(2, 10)
                draw.ellipse((x-size//2, y-size//2, x+size//2, y+size//2), 
                             fill=(200, 200, 200))
        
        # Text hinzufügen
        try:
            font = ImageFont.load_default()
        except IOError:
            # Fallback auf Standard-Schriftart
            font = ImageFont.load_default()

        text = f"Muster {index}"
        text_color = (100, 100, 100)
        
        # Text zeichnen (kompatibel mit verschiedenen PIL-Versionen)
        try:
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                text_width, text_height = draw.textsize(text, font=font)
            
            text_position = ((self.width - text_width) // 2, 50)
            draw.text(text_position, text, font=font, fill=text_color)
        except Exception as e:
            # Bei Problemen mit der Textdarstellung alternativen Ansatz verwenden
            self.logger.warning(f"Fehler bei der Textdarstellung: {e}")
            draw.text((50, 50), text, fill=text_color)
        
        # Winkelmarkierung
        angle = (index % 36) * 10  # 0-350° in 10°-Schritten
        angle_text = f"{angle}°"
        
        try:
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), angle_text, font=font)
                angle_text_width = bbox[2] - bbox[0]
                angle_text_height = bbox[3] - bbox[1]
            else:
                angle_text_width, angle_text_height = draw.textsize(angle_text, font=font)
            
            draw.text((self.width - angle_text_width - 50, self.height - angle_text_height - 50), 
                    angle_text, font=font, fill=text_color)
        except Exception as e:
            # Bei Problemen mit der Textdarstellung alternativen Ansatz verwenden
            self.logger.warning(f"Fehler bei der Textdarstellung des Winkels: {e}")
            draw.text((self.width - 100, self.height - 50), angle_text, fill=text_color)
        
        # Bild speichern
        filename = os.path.join(self.output_path, f'sample_pattern_{index}.jpg')
        image.save(filename)
        
        self.logger.debug(f"Musterbild {index} erstellt: {filename}")
        return filename
    
    def generate_sample_images(self, count=10):
        """
        Generiert mehrere Beispielbilder
        
        Args:
            count: Anzahl der zu generierenden Bilder (optional)
            
        Returns:
            Liste von Pfaden zu den generierten Bildern
        """
        generated_images = []
        
        # Abwechselnd Farbverlaufs- und Musterbilder generieren
        for i in range(count):
            if i % 2 == 0:
                image_path = self.generate_color_gradient_image(i)
            else:
                image_path = self.generate_pattern_image(i)
                
            generated_images.append(image_path)
        
        self.logger.info(f"{count} Beispielbilder generiert")
        return generated_images


# Standalone-Verwendungsbeispiel
if __name__ == '__main__':
    # Logger konfigurieren
    logging.basicConfig(level=logging.DEBUG)
    
    # Generator erstellen
    generator = SampleImagesGenerator()
    
    # Beispielbilder generieren
    generated_images = generator.generate_sample_images(10)
    
    print(f"{len(generated_images)} Beispielbilder wurden erstellt:")
    for img in generated_images:
        print(f"- {img}")
