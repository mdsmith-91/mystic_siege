from dataclasses import dataclass


@dataclass
class PlayerSlot:
    """Slot/session metadata for one joined player.

    Passed through the scene chain (Lobby → ClassSelect → GameScene).
    Plain data container only — no pygame dependency, no runtime combat state.
    Runtime state (HP, downed, weapons) lives on the Player sprite.
    """

    index: int              # 0–3, stable for the session; used for UI positioning
    input_config: dict | None  # current lobby path provides a concrete config, including 1P
    hero_data: dict | None = None  # filled during hero selection; None until locked
    color: tuple = (255, 255, 255)  # player color badge used in UI and HUD
