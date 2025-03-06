import os
import json
import logging

# Logger konfigurieren
logger = logging.getLogger("drehteller360.config_manager")

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
        },
        'web': {
            'host': '0.0.0.0',
            'port': 5000,
            'debug': True
        }
    }

    def __init__(self, config_path=None):
        """
        Initialize configuration manager
        
        :param config_path: Path to the configuration file
        """
        # Determine the project directory
        self.project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # If no config path provided, use a default in the project directory
        if config_path is None:
            config_path = os.path.join(self.project_dir, 'config.json')
        
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self):
        """
        Load configuration from file or create default
        
        :return: Configuration dictionary
        """
        try:
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Try to load existing config
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    
                    # Merge with default config 
                    return self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
            else:
                # Create default config file
                config = self.DEFAULT_CONFIG.copy()
                self.save_config(config)
                return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            # If loading fails, use default config and try to save it
            try:
                self.save_config(self.DEFAULT_CONFIG)
            except Exception as save_error:
                logger.error(f"Error saving default config: {save_error}")
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default_config, user_config):
        """
        Recursive merge of configurations
        
        :param default_config: Default configuration
        :param user_config: User configuration
        :return: Merged configuration
        """
        result = default_config.copy()
        
        for key, value in user_config.items():
            # If the value is a dictionary and exists in the default config
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                # Recursively merge
                result[key] = self._merge_configs(result[key], value)
            else:
                # Otherwise overwrite the value
                result[key] = value
                
        return result
    
    def save_config(self, new_config=None):
        """
        Save configuration to file
        
        :param new_config: Optional new configuration to save
        :return: True if successful, False otherwise
        """
        try:
            # Use provided config or current config
            if new_config is not None:
                # Merge with current config to ensure all keys exist
                config_to_save = self._merge_configs(self.config, new_config)
            else:
                config_to_save = self.config
            
            # Ensure full path exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save configuration with proper permissions
            with open(self.config_path, 'w') as f:
                json.dump(config_to_save, f, indent=4)
            
            # Update current config
            self.config = config_to_save
            logger.info(f"Konfiguration erfolgreich gespeichert in {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def get(self, key, default=None):
        """
        Get a configuration value
        
        :param key: Dot-separated key (e.g. 'camera.device_path')
        :param default: Default value if key not found
        :return: Configuration value
        """
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
            
            return value
        except Exception as e:
            logger.error(f"Error getting config value: {e}")
            return default

# Create a global config manager
config_manager = ConfigManager()
