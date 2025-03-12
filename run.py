#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run.py
Haupteinstiegspunkt für die Drehteller-360-Grad-Anwendung
"""

import os
import sys
import argparse
import logging
from app import create_app

# Logger einrichten
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parst Kommandozeilenargumente"""
    parser = argparse.ArgumentParser(description='360° Drehteller Steuerung')
    parser.add_argument('--host', default='0.0.0.0', 
                        help='Host-Adresse für den Webserver')
    parser.add_argument('--port', default=5000, type=int,
                        help='Port für den Webserver')
    parser.add_argument('--debug', action='store_true',
                        help='Debug-Modus aktivieren')
    parser.add_argument('--env', default='development', 
                        choices=['development', 'production', 'testing'],
                        help='Umgebung (development, production, testing)')
    return parser.parse_args()

if __name__ == '__main__':
    # Stelle sicher, dass wir im richtigen Verzeichnis sind
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Kommandozeilenargumente parsen
    args = parse_arguments()
    
    # App erstellen
    app = create_app(args.env)
    
    # Debug-Modus nur in Entwicklungsumgebung aktivieren
    debug_mode = False
    if args.debug and args.env == 'development':
        logger.info("Debug-Modus aktiviert (nur in Entwicklungsumgebung erlaubt)")
        debug_mode = True
    else:
        if args.debug and args.env != 'development':
            logger.warning("Debug-Modus in Produktionsumgebung angefordert, aber nicht aktiviert")
        debug_mode = False
    
    # Starte den Server
    logger.info(f"Starte Server auf {args.host}:{args.port} (Umgebung: {args.env}, Debug: {debug_mode})")
    app.run(host=args.host, port=args.port, debug=debug_mode)
