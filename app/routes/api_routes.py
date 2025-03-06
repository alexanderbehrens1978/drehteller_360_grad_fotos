from flask import Blueprint, request, jsonify
import json
import traceback
from app.services.config_manager import config_manager

api_bp = Blueprint('api', __name__)

@api_bp.route('/config')
def get_config():
    """Gibt die aktuelle Konfiguration zurück"""
    return jsonify(config_manager.config)

@api_bp.route('/config', methods=['POST'])
def save_config():
    """Speichert die Konfiguration"""
    try:
        # Check if request contains JSON data
        if not request.is_json:
            print("Request is not JSON")
            return jsonify({"status": "error", "message": "Missing JSON data"}), 400
            
        new_config = request.json
        if not new_config:
            print("Empty JSON data")
            return jsonify({"status": "error", "message": "Empty configuration data"}), 400
        
        print("Received configuration:", json.dumps(new_config, indent=2))
        
        # Use direct file writing instead of config_manager.save_config
        try:
            # Load current config file
            config_path = config_manager.config_path
            
            # Read current config
            with open(config_path, 'r') as f:
                current_config = json.load(f)
            
            # Update configuration with new values
            def update_config(target, source):
                for key, value in source.items():
                    if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                        update_config(target[key], value)
                    else:
                        target[key] = value
            
            # Merge configs
            update_config(current_config, new_config)
            
            # Write back to file
            with open(config_path, 'w') as f:
                json.dump(current_config, f, indent=4)
            
            # Update config_manager's config
            config_manager.config = current_config
            
            print("Configuration saved successfully")
            return jsonify({"status": "success"})
        except Exception as e:
            print("Error saving configuration:", str(e))
            traceback.print_exc()
            return jsonify({"status": "error", "message": f"Error saving config: {str(e)}"}), 500
            
    except Exception as e:
        print("General error:", str(e))
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500
