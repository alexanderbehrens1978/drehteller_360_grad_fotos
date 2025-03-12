#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run.py
Haupteinstiegspunkt für die Drehteller-360-Grad-Anwendung
"""

import os
import sys
import argparse
from app import create_app

def parse_arguments():
    """Parst Kommandozeilenargumente"""
    parser = argparse.ArgumentParser(description='360° Drehteller Steuerung')
    parser.add_argument('--host', default='0.0.0.0', 
                        help='Host-Adresse für den Webserver')
    parser.add_argument('--port', default=5000, type=int,
                        help='Port für den Webserver')
    parser.add_argument('--debug', action='store_true',
                        help='Debug-Modus aktivieren (nur für Entwicklung!)')
    parser.add_argument('--env', default='production', 
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
    if args.debug and args.env == 'development':
        app.config['DEBUG'] = True
    elif args.env == 'production':
        # Sicherstellen, dass Debug-Modus in Produktion deaktiviert ist
        app.config['DEBUG'] = False
    
    # Starte den Server
    app.run(host=args.host, port=args.port, debug=app.config['DEBUG'])
