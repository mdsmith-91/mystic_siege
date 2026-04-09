from src.weapons.arcane_bolt import ArcaneBolt
from src.weapons.bramble_seeds import BrambleSeeds
from src.weapons.caltrops import Caltrops
from src.weapons.chain_flail import ChainFlail
from src.weapons.flame_blast import FlameBlast
from src.weapons.frost_ring import FrostRing
from src.weapons.hex_orb import HexOrb
from src.weapons.holy_nova import HolyNova
from src.weapons.lightning_chain import LightningChain
from src.weapons.longbow import Longbow
from src.weapons.shadow_knives import ShadowKnives
from src.weapons.spear import Spear
from src.weapons.sword import Sword
from src.weapons.throwing_axes import ThrowingAxes


WEAPON_CLASS_REGISTRY = {
    "ArcaneBolt": ArcaneBolt,
    "BrambleSeeds": BrambleSeeds,
    "Caltrops": Caltrops,
    "ChainFlail": ChainFlail,
    "HolyNova": HolyNova,
    "Sword": Sword,
    "FlameBlast": FlameBlast,
    "FrostRing": FrostRing,
    "HexOrb": HexOrb,
    "LightningChain": LightningChain,
    "Longbow": Longbow,
    "ShadowKnives": ShadowKnives,
    "Spear": Spear,
    "ThrowingAxes": ThrowingAxes,
}


def create_weapon(weapon_class_name: str, owner, projectile_group, enemy_group, effect_group=None):
    weapon_class = WEAPON_CLASS_REGISTRY.get(weapon_class_name)
    if weapon_class is None:
        raise ValueError(f"Unknown weapon class: {weapon_class_name}")

    return weapon_class(owner, projectile_group, enemy_group, effect_group)
