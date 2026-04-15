import json
from pathlib import Path

# Set path to config.json in the project root
ROOT_DIR = Path(__file__).parent.parent.resolve()
CONFIG_PATH = ROOT_DIR / "config.json"

def load_config():
    """Load settings from config.json or return defaults if file is missing."""
    defaults = {
        "mode": "console",
        "email": "",
        "whatsapp": ""
    }
    
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                # Ensure all default keys exist in the loaded config
                return {**defaults, **config}
        return defaults
    except Exception:
        return defaults

def save_config(config_data):
    """Save the updated settings dictionary to config.json."""
    try:
        # Load existing config first to avoid overwriting unrelated settings
        current_config = load_config()
        current_config.update(config_data)
        
        with open(CONFIG_PATH, "w") as f:
            json.dump(current_config, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False