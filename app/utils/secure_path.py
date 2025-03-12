#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app/utils/secure_path.py
Sicherheitsfunktionen für die Pfadverarbeitung
"""

import os
import string
import logging

logger = logging.getLogger(__name__)

def secure_filename(filename):
    """
    Bereinigt einen Dateinamen und entfernt potenziell gefährliche Zeichen.
    Erlaubt nur alphanumerische Zeichen, Bindestrich, Unterstrich und Punkt.
    
    Args:
        filename: Der zu bereinigende Dateiname
        
    Returns:
        Bereinigter Dateiname ohne gefährliche Zeichen
    """
    if not filename:
        return ""
        
    # Extrahiere nur den Dateinamen ohne Pfad
    filename = os.path.basename(filename)
    
    # Erlaube alphanumerische Zeichen und bestimmte Sonderzeichen
    allowed_chars = set(string.ascii_letters + string.digits + '-_.')
    filename = ''.join(c for c in filename if c in allowed_chars)
    
    # Stellen Sie sicher, dass der Dateiname nicht leer ist
    if not filename:
        logger.warning(f"Dateiname wurde zu einer leeren Zeichenfolge bereinigt")
        return "unnamed_file"
        
    return filename

def secure_join(base_path, *paths):
    """
    Verbindet Pfadsegmente sicher und verhindert Verzeichnistraversierungsangriffe.
    
    Args:
        base_path: Der Basispfad, der nicht verlassen werden soll
        *paths: Zu verbindende Pfadsegmente
        
    Returns:
        Ein sicherer absoluter Pfad, der nicht außerhalb des Basispfads liegt
    """
    # Stelle sicher, dass der Basispfad ein absoluter Pfad ist
    base_path = os.path.abspath(base_path)
    
    # Normalisiere alle Pfadsegmente und entferne potenziell gefährliche Teile
    clean_paths = []
    for i, path in enumerate(paths):
        if i == len(paths) - 1 and path:  # Letztes Element könnte ein Dateiname sein
            clean_paths.append(secure_filename(path))
        else:
            # Normalisiere Pfade und entferne '..' und Anführungszeichen
            if path:
                normalized = os.path.normpath(path).replace('..', '').replace('"', '').replace("'", "")
                clean_paths.append(normalized)
    
    # Verbinde den Basispfad mit den bereinigten Pfadsegmenten
    joined_path = os.path.join(base_path, *clean_paths)
    safe_path = os.path.abspath(joined_path)
    
    # Überprüfe, ob der resultierende Pfad innerhalb des Basispfads liegt
    if not safe_path.startswith(base_path):
        logger.warning(f"Versuchter Pfad-Traversal-Angriff verhindert: {joined_path}")
        return base_path
    
    return safe_path

def validate_project_id(project_id):
    """
    Validiert eine Projekt-ID gegen Traversierungsangriffe.
    
    Args:
        project_id: Die zu validierende Projekt-ID
        
    Returns:
        True, wenn die Projekt-ID sicher ist, andernfalls False
    """
    if not project_id or not isinstance(project_id, str):
        return False
        
    # Entferne Leerzeichen am Anfang/Ende
    project_id = project_id.strip()
    
    # Überprüfe auf unerlaubte Zeichen oder Sequenzen
    invalid_sequences = ['..', '/', '\\', '~', '$', '&', '*', '(', ')', '`', "'", '"', '|', '<', '>', ';']
    for seq in invalid_sequences:
        if seq in project_id:
            return False
            
    return len(project_id) > 0
