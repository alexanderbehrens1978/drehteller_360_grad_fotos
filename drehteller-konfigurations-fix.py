#!/usr/bin/env python3
"""
Konfigurationsmanager-Fix für das 360° Drehteller-System
Dieses Skript implementiert fehlende config_manager.py Funktionen und Routen
"""

import os
import json
import logging
import sys
import shutil
from pathlib import Path

# Logger konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("config_manager_fix.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("config_manager_fix")

# Verbesserte Version von config_manager.py
def create_config_manager():
    """Erstellt eine verbesserte Version der config_manager.py-Datei"""
    config_path = "config_manager.py"
    
    # Backup der alten Datei erstellen, falls vorhanden
    if os.path.exists(config_path):
        backup_path = f"{config_path}.bak"
        logger.info(f"Erstelle Backup der alten config_manager.py: {backup_path}")
        shutil.copy(config_path, backup_path)
    
    improved_content = """import os
import json
import logging

class ConfigManager:
    DEFAULT_CONFIG = {
        'camera': {
            'device_path': '/dev/video0',
            'type': 'webcam',  # or 'gphoto2'
            'resolution': {
                'width': 1280,
                'height': 720
            }
        },
        'arduino': {
            'port': '/dev/ttyACM0',
            'baudrate': 9600
        },
        'rotation': {
            'default_degrees': 15,
            'default_interval': 5
        },
        'simulator': {
            'enabled': True
        }
    }

    def __init__(self, config_path=None):
        \"\"\"Initialize configuration manager
        
        :param config_path: Path to the configuration file
        \"\"\"
        # Determine the project directory
        self.project_dir = os.path.dirname(os.path.abspath(__file__))

        # If no config path provided, use a default in the project directory
        if config_path is None:
            config_path = os.path.join(self.project_dir, 'config.json')

        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        \"\"\"Load configuration from file or create default
        
        :return: Configuration dictionary
        \"\"\"
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            # Try to load existing config
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with default to ensure all keys exist
                    merged_config = self._merge_configs(self.DEFAULT_CONFIG, config)
                    return merged_config
            else:
                # Create default config file
                config = self.DEFAULT_CONFIG
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            # If loading fails, use default config and try to save it
            try:
                with open(self.config_path, 'w') as f:
                    json.dump(self.DEFAULT_CONFIG, f, indent=4)
            except Exception as save_error:
                print(f"Error saving default config: {save_error}")
            return self.DEFAULT_CONFIG

    def save_config(self, new_config=None):
        \"\"\"Save configuration to file
        
        :param new_config: Optional new configuration to save
        \"\"\"
        try:
            # Use provided config or current config
            config_to_save = new_config if new_config is not None else self.config

            # Ensure full path exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            # Save configuration
            with open(self.config_path, 'w') as f:
                json.dump(config_to_save, f, indent=4)

            # Update current config
            if new_config is not None:
                self.config = new_config
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        \"\"\"Get a configuration value
        
        :param key: Dot-separated key (e.g. 'camera.device_path')
        :param default: Default value if key not found
        :return: Configuration value
        \"\"\"
        try:
            # Split the key into parts
            parts = key.split('.')

            # Navigate through nested dictionary
            value = self.config
            for part in parts:
                if part in value:
                    value = value[part]
                else:
                    return default

            # Return value if found, otherwise default
            return value
        except Exception as e:
            print(f"Error getting config value: {e}")
            return default

    def _merge_configs(self, default_config, user_config):
        \"\"\"Merge default config with user config to ensure all keys exist
        
        :param default_config: Default configuration dictionary
        :param user_config: User configuration dictionary
        :return: Merged configuration dictionary
        \"\"\"
        merged_config = default_config.copy()

        for key, value in user_config.items():
            if key in merged_config and isinstance(merged_config[key], dict) and isinstance(value, dict):
                # Recursive merge for nested dictionaries
                merged_config[key] = self._merge_configs(merged_config[key], value)
            else:
                # Use user config value
                merged_config[key] = value

        return merged_config


# Create a global config manager instance
config_manager = ConfigManager()
"""

    # Schreibe verbesserte Version der Datei
    with open(config_path, "w") as f:
        f.write(improved_content)
    
    logger.info(f"Verbesserte config_manager.py erstellt: {config_path}")
    return True

def add_get_config_route():
    """Fügt die fehlende /get_config Route zur web.py-Datei hinzu"""
    web_py_path = "web.py"
    
    if not os.path.exists(web_py_path):
        logger.error(f"Konnte web.py nicht finden: {web_py_path}")
        return False
    
    # Backup der alten Datei erstellen
    backup_path = f"{web_py_path}.bak"
    logger.info(f"Erstelle Backup der alten web.py: {backup_path}")
    shutil.copy(web_py_path, backup_path)
    
    # Dateiinhalt lesen
    with open(web_py_path, "r") as f:
        content = f.read()
    
    # Prüfen, ob die Route bereits existiert
    if "@app.route('/get_config')" in content:
        logger.info("Die Route /get_config existiert bereits")
        return True
    
    # Füge Import für jsonify hinzu, falls noch nicht vorhanden
    if "from flask import" in content and "jsonify" not in content:
        content = content.replace(
            "from flask import", 
            "from flask import jsonify, "
        )
    
    # Füge die Route an einer geeigneten Stelle ein
    # Suche nach einer vorhandenen Route
    route_marker = "@app.route("
    
    if route_marker in content:
        # Finde die Position der letzten Route
        route_positions = [pos for pos in range(len(content)) if content.startswith(route_marker, pos)]
        
        if route_positions:
            # Finde das Ende der letzten Route-Funktion
            last_route_pos = route_positions[-1]
            func_start = content.find("def ", last_route_pos)
            
            if func_start != -1:
                # Finde die nächste leere Zeile nach dieser Funktion
                func_name_end = content.find("(", func_start)
                func_name = content[func_start+4:func_name_end]
                
                # Finde das Ende der Funktion (nächste Funktion oder Ende der Datei)
                next_def = content.find("\ndef ", func_start + 1)
                
                if next_def != -1:
                    insertion_point = next_def
                else:
                    # Wenn keine weitere Funktion gefunden wurde, füge am Ende ein
                    insertion_point = len(content)
                
                # Füge die neue Route ein
                new_route = """

@app.route('/get_config')
def get_config():
    \"\"\"
    Retrieve current configuration
    \"\"\"
    return jsonify(config_manager.config)
"""
                new_content = content[:insertion_point] + new_route + content[insertion_point:]
                
                # Schreibe die aktualisierte Datei
                with open(web_py_path, "w") as f:
                    f.write(new_content)
                
                logger.info("Route /get_config erfolgreich zur web.py hinzugefügt")
                return True
    
    logger.error("Konnte keine geeignete Stelle zum Einfügen der Route finden")
    return False

def create_default_config():
    """Erstellt eine Standardkonfigurationsdatei, falls keine vorhanden ist"""
    config_path = "config.json"
    
    if os.path.exists(config_path):
        logger.info(f"Konfigurationsdatei existiert bereits: {config_path}")
        return True
    
    default_config = {
        'camera': {
            'device_path': '/dev/video0',
            'type': 'webcam',
            'resolution': {
                'width': 1280,
                'height': 720
            }
        },
        'arduino': {
            'port': '/dev/ttyACM0',
            'baudrate': 9600
        },
        'rotation': {
            'default_degrees': 15,
            'default_interval': 5
        },
        'simulator': {
            'enabled': True
        }
    }
    
    try:
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        
        logger.info(f"Standardkonfigurationsdatei erstellt: {config_path}")
        return True
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Konfigurationsdatei: {str(e)}")
        return False

def fix_gitignore():
    """Aktualisiert die .gitignore-Datei, um config.json nicht zu ignorieren"""
    gitignore_path = ".gitignore"
    
    if not os.path.exists(gitignore_path):
        logger.info(f".gitignore-Datei nicht gefunden: {gitignore_path}")
        return True
    
    with open(gitignore_path, "r") as f:
        content = f.read()
    
    # Prüfen, ob config.json ignoriert wird
    if "config.json" in content:
        # Entferne den Eintrag
        lines = content.splitlines()
        new_lines = [line for line in lines if line.strip() != "config.json"]
        
        # Schreibe die aktualisierte Datei
        with open(gitignore_path, "w") as f:
            f.write("\n".join(new_lines))
        
        logger.info("config.json aus .gitignore entfernt")
    else:
        logger.info("config.json wird nicht ignoriert")
    
    return True

def main():
    """Hauptfunktion"""
    logger.info("Starte Konfigurationsmanager-Fix...")
    
    # Erstelle verbesserte Version von config_manager.py
    if create_config_manager():
        logger.info("config_manager.py erfolgreich aktualisiert")
    else:
        logger.error("Fehler beim Aktualisieren von config_manager.py")
    
    # Füge die /get_config Route hinzu
    if add_get_config_route():
        logger.info("Route /get_config erfolgreich hinzugefügt")
    else:
        logger.error("Fehler beim Hinzufügen der Route /get_config")
    
    # Erstelle eine Standardkonfigurationsdatei
    if create_default_config():
        logger.info("Standardkonfigurationsdatei erstellt oder vorhanden")
    else:
        logger.error("Fehler beim Erstellen der Standardkonfigurationsdatei")
    
    # Aktualisiere .gitignore
    if fix_gitignore():
        logger.info(".gitignore erfolgreich aktualisiert oder nicht benötigt")
    else:
        logger.error("Fehler beim Aktualisieren der .gitignore")
    
    logger.info("Konfigurationsmanager-Fix abgeschlossen")
    print("\nKonfigurationsmanager-Fix abgeschlossen. Starten Sie den Flask-Server neu.")

if __name__ == "__main__":
    main()
