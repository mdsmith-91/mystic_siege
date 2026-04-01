import os
import json
from datetime import datetime
from typing import Dict, Any

from src.utils.resource_loader import ResourceLoader

DEFAULT_SAVE = {
    "total_runs": 0,
    "total_kills": 0,
    "total_time_played": 0.0,
    "highest_level": 1,
    "best_time_survived": 0.0,
    "unlocked_heroes": ["Knight of the Burning Crown"],
    "settings": {
        "music_volume": 0.5,
        "sfx_volume": 0.8,
        "fullscreen": False,
        "show_fps": False
    }
}

class SaveSystem:
    def __init__(self):
        self.save_path = "saves/progress.json"
        self.data = self.load()

    def load(self) -> Dict[str, Any]:
        """Load save data from file or return default if not found"""
        try:
            with open(self.save_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return a copy of the default save if file doesn't exist or is invalid
            return json.loads(json.dumps(DEFAULT_SAVE))

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
        self.data = json.loads(json.dumps(DEFAULT_SAVE))
        self.save(self.data)

    def get_setting(self, key: str) -> Any:
        """Get a setting value"""
        return self.data["settings"][key]

    def set_setting(self, key: str, value: Any) -> None:
        """Set a setting value and save immediately"""
        self.data["settings"][key] = value
        self.save(self.data)