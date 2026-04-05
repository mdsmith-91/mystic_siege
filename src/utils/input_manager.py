import pygame
from settings import (
    CONTROLLER_DEADZONE,
    CONTROLLER_AXIS_REPEAT_DELAY,
    CONTROLLER_AXIS_REPEAT_RATE,
    CONTROLLER_BINDINGS_DEFAULT,
    CONTROLLER_BINDINGS_SETTINGS_DEFAULT,
)
from src.systems.save_system import SaveSystem


class InputManager:
    """Singleton that bridges controller input to the rest of the game."""

    _instance: "InputManager | None" = None

    @classmethod
    def instance(cls) -> "InputManager":
        if cls._instance is None:
            cls._instance = InputManager()
        return cls._instance

    def __init__(self) -> None:
        self._save_system = SaveSystem()
        self._joysticks: dict[int, pygame.joystick.Joystick] = {}
        self._joystick_meta: dict[int, dict] = {}
        self._binding_data = self._load_bindings()
        self._axis_dir: dict[tuple[int, int], int] = {}
        self._axis_timer: dict[tuple[int, int], float] = {}
        self._hat_state: dict[tuple[int, int], tuple[int, int]] = {}
        self._button_state: dict[tuple[int, int], bool] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self) -> None:
        """Enumerate joysticks already connected at startup."""
        for i in range(pygame.joystick.get_count()):
            joy = pygame.joystick.Joystick(i)
            self._register_joystick(joy)

    def reload_bindings(self) -> None:
        """Reload controller bindings from persisted settings."""
        self._save_system = SaveSystem()
        self._binding_data = self._load_bindings()
        for joy in self._joysticks.values():
            self._register_joystick(joy)

    def get_binding(self, action: str, *, joystick_id: int | None = None, profile_key: str | None = None) -> int | list[int]:
        """Return the normalized binding for a controller action."""
        binding = self._resolve_bindings(joystick_id=joystick_id, profile_key=profile_key)[action]
        return list(binding) if isinstance(binding, list) else binding

    def describe_binding(self, action: str, *, joystick_id: int | None = None, profile_key: str | None = None) -> str:
        """Human-readable button label for settings and hints."""
        binding = self.get_binding(action, joystick_id=joystick_id, profile_key=profile_key)
        if isinstance(binding, list):
            if not binding:
                return "Unbound"
            if len(binding) == 1:
                return f"Btn {binding[0]}"
            return ", ".join(f"Btn {button}" for button in binding)
        return f"Btn {binding}"

    def set_binding(
        self,
        action: str,
        button: int,
        *,
        joystick_id: int | None = None,
        profile_key: str | None = None,
    ) -> None:
        """Persist and activate a controller binding override."""
        target_key = self._resolve_profile_key(joystick_id=joystick_id, profile_key=profile_key)
        if target_key is None:
            target = self._binding_data["global_bindings"]
        else:
            target = self._binding_data["profiles"].setdefault(
                target_key,
                {
                    "guid": self._guid_for_profile_key(target_key),
                    "name": self._name_for_profile_key(target_key),
                    "bindings": self._normalized_default_bindings(),
                },
            )["bindings"]

            meta = self._profile_metadata_for_key(target_key)
            if meta is not None:
                self._binding_data["profiles"][target_key]["guid"] = meta.get("guid")
                self._binding_data["profiles"][target_key]["name"] = meta.get("name")

        target[action] = [button] if action == "start" else button
        self._save_system.set_setting("controller_bindings", self._binding_data)
        self.reload_bindings()

    def reset_bindings(self, *, joystick_id: int | None = None, profile_key: str | None = None) -> None:
        """Restore controller bindings for the selected scope and persist them."""
        target_key = self._resolve_profile_key(joystick_id=joystick_id, profile_key=profile_key)
        if target_key is None:
            self._binding_data["global_bindings"] = self._normalized_default_bindings()
        else:
            profile = self._binding_data["profiles"].get(target_key)
            if profile is None:
                profile = {
                    "guid": self._guid_for_profile_key(target_key),
                    "name": self._name_for_profile_key(target_key),
                    "bindings": self._normalized_default_bindings(),
                }
                self._binding_data["profiles"][target_key] = profile
            else:
                profile["bindings"] = self._normalized_default_bindings()
        self._save_system.set_setting("controller_bindings", self._binding_data)
        self.reload_bindings()

    def button_matches(
        self,
        action: str,
        button: int,
        *,
        joystick_id: int | None = None,
        profile_key: str | None = None,
    ) -> bool:
        """Return True if the raw button matches the configured action binding."""
        binding = self._resolve_bindings(joystick_id=joystick_id, profile_key=profile_key)[action]
        if isinstance(binding, list):
            return button in binding
        return button == binding

    def get_synthetic_keys_for_button(
        self,
        button: int,
        *,
        joystick_id: int | None = None,
        profile_key: str | None = None,
    ) -> set[int]:
        """Return synthetic menu keys emitted for a raw controller button."""
        keys: set[int] = set()
        if self.button_matches("confirm", button, joystick_id=joystick_id, profile_key=profile_key):
            keys.add(pygame.K_RETURN)
        if self.button_matches("back", button, joystick_id=joystick_id, profile_key=profile_key):
            keys.add(pygame.K_ESCAPE)
        if self.button_matches("start", button, joystick_id=joystick_id, profile_key=profile_key):
            keys.add(pygame.K_ESCAPE)
        return keys

    def get_connected_controller_details(self) -> list[dict]:
        """Return connected controller metadata for diagnostics/readouts."""
        return [
            {
                "instance_id": instance_id,
                "name": meta["name"],
                "guid": meta["guid"],
                "profile_key": meta["profile_key"],
                "buttons": meta["buttons"],
            }
            for instance_id, meta in sorted(self._joystick_meta.items())
        ]

    def get_binding_profile_options(self) -> list[dict]:
        """Return available binding profile targets for the settings UI."""
        options = [{
            "profile_key": None,
            "display_name": "Global Default",
            "name": "Global Default",
            "guid": None,
            "is_connected": False,
            "connected_instance_ids": [],
            "is_global": True,
        }]

        merged: dict[str, dict] = {}
        for key, profile in self._binding_data["profiles"].items():
            canonical_key = self._canonical_profile_key(key)
            option = merged.setdefault(canonical_key, {
                "profile_key": canonical_key,
                "display_name": profile.get("name") or key,
                "name": profile.get("name") or key,
                "guid": profile.get("guid"),
                "is_connected": False,
                "connected_instance_ids": [],
                "is_global": False,
            })
            if option.get("guid") is None and profile.get("guid") is not None:
                option["guid"] = profile.get("guid")
            if option.get("name") == canonical_key and profile.get("name"):
                option["name"] = profile.get("name")
                option["display_name"] = profile.get("name")

        for instance_id, meta in self._joystick_meta.items():
            key = self._canonical_profile_key(meta["profile_key"])
            option = merged.setdefault(
                key,
                {
                    "profile_key": key,
                    "display_name": meta["name"],
                    "name": meta["name"],
                    "guid": meta["guid"],
                    "is_connected": False,
                    "connected_instance_ids": [],
                    "is_global": False,
                },
            )
            option["is_connected"] = True
            option["connected_instance_ids"].append(instance_id)
            option["display_name"] = meta["name"]
            option["name"] = meta["name"]
            if meta["guid"] is not None:
                option["guid"] = meta["guid"]

        profiles = sorted(
            merged.values(),
            key=lambda option: (option["name"].lower(), option["profile_key"] or ""),
        )
        options.extend(profiles)
        return options

    def get_connected_instance_ids_for_profile(self, profile_key: str | None) -> list[int]:
        """Return live connected controller instance IDs for the given profile key."""
        if profile_key is None:
            return []

        canonical_key = self._canonical_profile_key(profile_key)
        instance_ids: list[int] = []
        for instance_id, meta in self._joystick_meta.items():
            meta_key = self._canonical_profile_key(meta["profile_key"])
            if meta_key == canonical_key or canonical_key in meta["candidate_keys"]:
                instance_ids.append(instance_id)
        return instance_ids

    def canonicalize_profile_key(self, profile_key: str | None) -> str | None:
        """Return the canonical storage key for a controller profile."""
        if profile_key is None:
            return None
        return self._canonical_profile_key(profile_key)

    def ensure_profile_bindings(
        self,
        *,
        joystick_id: int | None = None,
        profile_key: str | None = None,
    ) -> dict | None:
        """Materialize a controller profile by copying the current global bindings."""
        target_key = self._resolve_profile_key(joystick_id=joystick_id, profile_key=profile_key)
        if target_key is None:
            return None

        existing = self._binding_data["profiles"].get(target_key)
        if existing is not None:
            return existing

        meta = self._profile_metadata_for_key(target_key)
        profile = {
            "guid": meta.get("guid") if meta is not None else self._guid_for_profile_key(target_key),
            "name": meta.get("name") if meta is not None else self._name_for_profile_key(target_key),
            "bindings": self._normalize_simple_bindings(self._binding_data["global_bindings"]),
        }
        self._binding_data["profiles"][target_key] = profile
        self._save_system.set_setting("controller_bindings", self._binding_data)
        self.reload_bindings()
        return self._binding_data["profiles"].get(target_key)

    def update(self, dt: float, events: list) -> None:
        """Process events and tick controller state. Call once per frame."""
        for event in events:
            if event.type == pygame.JOYDEVICEADDED:
                joy = pygame.joystick.Joystick(event.device_index)
                self._register_joystick(joy)
            elif event.type == pygame.JOYDEVICEREMOVED:
                iid = event.instance_id
                self._joysticks.pop(iid, None)
                self._joystick_meta.pop(iid, None)
                self._axis_dir = {k: v for k, v in self._axis_dir.items() if k[0] != iid}
                self._axis_timer = {k: v for k, v in self._axis_timer.items() if k[0] != iid}
                self._hat_state = {k: v for k, v in self._hat_state.items() if k[0] != iid}
                self._button_state = {k: v for k, v in self._button_state.items() if k[0] != iid}

        for joy in self._joysticks.values():
            self._process_axes(joy, dt)
            self._process_hats(joy)
            self._process_buttons(joy)

    def get_movement(self) -> tuple[float, float]:
        for joy in self._joysticks.values():
            if joy.get_numaxes() < 2:
                continue
            x = joy.get_axis(0)
            y = joy.get_axis(1)
            x = x if abs(x) >= CONTROLLER_DEADZONE else 0.0
            y = y if abs(y) >= CONTROLLER_DEADZONE else 0.0
            if x != 0.0 or y != 0.0:
                return (x, y)
        return (0.0, 0.0)

    def get_movement_for_joystick(self, joystick_id: int) -> tuple[float, float]:
        joy = self._joysticks.get(joystick_id)
        if joy is None or joy.get_numaxes() < 2:
            return (0.0, 0.0)
        x = joy.get_axis(0)
        y = joy.get_axis(1)
        x = x if abs(x) >= CONTROLLER_DEADZONE else 0.0
        y = y if abs(y) >= CONTROLLER_DEADZONE else 0.0
        return (x, y)

    def get_menu_navigation_for_joystick(self, joystick_id: int) -> tuple[int, int]:
        joy = self._joysticks.get(joystick_id)
        if joy is None:
            return (0, 0)

        x_dir = 0
        y_dir = 0

        if joy.get_numaxes() >= 2:
            raw_x = joy.get_axis(0)
            raw_y = joy.get_axis(1)
            if raw_x <= -CONTROLLER_DEADZONE:
                x_dir = -1
            elif raw_x >= CONTROLLER_DEADZONE:
                x_dir = 1
            if raw_y <= -CONTROLLER_DEADZONE:
                y_dir = -1
            elif raw_y >= CONTROLLER_DEADZONE:
                y_dir = 1

        for hat_idx in range(joy.get_numhats()):
            hat_x, hat_y = joy.get_hat(hat_idx)
            if hat_x != 0:
                x_dir = hat_x
            if hat_y != 0:
                y_dir = -hat_y

        return (x_dir, y_dir)

    def get_confirm_for_joystick(self, joystick_id: int) -> bool:
        joy = self._joysticks.get(joystick_id)
        confirm_button = self._resolve_bindings(joystick_id=joystick_id)["confirm"]
        if not isinstance(confirm_button, int):
            return False
        if joy is None or joy.get_numbuttons() <= confirm_button:
            return False
        return bool(joy.get_button(confirm_button))

    def is_joystick_connected(self, joystick_id: int) -> bool:
        return joystick_id in self._joysticks

    def get_connected_joysticks(self) -> list[int]:
        return list(self._joysticks.keys())

    @property
    def connected(self) -> bool:
        return bool(self._joysticks)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_bindings(self) -> dict:
        saved = self._save_system.get_setting("controller_bindings")
        return self._normalize_binding_data(saved)

    def _register_joystick(self, joy: pygame.joystick.Joystick) -> None:
        instance_id = joy.get_instance_id()
        self._joysticks[instance_id] = joy
        self._joystick_meta[instance_id] = self._build_joystick_metadata(joy)

    def _build_joystick_metadata(self, joy: pygame.joystick.Joystick) -> dict:
        name = joy.get_name()
        guid = self._safe_guid(joy)
        candidate_keys = self._candidate_profile_keys(name=name, guid=guid)
        existing_key = next(
            (key for key in candidate_keys if key in self._binding_data["profiles"]),
            None,
        )
        profile_key = existing_key or candidate_keys[0]
        return {
            "instance_id": joy.get_instance_id(),
            "name": name,
            "guid": guid,
            "profile_key": profile_key,
            "candidate_keys": candidate_keys,
            "buttons": joy.get_numbuttons(),
        }

    @staticmethod
    def _safe_guid(joy: pygame.joystick.Joystick) -> str | None:
        getter = getattr(joy, "get_guid", None)
        if not callable(getter):
            return None
        try:
            guid = getter()
        except Exception:
            return None
        if guid in (None, ""):
            return None
        return str(guid)

    @staticmethod
    def _candidate_profile_keys(*, name: str | None, guid: str | None) -> list[str]:
        keys: list[str] = []
        if guid:
            keys.append(f"guid:{guid}")
        if name:
            keys.append(f"name:{name}")
        return keys or ["name:Unknown Controller"]

    @staticmethod
    def _normalized_default_bindings() -> dict:
        return {
            "confirm": int(CONTROLLER_BINDINGS_DEFAULT["confirm"]),
            "back": int(CONTROLLER_BINDINGS_DEFAULT["back"]),
            "start": [int(button) for button in CONTROLLER_BINDINGS_DEFAULT["start"]],
        }

    @classmethod
    def _normalize_simple_bindings(cls, bindings: object) -> dict:
        normalized = cls._normalized_default_bindings()
        if not isinstance(bindings, dict):
            return normalized

        confirm = bindings.get("confirm")
        if isinstance(confirm, int) and confirm >= 0:
            normalized["confirm"] = confirm

        back = bindings.get("back")
        if isinstance(back, int) and back >= 0:
            normalized["back"] = back

        start = bindings.get("start")
        if isinstance(start, int) and start >= 0:
            normalized["start"] = [start]
        elif isinstance(start, list):
            valid_buttons = [button for button in start if isinstance(button, int) and button >= 0]
            if valid_buttons:
                normalized["start"] = valid_buttons

        return normalized

    @classmethod
    def _normalize_binding_data(cls, bindings: object) -> dict:
        defaults = {
            "global_bindings": cls._normalized_default_bindings(),
            "profiles": {},
        }
        if not isinstance(bindings, dict):
            return defaults

        if "global_bindings" not in bindings and "profiles" not in bindings:
            defaults["global_bindings"] = cls._normalize_simple_bindings(bindings)
            return defaults

        defaults["global_bindings"] = cls._normalize_simple_bindings(
            bindings.get("global_bindings", CONTROLLER_BINDINGS_SETTINGS_DEFAULT["global_bindings"])
        )

        profiles = bindings.get("profiles")
        if not isinstance(profiles, dict):
            return defaults

        normalized_profiles: dict[str, dict] = {}
        for key, profile in profiles.items():
            if not isinstance(key, str) or not isinstance(profile, dict):
                continue
            normalized_profiles[key] = {
                "guid": profile.get("guid") if isinstance(profile.get("guid"), str) else cls._guid_for_profile_key(key),
                "name": profile.get("name") if isinstance(profile.get("name"), str) else cls._name_for_profile_key(key),
                "bindings": cls._normalize_simple_bindings(profile.get("bindings")),
            }
        defaults["profiles"] = normalized_profiles
        return defaults

    @staticmethod
    def _guid_for_profile_key(profile_key: str) -> str | None:
        if profile_key.startswith("guid:"):
            return profile_key.split(":", 1)[1]
        return None

    @staticmethod
    def _name_for_profile_key(profile_key: str) -> str:
        return profile_key.split(":", 1)[1] if ":" in profile_key else profile_key

    def _profile_metadata_for_key(self, profile_key: str) -> dict | None:
        for meta in self._joystick_meta.values():
            if meta["profile_key"] == profile_key or profile_key in meta["candidate_keys"]:
                return meta
        return self._binding_data["profiles"].get(profile_key)

    def _resolve_profile_key(self, *, joystick_id: int | None = None, profile_key: str | None = None) -> str | None:
        if profile_key is not None:
            return self._canonical_profile_key(profile_key)
        if joystick_id is None:
            return None
        meta = self._joystick_meta.get(joystick_id)
        if meta is None:
            return None
        return self._canonical_profile_key(meta["profile_key"])

    def _canonical_profile_key(self, profile_key: str) -> str:
        meta = self._profile_metadata_for_key(profile_key)
        if meta is not None and meta.get("guid"):
            return f"guid:{meta['guid']}"
        if profile_key in self._binding_data["profiles"]:
            return profile_key
        if meta is not None:
            candidate_keys = meta.get("candidate_keys", [])
            for candidate_key in candidate_keys:
                if candidate_key in self._binding_data["profiles"]:
                    return candidate_key
            if candidate_keys:
                return candidate_keys[0]
        return profile_key

    def _resolve_bindings(self, *, joystick_id: int | None = None, profile_key: str | None = None) -> dict:
        target_key = self._resolve_profile_key(joystick_id=joystick_id, profile_key=profile_key)
        if target_key is not None:
            profile = self._binding_data["profiles"].get(target_key)
            if profile is not None:
                return profile["bindings"]

            meta = self._joystick_meta.get(joystick_id) if joystick_id is not None else None
            if meta is not None:
                for candidate_key in meta["candidate_keys"]:
                    profile = self._binding_data["profiles"].get(candidate_key)
                    if profile is not None:
                        return profile["bindings"]

        return self._binding_data["global_bindings"]

    def _process_axes(self, joy: pygame.joystick.Joystick, dt: float) -> None:
        iid = joy.get_instance_id()
        nav_map: dict[int, tuple[int, int]] = {
            0: (pygame.K_LEFT, pygame.K_RIGHT),
            1: (pygame.K_UP, pygame.K_DOWN),
        }
        for axis_idx, (neg_key, pos_key) in nav_map.items():
            if joy.get_numaxes() <= axis_idx:
                continue
            raw = joy.get_axis(axis_idx)
            if abs(raw) < CONTROLLER_DEADZONE:
                new_dir = 0
            elif raw < 0:
                new_dir = -1
            else:
                new_dir = 1

            state_key = (iid, axis_idx)
            prev_dir = self._axis_dir.get(state_key, 0)

            if new_dir != prev_dir:
                self._axis_dir[state_key] = new_dir
                if new_dir != 0:
                    self._axis_timer[state_key] = CONTROLLER_AXIS_REPEAT_DELAY
                    self._post_key(neg_key if new_dir < 0 else pos_key, instance_id=iid, synthetic_controller_event=True)
                else:
                    self._axis_timer.pop(state_key, None)
            elif new_dir != 0:
                timer = self._axis_timer.get(state_key, 0.0) - dt
                if timer <= 0.0:
                    timer += CONTROLLER_AXIS_REPEAT_RATE
                    self._post_key(neg_key if new_dir < 0 else pos_key, instance_id=iid, synthetic_controller_event=True)
                self._axis_timer[state_key] = timer

    def _process_hats(self, joy: pygame.joystick.Joystick) -> None:
        iid = joy.get_instance_id()
        for hat_idx in range(joy.get_numhats()):
            hx, hy = joy.get_hat(hat_idx)
            state_key = (iid, hat_idx)
            prev_hx, prev_hy = self._hat_state.get(state_key, (0, 0))
            if (hx, hy) == (prev_hx, prev_hy):
                continue
            self._hat_state[state_key] = (hx, hy)
            if hx == -1:
                self._post_key(pygame.K_LEFT, instance_id=iid, synthetic_controller_event=True)
            elif hx == 1:
                self._post_key(pygame.K_RIGHT, instance_id=iid, synthetic_controller_event=True)
            if hy == 1:
                self._post_key(pygame.K_UP, instance_id=iid, synthetic_controller_event=True)
            elif hy == -1:
                self._post_key(pygame.K_DOWN, instance_id=iid, synthetic_controller_event=True)

    def _process_buttons(self, joy: pygame.joystick.Joystick) -> None:
        iid = joy.get_instance_id()
        bindings = self._resolve_bindings(joystick_id=iid)
        button_map: dict[int, int] = {
            bindings["confirm"]: pygame.K_RETURN,
            bindings["back"]: pygame.K_ESCAPE,
        }
        for button in bindings["start"]:
            button_map[button] = pygame.K_ESCAPE

        for btn_idx, mapped_key in button_map.items():
            if joy.get_numbuttons() <= btn_idx:
                continue
            pressed = bool(joy.get_button(btn_idx))
            state_key = (iid, btn_idx)
            was_pressed = self._button_state.get(state_key, False)
            if pressed and not was_pressed:
                self._post_key(mapped_key, instance_id=iid, synthetic_controller_event=True)
            elif not pressed and was_pressed:
                self._post_keyup(mapped_key, instance_id=iid, synthetic_controller_event=True)
            self._button_state[state_key] = pressed

    @staticmethod
    def _post_key(
        key: int,
        *,
        instance_id: int | None = None,
        synthetic_controller_event: bool = False,
    ) -> None:
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN,
            {
                "key": key,
                "mod": 0,
                "unicode": "",
                "scancode": 0,
                "synthetic_controller_event": synthetic_controller_event,
                "source_device_type": "controller" if synthetic_controller_event else "keyboard",
                "source_instance_id": instance_id,
            },
        ))

    @staticmethod
    def _post_keyup(
        key: int,
        *,
        instance_id: int | None = None,
        synthetic_controller_event: bool = False,
    ) -> None:
        pygame.event.post(pygame.event.Event(
            pygame.KEYUP,
            {
                "key": key,
                "mod": 0,
                "unicode": "",
                "scancode": 0,
                "synthetic_controller_event": synthetic_controller_event,
                "source_device_type": "controller" if synthetic_controller_event else "keyboard",
                "source_instance_id": instance_id,
            },
        ))
