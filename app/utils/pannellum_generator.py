#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/utils/pannellum_generator.py
Generiert Pannellum-Viewer HTML für die 360°-Ansicht
"""

import os
import json
import logging
from pathlib import Path

# Logger einrichten
logger = logging.getLogger(__name__)

class PannellumGenerator:
    """Klasse zur Generierung von Pannellum-Viewern aus Projektbildern"""
    
    def __init__(self):
        """Initialisiert den Pannellum-Generator"""
        self.logger = logging.getLogger(__name__)
        
    def generate_viewer_html(self, project, base_url=""):
        """
        Generiert das HTML für einen Pannellum-Viewer
        
        Args:
            project: Projekt-Instanz mit Bildern
            base_url: Basis-URL für die Bilder (optional)
            
        Returns:
            HTML-Code für den Pannellum-Viewer
        """
        if not project or not project.images or len(project.images) == 0:
            self.logger.error("Kann keinen Viewer erstellen: Keine Bilder im Projekt vorhanden")
            return None
            
        # Sortiere die Bilder nach Winkel, wenn vorhanden
        images = sorted(project.images, key=lambda x: x.get('angle', 0) if isinstance(x, dict) else 0)
        
        # Bildpfade erstellen
        image_paths = []
        for img in images:
            if isinstance(img, dict) and 'path' in img:
                # Relatives Pfad zum Bild (innerhalb des Projektordners)
                rel_path = img['path']
                if not base_url:
                    # Wenn keine Basis-URL angegeben ist, verwende relativen Pfad
                    image_url = f"/projects/image/{project.id}/{rel_path}"
                else:
                    # Sonst füge Basis-URL hinzu
                    image_url = f"{base_url}/projects/image/{project.id}/{rel_path}"
                image_paths.append(image_url)
            elif isinstance(img, str):
                # Falls direkt ein Pfad angegeben ist
                if not base_url:
                    image_url = f"/projects/image/{project.id}/{img}"
                else:
                    image_url = f"{base_url}/projects/image/{project.id}/{img}"
                image_paths.append(image_url)
        
        # Pannellum-Konfiguration erstellen
        config = {
            "type": "equirectangular",
            "autoLoad": True,
            "panoramas": image_paths
        }
        
        # HTML für den Pannellum-Viewer generieren
        html = self._generate_viewer_template(project.name, config, image_paths)
        
        return html
    
    def _generate_viewer_template(self, title, config, image_paths):
        """
        Generiert die HTML-Vorlage für den Pannellum-Viewer
        
        Args:
            title: Titel des Viewers
            config: Pannellum-Konfiguration
            image_paths: Liste der Bildpfade
            
        Returns:
            HTML-Code für den Pannellum-Viewer
        """
        # HTML-Template für den Viewer
        return f'''<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 360° Ansicht</title>
    <!-- Pannellum CSS -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.css"/>
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
        }}
        #panorama {{
            width: 100vw;
            height: 100vh;
        }}
        .controls {{
            position: absolute;
            bottom: 10px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 10;
            background: rgba(0,0,0,0.5);
            padding: 10px;
            border-radius: 5px;
            display: flex;
            gap: 10px;
        }}
        .control-btn {{
            background: #fff;
            color: #000;
            border: none;
            padding: 8px 15px;
            border-radius: 3px;
            cursor: pointer;
            font-weight: bold;
        }}
        .control-btn:hover {{
            background: #eee;
        }}
    </style>
</head>
<body>
    <div id="panorama"></div>
    
    <div class="controls">
        <button id="prev-btn" class="control-btn">◀ Vorheriges</button>
        <button id="play-btn" class="control-btn">▶ Auto-Rotation</button>
        <button id="next-btn" class="control-btn">Nächstes ▶</button>
    </div>

    <!-- Pannellum JS -->
    <script src="https://cdn.jsdelivr.net/npm/pannellum@2.5.6/build/pannellum.js"></script>
    <script>
        // Bild-Pfade
        const images = {json.dumps(image_paths)};
        let currentIndex = 0;
        let autoRotateInterval = null;
        
        // Pannellum-Viewer initialisieren
        const viewer = pannellum.viewer('panorama', {{
            "type": "equirectangular",
            "panorama": images[0],
            "autoLoad": true,
            "showControls": false
        }});
        
        // Viewer-Steuerung
        document.getElementById('prev-btn').addEventListener('click', () => {{
            currentIndex = (currentIndex - 1 + images.length) % images.length;
            viewer.loadScene('scene' + currentIndex);
        }});
        
        document.getElementById('next-btn').addEventListener('click', () => {{
            currentIndex = (currentIndex + 1) % images.length;
            viewer.loadScene('scene' + currentIndex);
        }});
        
        const playBtn = document.getElementById('play-btn');
        playBtn.addEventListener('click', toggleAutoRotate);
        
        // Auto-Rotation ein-/ausschalten
        function toggleAutoRotate() {{
            if (autoRotateInterval) {{
                // Stoppen
                clearInterval(autoRotateInterval);
                autoRotateInterval = null;
                playBtn.textContent = '▶ Auto-Rotation';
            }} else {{
                // Starten
                autoRotateInterval = setInterval(() => {{
                    currentIndex = (currentIndex + 1) % images.length;
                    viewer.loadScene('scene' + currentIndex);
                }}, 1000);
                playBtn.textContent = '⏸ Pause';
            }}
        }}
        
        // Szenen für jedes Bild erstellen
        images.forEach((image, index) => {{
            viewer.addScene('scene' + index, {{
                "panorama": image,
                "type": "equirectangular"
            }});
        }});
        
        // Tastatur-Navigation
        document.addEventListener('keydown', (e) => {{
            switch (e.key) {{
                case 'ArrowLeft':
                    document.getElementById('prev-btn').click();
                    break;
                case 'ArrowRight':
                    document.getElementById('next-btn').click();
                    break;
                case ' ': // Leertaste
                    toggleAutoRotate();
                    break;
            }}
        }});
        
        // Auto-Rotation standardmäßig starten
        toggleAutoRotate();
    </script>
</body>
</html>'''
    
    def generate_viewer_file(self, project, output_path):
        """
        Generiert eine HTML-Datei für den Pannellum-Viewer
        
        Args:
            project: Projekt-Instanz mit Bildern
            output_path: Pfad, an dem die HTML-Datei gespeichert werden soll
            
        Returns:
            Pfad zur generierten HTML-Datei
        """
        # HTML generieren
        html = self.generate_viewer_html(project)
        
        if not html:
            self.logger.error("Konnte keinen Viewer generieren")
            return None
        
        try:
            # Verzeichnis erstellen, falls es nicht existiert
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # HTML-Datei schreiben
            with open(output_path, 'w') as f:
                f.write(html)
                
            self.logger.info(f"Pannellum-Viewer für Projekt {project.id} nach {output_path} exportiert")
            return output_path
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern des Pannellum-Viewers: {str(e)}")
            return None

# Globale Instanz erstellen
pannellum_generator = PannellumGenerator()
