"""
Verwendung des Import-Trackers
Mit diesem Skript kannst du nachverfolgen, welche Python-Dateien geladen werden, wenn du deine run.py ausführst. Du kannst auch bestimmte Ordner vom Tracking ausschließen.
Grundlegende Verwendung:
bashKopierenpython import_tracker.py run.py
Mit Ausschluss bestimmter Verzeichnisse:
bashKopierenpython import_tracker.py run.py --exclude /pfad/zu/ordner1 --exclude /pfad/zu/ordner2
Ausgabe in eine Datei schreiben:
bashKopierenpython import_tracker.py run.py --output importierte_dateien.txt
Ausführliche Ausgabe während der Ausführung:
bashKopierenpython import_tracker.py run.py --verbose
So funktioniert es:

Das Skript nutzt Python's eigenes Import-System, um alle geladenen Module zu erfassen
Es umgeht das standardmäßige Import-System durch einen eigenen MetaPathFinder
Beim Import einer Datei wird überprüft, ob sie in einem ausgeschlossenen Verzeichnis liegt
Am Ende wird eine sortierte Liste aller importierten Dateien ausgegeben

Der Vorteil dieses Ansatzes ist, dass du die Anwendung normal ausführen kannst und trotzdem alle Importe nachverfolgst.
Gibt es noch spezifische Anforderungen an das Skript, die ich berücksichtigen sollte?
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import-Tracker: Verfolgt alle importierten Module beim Ausführen eines Python-Skripts
"""

import sys
import os
import importlib.abc
import importlib.machinery
import runpy
import argparse
import time

class ImportTracker(importlib.abc.MetaPathFinder):
    """
    Ein MetaPathFinder, der alle Import-Operationen nachverfolgt und protokolliert
    """
    
    def __init__(self, exclude_dirs=None):
        self.imported_files = set()
        self.exclude_dirs = set() if exclude_dirs is None else set(os.path.abspath(d) for d in exclude_dirs)
        self.original_meta_path = sys.meta_path.copy()
        
    def find_spec(self, fullname, path, target=None):
        # Wir delegieren an die ursprünglichen Finder
        for finder in self.original_meta_path:
            try:
                spec = finder.find_spec(fullname, path, target)
                if spec is not None:
                    # Wenn eine Quelldatei gefunden wurde und sie nicht in einem ausgeschlossenen Verzeichnis liegt
                    if spec.origin and os.path.isfile(spec.origin) and spec.origin.endswith(('.py', '.pyc', '.pyo')):
                        abs_path = os.path.abspath(spec.origin)
                        
                        # Überprüfen, ob der Pfad in einem ausgeschlossenen Verzeichnis liegt
                        if not any(abs_path.startswith(excluded_dir) for excluded_dir in self.exclude_dirs):
                            self.imported_files.add(abs_path)
                    
                    return spec
            except (AttributeError, ImportError):
                continue
        
        return None

    def start_tracking(self):
        """Aktiviert das Import-Tracking"""
        sys.meta_path = [self] + sys.meta_path
        
    def stop_tracking(self):
        """Deaktiviert das Import-Tracking"""
        sys.meta_path = self.original_meta_path
        
    def get_imported_files(self):
        """Gibt die Liste der importierten Dateien zurück"""
        return sorted(self.imported_files)


def main():
    # Kommandozeilen-Argumente parsen
    parser = argparse.ArgumentParser(description='Verfolgt importierte Python-Module beim Ausführen eines Skripts.')
    parser.add_argument('script', help='Der Pfad zum auszuführenden Python-Skript (z.B. run.py)')
    parser.add_argument('--exclude', '-e', action='append', default=[], 
                        help='Verzeichnisse, die vom Tracking ausgeschlossen werden sollen (mehrfach verwendbar)')
    parser.add_argument('--output', '-o', help='Ausgabedatei für die Liste der importierten Module')
    parser.add_argument('--verbose', '-v', action='store_true', help='Ausführliche Ausgabe während der Ausführung')
    
    args = parser.parse_args()
    
    # Überprüfen, ob das angegebene Skript existiert
    script_path = os.path.abspath(args.script)
    if not os.path.isfile(script_path):
        print(f"Fehler: Die Datei '{args.script}' wurde nicht gefunden.")
        sys.exit(1)
        
    # Das Verzeichnis des Skripts zum Suchpfad hinzufügen
    script_dir = os.path.dirname(script_path)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
        
    # Ausgeschlossene Verzeichnisse vorbereiten
    exclude_dirs = []
    for exclude_path in args.exclude:
        abs_exclude = os.path.abspath(exclude_path)
        if not os.path.isdir(abs_exclude):
            print(f"Warnung: Ausgeschlossenes Verzeichnis '{exclude_path}' existiert nicht oder ist kein Verzeichnis.")
        exclude_dirs.append(abs_exclude)
    
    if args.verbose:
        print(f"Starte Ausführung von: {script_path}")
        print(f"Ausgeschlossene Verzeichnisse: {exclude_dirs}")
        
    # Import-Tracker einrichten
    tracker = ImportTracker(exclude_dirs=exclude_dirs)
    tracker.start_tracking()
    
    start_time = time.time()
    
    try:
        # Skript ausführen
        sys.argv = [script_path]  # Setze sys.argv[0] auf den Skriptpfad
        runpy.run_path(script_path, run_name='__main__')
    except Exception as e:
        print(f"Fehler beim Ausführen des Skripts: {e}")
    finally:
        tracker.stop_tracking()
        
    end_time = time.time()
    
    # Ergebnisse anzeigen
    imported_files = tracker.get_imported_files()
    
    if args.verbose:
        print(f"\nAusführung abgeschlossen in {end_time - start_time:.2f} Sekunden")
        print(f"Insgesamt wurden {len(imported_files)} Dateien importiert.\n")
    
    output_lines = [f"# Importierte Dateien von {os.path.basename(script_path)} - {time.strftime('%Y-%m-%d %H:%M:%S')}"]
    for file_path in imported_files:
        rel_path = os.path.relpath(file_path, os.getcwd())
        output_lines.append(rel_path)
    
    if args.output:
        # In Datei schreiben
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        if args.verbose:
            print(f"Importierte Dateien wurden in '{args.output}' gespeichert.")
    else:
        # Auf Konsole ausgeben
        print('\n'.join(output_lines))
    
    
if __name__ == "__main__":
    main()
