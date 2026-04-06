from src.weapons.arcane_bolt import ArcaneBolt
from src.weapons.flame_blast import FlameBlast
from src.weapons.frost_ring import FrostRing
from src.weapons.holy_nova import HolyNova
from src.weapons.lightning_chain import LightningChain
from src.weapons.longbow import Longbow
from src.weapons.spectral_blade import SpectralBlade


WEAPON_CLASS_REGISTRY = {
    "ArcaneBolt": ArcaneBolt,
    "HolyNova": HolyNova,
    "SpectralBlade": SpectralBlade,
    "FlameBlast": FlameBlast,
    "FrostRing": FrostRing,
    "LightningChain": LightningChain,
    "Longbow": Longbow,
}


def create_weapon(weapon_class_name: str, owner, projectile_group, enemy_group, effect_group=None):
    weapon_class = WEAPON_CLASS_REGISTRY.get(weapon_class_name)
    if weapon_class is None:
        raise ValueError(f"Unknown weapon class: {weapon_class_name}")

    return weapon_class(owner, projectile_group, enemy_group, effect_group)
