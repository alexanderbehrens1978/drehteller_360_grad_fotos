#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bereinigungsskript für 360° Drehteller-Anwendung
Entfernt ungenutzte Funktionen, Variablen und Konstanten

Dieses Skript analysiert Python-Dateien und entfernt ungenutzte Elemente.
"""

import os
import re
import glob
import ast
from collections import defaultdict
import sys

# Verzeichnispfad (passe an, falls nötig)
BASE_DIR = "/d360/dev"
if not os.path.exists(BASE_DIR):
    BASE_DIR = os.getcwd()

# Logs einrichten
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Funktion, um alle Python-Dateien im Projekt zu finden
def find_python_files():
    python_files = []
    for root, _, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                # Virtuelle Umgebung ausschließen
                if 'myenv' not in full_path and 'venv' not in full_path:
                    python_files.append(full_path)
    return python_files

# Ungenutzte Konstanten erkennen
def find_unused_constants(files):
    # Erkannte Konstanten
    constants = {}
    constant_usage = defaultdict(int)
    
    # Regex für Konstanten (Großbuchstaben mit Unterstrichen)
    constant_pattern = re.compile(r'\b([A-Z][A-Z0-9_]+)\b')
    
    # Konstanten finden
    for file_path in files:
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                content = file.read()
                
                # Konstanten-Definitionen finden
                for match in constant_pattern.finditer(content):
                    const_name = match.group(1)
                    # Ignoriere bekannte Standard-Konstanten
                    if const_name in ('__NAME__', '__MAIN__', 'DEBUG', 'TRUE', 'FALSE'):
                        continue
                    # Zähle die Verwendung (inkl. Definition)
                    constant_usage[const_name] += 1
                    if const_name not in constants:
                        constants[const_name] = file_path
            except UnicodeDecodeError:
                logger.warning(f"Konnte {file_path} nicht lesen (Encodierungsproblem)")
    
    # Ungenutzte Konstanten (die nur einmal vorkommen - die Definition selbst)
    unused_constants = {const: file for const, file in constants.items() 
                         if constant_usage[const] <= 1}
    
    return unused_constants

# Ungenutzte Funktionen erkennen
def find_unused_functions(files):
    functions_defined = {}  # {function_name: file_path}
    functions_used = set()
    
    # Erst alle Funktionsdefinitionen sammeln
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                try:
                    # AST-Analyse für Funktionen
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            func_name = node.name
                            # Ignoriere spezielle Methoden und Flask-Routen
                            if (func_name.startswith('__') or 
                                func_name in ('create_app', 'index') or
                                any(decorator.id == 'route' for decorator in node.decorator_list 
                                    if isinstance(decorator, ast.Name))):
                                continue
                            functions_defined[func_name] = file_path
                except SyntaxError:
                    logger.warning(f"Syntaxfehler in {file_path}, überspringe AST-Analyse")
                    
                # Funktionsaufrufe finden (einfache Textsuche)
                function_calls = re.findall(r'(\w+)\(', content)
                functions_used.update(function_calls)
        except Exception as e:
            logger.error(f"Fehler beim Analysieren von {file_path}: {e}")
    
    # Ungenutzte Funktionen identifizieren
    unused_functions = {func: file for func, file in functions_defined.items() 
                        if func not in functions_used and not func.startswith('_')}
    
    return unused_functions

# Ungenutzte Variablen erkennen (einfache Methode)
def find_unused_variables(files):
    unused_vars = {}
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # AST-Analyse für Variablen
                try:
                    tree = ast.parse(content)
                    defined_vars = set()
                    used_vars = set()
                    
                    # Variablendefinitionen sammeln
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    defined_vars.add(target.id)
                        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                            used_vars.add(node.id)
                    
                    # Ungenutzte Variablen identifizieren
                    for var in defined_vars:
                        if var not in used_vars and not var.startswith('_'):
                            unused_vars[var] = file_path
                except SyntaxError:
                    logger.warning(f"Syntaxfehler in {file_path}, überspringe Variable-Analyse")
        except Exception as e:
            logger.error(f"Fehler beim Analysieren von Variablen in {file_path}: {e}")
    
    return unused_vars

# Erkannte ungenutzte Elemente aus den Dateien entfernen
def remove_unused_elements(unused_constants, unused_functions, unused_variables):
    modified_files = set()
    
    # Verarbeite Dateien, die ungenutzte Elemente enthalten
    all_files = set(unused_constants.values()).union(
               set(unused_functions.values())).union(
               set(unused_variables.values()))
    
    for file_path in all_files:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                original_content = content
                
                # Ungenutzte Konstanten entfernen
                for const in [c for c, f in unused_constants.items() if f == file_path]:
                    # Konstanten-Definition entfernen (ganze Zeile)
                    pattern = re.compile(r'^\s*' + const + r'\s*=.*$', re.MULTILINE)
                    content = pattern.sub('', content)
                    logger.info(f"Entferne Konstante {const} aus {file_path}")
                
                # Ungenutzte Funktionen entfernen
                for func in [f for f, path in unused_functions.items() if path == file_path]:
                    # Erkenne Funktionsdefinition und den gesamten Funktionskörper
                    try:
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef) and node.name == func:
                                start_line = node.lineno - 1  # 0-basierter Index
                                end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line
                                
                                # Extrahiere Zeilen vor und nach der Funktion
                                lines = content.split('\n')
                                before = '\n'.join(lines[:start_line])
                                after = '\n'.join(lines[end_line:])
                                
                                # Füge Zeilen wieder zusammen, ohne die Funktion
                                content = before + '\n' + after
                                logger.info(f"Entferne Funktion {func} aus {file_path}")
                                break
                    except SyntaxError:
                        logger.warning(f"Konnte Funktion {func} nicht entfernen (Syntaxfehler in {file_path})")
                
                # Ungenutzte Variablen entfernen ist komplex, da wir den Kontext beachten müssen
                # Hier verzichten wir auf die automatische Entfernung von Variablen
                # und geben stattdessen eine Warnung aus
                for var in [v for v, path in unused_variables.items() if path == file_path]:
                    logger.info(f"Ungenutzte Variable gefunden: {var} in {file_path}")
                
                # Datei nur aktualisieren, wenn sich etwas geändert hat
                if content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(content)
                    modified_files.add(file_path)
        except Exception as e:
            logger.error(f"Fehler beim Bereinigen von {file_path}: {e}")
    
    return modified_files

def main():
    logger.info("Starte Bereinigung des 360° Drehteller Codes...")
    
    # Python-Dateien finden
    python_files = find_python_files()
    logger.info(f"{len(python_files)} Python-Dateien gefunden")
    
    # Ungenutzte Elemente finden
    logger.info("Suche nach ungenutzten Konstanten...")
    unused_constants = find_unused_constants(python_files)
    logger.info(f"{len(unused_constants)} ungenutzte Konstanten gefunden")
    
    logger.info("Suche nach ungenutzten Funktionen...")
    unused_functions = find_unused_functions(python_files)
    logger.info(f"{len(unused_functions)} ungenutzte Funktionen gefunden")
    
    logger.info("Suche nach ungenutzten Variablen...")
    unused_variables = find_unused_variables(python_files)
    logger.info(f"{len(unused_variables)} möglicherweise ungenutzte Variablen gefunden")
    
    # Ungenutzte Konstanten und Funktionen anzeigen
    if unused_constants:
        logger.info("Ungenutzte Konstanten:")
        for const, file in unused_constants.items():
            logger.info(f"  {const} in {os.path.relpath(file, BASE_DIR)}")
    
    if unused_functions:
        logger.info("Ungenutzte Funktionen:")
        for func, file in unused_functions.items():
            logger.info(f"  {func}() in {os.path.relpath(file, BASE_DIR)}")
    
    # Bereinigung durchführen
    modified_files = remove_unused_elements(unused_constants, unused_functions, unused_variables)
    
    logger.info(f"Bereinigung abgeschlossen. {len(modified_files)} Dateien wurden modifiziert:")
    for file in modified_files:
        logger.info(f"  {os.path.relpath(file, BASE_DIR)}")

if __name__ == "__main__":
    main()
