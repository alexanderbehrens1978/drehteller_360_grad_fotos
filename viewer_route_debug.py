#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug-Skript für 360° Viewer Routing-Probleme
Dieses Skript prüft, ob die Cloudimage-Viewer Route korrekt funktioniert.
"""

import sys
import os
import logging
import requests
from urllib.parse import urljoin

# ---- KONFIGURATION ----
# Passe diese Werte an deine Umgebung an
BASE_URL = "http://192.168.188.105:5000"  # Die URL deines Servers
PROJECT_ID = "f3d9cd31-3bfe-4f92-acef-927759c4982c"  # Die ID aus dem Screenshot
DEBUG_LEVEL = logging.DEBUG

# ---- LOGGING-SETUP ----
logging.basicConfig(
    level=DEBUG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_viewer_overview_page():
    """Teste, ob die Viewer-Übersichtsseite erreichbar ist."""
    url = urljoin(BASE_URL, "/viewer")
    logger.info(f"Teste Viewer-Übersicht: {url}")
    
    try:
        response = requests.get(url)
        logger.info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Viewer-Übersichtsseite ist erreichbar!")
            return True
        else:
            logger.error(f"Viewer-Übersichtsseite nicht erreichbar (Status {response.status_code})")
            return False
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Viewer-Übersicht: {str(e)}")
        return False

def test_cloudimage_viewer_route():
    """Teste, ob die Cloudimage-Viewer Route funktioniert."""
    url = urljoin(BASE_URL, f"/viewer/cloudimage?project={PROJECT_ID}")
    logger.info(f"Teste Cloudimage-Viewer: {url}")
    
    try:
        response = requests.get(url)
        logger.info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            logger.info("Cloudimage-Viewer ist erreichbar!")
            return True
        else:
            logger.error(f"Cloudimage-Viewer nicht erreichbar (Status {response.status_code})")
            logger.error(f"Antwort: {response.text[:500]}...")  # Ersten 500 Zeichen der Antwort
            return False
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Cloudimage-Viewers: {str(e)}")
        return False

def check_project_exists():
    """Prüfe, ob das Projekt existiert und geladen werden kann."""
    url = urljoin(BASE_URL, f"/api/project/{PROJECT_ID}")
    logger.info(f"Prüfe Projekt-Existenz: {url}")
    
    try:
        response = requests.get(url)
        logger.info(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            project = response.json()
            logger.info(f"Projekt gefunden: {project.get('name', 'Unbekannt')}")
            logger.info(f"Bilder im Projekt: {len(project.get('images', []))}")
            return True
        else:
            logger.error(f"Projekt nicht gefunden (Status {response.status_code})")
            return False
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des Projekts: {str(e)}")
        return False

def check_log_files():
    """Versuche, die Logdateien zu lesen, wenn vorhanden."""
    log_paths = [
        "/home/alex/development/drehteller_360_grad_fotos/logs/app.log",
        "/home/alex/development/drehteller_360_grad_fotos/drehteller360.log"
    ]
    
    for log_path in log_paths:
        if os.path.exists(log_path):
            logger.info(f"Logdatei gefunden: {log_path}")
            try:
                with open(log_path, 'r') as f:
                    # Letzte 20 Zeilen lesen
                    lines = f.readlines()
                    last_lines = lines[-20:] if len(lines) > 20 else lines
                    logger.info(f"Letzte Logeinträge aus {log_path}:")
                    for line in last_lines:
                        logger.info(f"  {line.strip()}")
            except Exception as e:
                logger.error(f"Fehler beim Lesen der Logdatei {log_path}: {str(e)}")
        else:
            logger.warning(f"Logdatei nicht gefunden: {log_path}")

def check_file_permissions():
    """Prüft, ob die Berechtigungen für die Template-Dateien korrekt sind."""
    template_paths = [
        "/home/alex/development/drehteller_360_grad_fotos/templates/viewer/overview.html",
        "/home/alex/development/drehteller_360_grad_fotos/templates/viewer/cloudimage_viewer.html"
    ]
    
    for path in template_paths:
        if os.path.exists(path):
            try:
                st = os.stat(path)
                logger.info(f"Datei {path} gefunden:")
                logger.info(f"  Berechtigungen: {oct(st.st_mode)[-3:]}")
                logger.info(f"  Besitzer: {st.st_uid}")
                logger.info(f"  Gruppe: {st.st_gid}")
                logger.info(f"  Größe: {st.st_size} Bytes")
            except Exception as e:
                logger.error(f"Fehler beim Prüfen der Berechtigungen für {path}: {str(e)}")
        else:
            logger.error(f"Template-Datei nicht gefunden: {path}")

def main():
    """Hauptfunktion zur Diagnose des Viewer-Problems."""
    logger.info("=== 360° Viewer Debugging-Skript ===")
    
    # Teste Viewer-Übersicht
    overview_ok = test_viewer_overview_page()
    
    # Teste Cloudimage-Viewer
    cloudimage_ok = test_cloudimage_viewer_route()
    
    # Prüfe Projekt-Existenz
    project_ok = check_project_exists()
    
    # Prüfe Dateiberechtigungen
    check_file_permissions()
    
    # Logdateien prüfen
    check_log_files()
    
    # Zusammenfassung ausgeben
    logger.info("\n=== Zusammenfassung ===")
    logger.info(f"Viewer-Übersicht erreichbar: {'Ja' if overview_ok else 'Nein'}")
    logger.info(f"Cloudimage-Viewer erreichbar: {'Ja' if cloudimage_ok else 'Nein'}")
    logger.info(f"Projekt existiert: {'Ja' if project_ok else 'Nein'}")
    
    if not cloudimage_ok:
        logger.info("\n=== Lösungsvorschläge ===")
        if not project_ok:
            logger.info("1. Projekt existiert nicht oder ist beschädigt.")
            logger.info("   - Stelle sicher, dass das Projekt existiert und Bilder enthält.")
            logger.info("   - Versuche, das Projekt neu zu erstellen.")
        else:
            logger.info("1. Cloudimage-Viewer-Route funktioniert nicht.")
            logger.info("   - Überprüfe den Code der Route-Funktion 'cloudimage_viewer'.")
            logger.info("   - Prüfe, ob die Templates korrekt sind.")
            logger.info("   - Suche in den Logs nach Fehlern beim Laden des Viewers.")

if __name__ == "__main__":
    main()
