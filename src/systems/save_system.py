import os
import json
from typing import Dict, Any
from settings import CONTROLLER_BINDINGS_SETTINGS_DEFAULT, HERO_CLASSES
from src.utils.fps_cap import detect_refresh_rate


def _current_unlocked_heroes() -> list[str]:
    return [hero["name"] for hero in HERO_CLASSES]

def _build_default_save() -> Dict[str, Any]:
    return {
        "total_runs": 0,
        "total_kills": 0,
        "total_time_played": 0.0,
        "highest_level": 1,
        "best_time_survived": 0.0,
        "unlocked_heroes": _current_unlocked_heroes(),
        "settings": {
            "music_volume": 0.5,
            "sfx_volume": 0.8,
            "show_fps": False,
            "show_stat_bonuses": True,
            "fps_cap": detect_refresh_rate(),
            "controller_bindings": CONTROLLER_BINDINGS_SETTINGS_DEFAULT,
        },
    }


def _deep_copy(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _deep_copy_default_save() -> Dict[str, Any]:
    return _deep_copy(_build_default_save())


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


def _normalize_save_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Backfill additive save fields that older saves could not have known about."""
    normalized = _deep_copy(data)
    unlocked = normalized.get("unlocked_heroes")
    if not isinstance(unlocked, list):
        normalized["unlocked_heroes"] = _current_unlocked_heroes()
        return normalized

    known_names = _current_unlocked_heroes()
    existing_names = {name for name in unlocked if isinstance(name, str)}
    normalized["unlocked_heroes"] = list(unlocked)
    for hero_name in known_names:
        if hero_name not in existing_names:
            normalized["unlocked_heroes"].append(hero_name)
    return normalized

class SaveSystem:
    def __init__(self):
        self.save_path = "saves/progress.json"
        self.data = self.load()
        self._last_mtime = self._get_save_mtime()

    def _get_save_mtime(self) -> float | None:
        try:
            return os.path.getmtime(self.save_path)
        except FileNotFoundError:
            return None

    def load(self) -> Dict[str, Any]:
        """Load save data from file or return default if not found"""
        defaults = _build_default_save()
        loaded_from_disk = True
        try:
            with open(self.save_path, 'r') as f:
                loaded_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            loaded_data = {}
            loaded_from_disk = False

        merged_data = _merge_save_data(defaults, loaded_data)
        normalized_data = _normalize_save_data(merged_data)
        if loaded_from_disk and normalized_data != merged_data:
            self.save(normalized_data)
        return normalized_data

    def save(self, data: Dict[str, Any]) -> None:
        """Write data to save file, creating directory if needed"""
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        with open(self.save_path, 'w') as f:
            json.dump(data, f, indent=2)
        self._last_mtime = self._get_save_mtime()

    def reload_if_changed(self) -> bool:
        """Reload shared save data when another SaveSystem instance has written it."""
        current_mtime = self._get_save_mtime()
        if current_mtime == self._last_mtime:
            return False

        self.data = self.load()
        self._last_mtime = current_mtime
        return True

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
        return _build_default_save()["settings"][key]

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value and save immediately"""
        self.data.setdefault("settings", {})
        self.data["settings"][key] = value
        self.save(self.data)
