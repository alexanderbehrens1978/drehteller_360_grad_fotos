#!/usr/bin/env python3
"""
Drehteller 360° Fotos - Hauptanwendung
Dieses Skript startet die Weboberfläche für die Drehteller-Steuerung.
"""

import os
import sys
import logging
from app import create_app
from app.services.config_manager import config_manager

# Konfiguriere Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('drehteller360')

def main():
    """Hauptfunktion zum Starten der Anwendung"""
    # Stelle sicher, dass die erforderlichen Verzeichnisse existieren
    os.makedirs('static/photos', exist_ok=True)
    os.makedirs('static/test', exist_ok=True)
    
    # Erstelle die Flask-App
    app = create_app()
    
    # Starte die Flask-App
    host = config_manager.get('web.host', '0.0.0.0')
    port = config_manager.get('web.port', 5000)
    debug = config_manager.get('web.debug', True)
    
    logger.info(f"Starte Drehteller 360° Weboberfläche auf {host}:{port}")
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
