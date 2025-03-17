#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import subprocess

def zeige_dateien_und_inhalt(verzeichnis, ausgabe_datei, excluded_files=None):
    """
    Durchsucht rekursiv ein Verzeichnis und gibt den Inhalt aller Dateien in eine Ausgabedatei aus,
    außer denjenigen, die in den ausgeschlossenen Verzeichnissen oder Dateien enthalten sind.
    
    :param verzeichnis: Pfad zum zu durchsuchenden Verzeichnis
    :param ausgabe_datei: Dateipfad für die Ausgabe
    :param excluded_files: Liste von Dateinamen, die ausgeschlossen werden sollen
    """
    if excluded_files is None:
        excluded_files = []
    
    excluded_dirs = {'.git', 'bin', '__pycache__', '.idea', 'myenv', 'photos', 'doc', 'static/css', 'logs', 'venv'}
    
    with open(ausgabe_datei, 'w', encoding='utf-8') as ausgabe:
        for root, dirs, files in os.walk(verzeichnis):
            # Entferne ausgeschlossene Verzeichnisse aus der Liste
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                # Prüfe, ob die Datei ausgeschlossen werden soll
                if any(file.endswith(ausschluss.replace('*', '')) for ausschluss in excluded_files):
                    continue
                
                dateipfad = os.path.join(root, file)
                ausgabe.write(f"\n--- Datei: {dateipfad} ---\n")
                
                try:
                    # Versuche, die Datei im UTF-8 Format zu öffnen
                    with open(dateipfad, 'r', encoding='utf-8') as f:
                        inhalt = f.read()
                        ausgabe.write(inhalt)
                        ausgabe.write("\n")
                except Exception as e:
                    ausgabe.write(f"Fehler beim Lesen der Datei: {e}\n")

def main():
    # Aktuelles Verzeichnis (Root des Projekts)
    projekt_root = os.path.dirname(os.path.abspath(__file__))
    
    # Datum und Uhrzeit für Dateinamen
    jetzt = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    
    # Ausgeschlossene Dateien
    excluded_files = ['README.md', '*.log', '.gitignore', '*.txt', '*.jpg', '*.jpeg', '*.png', '*.gif']
    
    # Liste der Verzeichnisse, die durchsucht werden sollen
    verzeichnisse = {
        'app': os.path.join(projekt_root, 'app'),
        'templates': os.path.join(projekt_root, 'templates'),
        'static': os.path.join(projekt_root, 'static')
    }
    
    # Erstellung und Durchführung der Ausgabe für jedes Verzeichnis
    for verzeichnis_name, verzeichnis_pfad in verzeichnisse.items():
        if os.path.exists(verzeichnis_pfad):
            ausgabe_datei = os.path.join(projekt_root, f"{verzeichnis_name}-alles-{jetzt}.txt")
            print(f"Erstelle Ausgabe für {verzeichnis_name} in {ausgabe_datei}...")
            zeige_dateien_und_inhalt(verzeichnis_pfad, ausgabe_datei, excluded_files)
            print(f"Fertig! Ausgabe in {ausgabe_datei} erstellt.")

if __name__ == "__main__":
    main()
