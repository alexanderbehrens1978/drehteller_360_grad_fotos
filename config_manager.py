import os
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
        """Initialize configuration manager
        
        :param config_path: Path to the configuration file
        """
        # Determine the project directory
        self.project_dir = os.path.dirname(os.path.abspath(__file__))

        # If no config path provided, use a default in the project directory
        if config_path is None:
            config_path = os.path.join(self.project_dir, 'config.json')

        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        """Load configuration from file or create default
        
        :return: Configuration dictionary
        """
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
        """Save configuration to file
        
        :param new_config: Optional new configuration to save
        """
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
        """Get a configuration value
        
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

            # Return value if found, otherwise default
            return value
        except Exception as e:
            print(f"Error getting config value: {e}")
            return default

    def _merge_configs(self, default_config, user_config):
        """Merge default config with user config to ensure all keys exist
        
        :param default_config: Default configuration dictionary
        :param user_config: User configuration dictionary
        :return: Merged configuration dictionary
        """
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
