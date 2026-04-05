import os
import json
from typing import Dict, Any
from settings import CONTROLLER_BINDINGS_SETTINGS_DEFAULT

DEFAULT_SAVE = {
    "total_runs": 0,
    "total_kills": 0,
    "total_time_played": 0.0,
    "highest_level": 1,
    "best_time_survived": 0.0,
    "unlocked_heroes": ["Knight", "Wizard", "Friar"],
    "settings": {
        "music_volume": 0.5,
        "sfx_volume": 0.8,
        "show_fps": False,
        "controller_bindings": CONTROLLER_BINDINGS_SETTINGS_DEFAULT,
    }
}


def _deep_copy(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _deep_copy_default_save() -> Dict[str, Any]:
    return _deep_copy(DEFAULT_SAVE)


def _merge_save_data(defaults: Dict[str, Any], loaded: Any) -> Dict[str, Any]:
    """Merge loaded save data onto defaults without dropping new fields."""
    if not isinstance(loaded, dict):
        return _deep_copy(defaults)

    merged = _deep_copy(defaults)
    for key, loaded_value in loaded.items():
        default_value = defaults.get(key)
        if isinstance(default_value, dict) and isinstance(loaded_value, dict):
            merged[key] = _merge_save_data(default_value, loaded_value)
        elif key in defaults:
            merged[key] = loaded_value
        else:
            merged[key] = _deep_copy(loaded_value)
    return merged

class SaveSystem:
    def __init__(self):
        self.save_path = "saves/progress.json"
        self.data = self.load()

    def load(self) -> Dict[str, Any]:
        """Load save data from file or return default if not found"""
        try:
            with open(self.save_path, 'r') as f:
                loaded_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            loaded_data = {}

        return _merge_save_data(DEFAULT_SAVE, loaded_data)

    def save(self, data: Dict[str, Any]) -> None:
        """Write data to save file, creating directory if needed"""
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        with open(self.save_path, 'w') as f:
            json.dump(data, f, indent=2)

    def update_after_run(self, run_result: Dict[str, Any]) -> None:
        """Update persistent stats based on run result and save"""
        # Update run count
        self.data["total_runs"] += 1

        # Update kills
        self.data["total_kills"] += run_result["kills"]

        # Update time played
        self.data["total_time_played"] += run_result["time_survived"]

        # Update highest level reached
        if run_result["level"] > self.data["highest_level"]:
            self.data["highest_level"] = run_result["level"]

        # Update best time survived
        if run_result["time_survived"] > self.data["best_time_survived"]:
            self.data["best_time_survived"] = run_result["time_survived"]

        # Save updated data
        self.save(self.data)

    def reset(self) -> None:
        """Reset save data to default"""
        self.data = _deep_copy_default_save()
        self.save(self.data)

    def get_setting(self, key: str) -> Any:
        """Get a setting value"""
        settings = self.data.get("settings", {})
        if key in settings:
            return settings[key]
        return DEFAULT_SAVE["settings"][key]

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value and save immediately"""
        self.data.setdefault("settings", {})
        self.data["settings"][key] = value
        self.save(self.data)
