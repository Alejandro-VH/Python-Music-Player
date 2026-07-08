import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "volume": 0.35,
    "max_gain": 0.7,
    "color": "blue",
    "songs_directory": "Sin carpeta seleccionada"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al leer la configuración: {e}")
        return DEFAULT_CONFIG

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
        print("Configuración guardada correctamente.")
    except Exception as e:
        print(f"Error al guardar la configuración: {e}")