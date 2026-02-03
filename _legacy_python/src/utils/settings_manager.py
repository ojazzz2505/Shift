import json
import os
from .config import Config
from .logger import logger

class SettingsManager:
    """
    Manages persistent settings in a JSON file.
    """
    SETTINGS_FILE = Config.BASE_DIR / "settings.json"
    
    DEFAULT_SETTINGS = {
        "theme": "Dark",
        # Output Maps: "video": "C:/Users/.../Videos", etc.
        "output_paths": {
            "video": "",
            "image": "",
            "document": "",
            "audio": ""
        }
    }
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsManager, cls).__new__(cls)
            cls._instance.data = cls._instance.load_settings()
        return cls._instance

    def load_settings(self):
        if not os.path.exists(self.SETTINGS_FILE):
            logger.info("No settings file found, using defaults.")
            return self.DEFAULT_SETTINGS.copy()
            
        try:
            with open(self.SETTINGS_FILE, "r") as f:
                data = json.load(f)
                # Merge with defaults to ensure new keys exist
                merged = self.DEFAULT_SETTINGS.copy()
                merged.update(data)
                # Deep merge output_paths
                if "output_paths" in data:
                    merged["output_paths"].update(data["output_paths"])
                return merged
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return self.DEFAULT_SETTINGS.copy()

    def save_settings(self):
        try:
            with open(self.SETTINGS_FILE, "w") as f:
                json.dump(self.data, f, indent=4)
            logger.info("Settings saved.")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            
    def get(self, key, default=None):
        return self.data.get(key, default)
        
    def set(self, key, value):
        self.data[key] = value
        self.save_settings()

    def get_output_path(self, file_type):
        """Returns the specific output path for a file type (video, image, etc.) or None if empty."""
        paths = self.data.get("output_paths", {})
        path = paths.get(file_type, "")
        if path and os.path.exists(path):
            return path
        return None
        
    def set_output_path(self, file_type, path):
        if "output_paths" not in self.data:
            self.data["output_paths"] = {}
        self.data["output_paths"][file_type] = path
        self.save_settings()
