import json
import os
import threading

class ConfigManager:
    def __init__(self, config_path='/opt/kioskpi/config.json', default_path='/opt/kioskpi/config/default_config.json'):
        self.config_path = config_path
        self.default_path = default_path
        self.lock = threading.Lock()
        self.config = self._load_config()

    def _load_config(self):
        # Load defaults
        config = {}
        if os.path.exists(self.default_path):
            try:
                with open(self.default_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"Error loading default config: {e}")

        # Load user config and merge
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config.update(user_config)
            except Exception as e:
                print(f"Error loading user config: {e}")

        return config

    def get(self, key, default=None):
        with self.lock:
            return self.config.get(key, default)

    def get_all(self):
        with self.lock:
            return self.config.copy()

    def set(self, key, value):
        with self.lock:
            self.config[key] = value
            self._save_config()

    def update(self, new_config):
        with self.lock:
            self.config.update(new_config)
            self._save_config()

    def _save_config(self):
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
