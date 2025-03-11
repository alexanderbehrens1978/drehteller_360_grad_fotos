#!/usr/bin/env python3
# Datei: directory_file_lister.py
# Skript zur detaillierten Analyse der Projektstruktur des 360° Drehtellers

import os
import json
import hashlib
from datetime import datetime

class ProjectStructureAnalyzer:
    def __init__(self, base_path):
        """
        Initialisiert den Projektstruktur-Analyzer
        
        :param base_path: Basisverzeichnis für die Analyse
        """
        self.base_path = os.path.abspath(base_path)
        self.ignore_patterns = [
            '.git', '__pycache__', '.vscode', '.idea', 
            'myenv', 'venv', 'env', 'bin', 
            '.DS_Store', 'Thumbs.db'
        ]
        self.report = {
            'meta': {
                'analyzed_path': self.base_path,
                'analysis_timestamp': datetime.now().isoformat(),
                'total_files': 0,
                'total_directories': 0,
                'file_types': {},
                'directory_structure': {}
            },
            'files': [],
            'directories': []
        }

    def should_ignore(self, path):
        """
        Prüft, ob ein Pfad ignoriert werden soll
        
        :param path: Zu prüfender Pfad
        :return: True wenn ignoriert, False sonst
        """
        return any(ignored in path.split(os.path.sep) for ignored in self.ignore_patterns)

    def calculate_file_hash(self, filepath):
        """
        Berechnet MD5-Hash einer Datei
        
        :param filepath: Pfad zur Datei
        :return: MD5-Hash als Hexadezimalstring
        """
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except (IOError, PermissionError):
            return 'UNREADABLE'

    def analyze_directory(self, path=None):
        """
        Analysiert rekursiv das Verzeichnis
        
        :param path: Zu analysierendes Verzeichnis (Standard: Basisverzeichnis)
        """
        if path is None:
            path = self.base_path

        try:
            for item in os.scandir(path):
                if self.should_ignore(item.path):
                    continue

                if item.is_dir(follow_symlinks=False):
                    # Verzeichnis-Analyse
                    dir_info = {
                        'path': os.path.relpath(item.path, self.base_path),
                        'name': item.name,
                        'created': item.stat().st_ctime,
                        'modified': item.stat().st_mtime
                    }
                    self.report['directories'].append(dir_info)
                    self.report['meta']['total_directories'] += 1
                    self.report['meta']['directory_structure'][dir_info['path']] = []

                    # Rekursive Analyse von Unterverzeichnissen
                    self.analyze_directory(item.path)

                elif item.is_file(follow_symlinks=False):
                    # Datei-Analyse
                    file_info = {
                        'path': os.path.relpath(item.path, self.base_path),
                        'name': item.name,
                        'size': item.stat().st_size,
                        'created': item.stat().st_ctime,
                        'modified': item.stat().st_mtime,
                        'hash': self.calculate_file_hash(item.path)
                    }

                    # Dateityp-Statistik
                    file_ext = os.path.splitext(item.name)[1].lower()
                    self.report['meta']['file_types'][file_ext] = \
                        self.report['meta']['file_types'].get(file_ext, 0) + 1

                    self.report['files'].append(file_info)
                    self.report['meta']['total_files'] += 1

        except PermissionError:
            print(f"Keine Berechtigung für Verzeichnis: {path}")

    def generate_report(self, output_file=None):
        """
        Generiert einen detaillierten Bericht
        
        :param output_file: Optionale Ausgabedatei für den Bericht
        :return: JSON-formatierter Bericht
        """
        report_json = json.dumps(self.report, indent=2)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_json)
        
        return report_json

def main():
    # Projektverzeichnis ermitteln
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Analyzer initialisieren
    analyzer = ProjectStructureAnalyzer(project_dir)
    
    # Verzeichnisstruktur analysieren
    print(f"Analysiere Projekt im Verzeichnis: {project_dir}")
    analyzer.analyze_directory()
    
    # Bericht generieren
    report_file = os.path.join(project_dir, 'projekt_struktur_bericht.json')
    report = analyzer.generate_report(report_file)
    
    # Zusammenfassung ausgeben
    print("\n--- Projekt-Struktur-Zusammenfassung ---")
    print(f"Gesamtzahl Dateien: {analyzer.report['meta']['total_files']}")
    print(f"Gesamtzahl Verzeichnisse: {analyzer.report['meta']['total_directories']}")
    print("\nDateitypen:")
    for ext, count in analyzer.report['meta']['file_types'].items():
        print(f"  {ext or 'Ohne Erweiterung'}: {count}")
    
    print(f"\nDetaillierter Bericht gespeichert in: {report_file}")

if __name__ == '__main__':
    main()
