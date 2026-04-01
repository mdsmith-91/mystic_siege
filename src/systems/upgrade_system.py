import random
from settings import HERO_CLASSES

# Define PASSIVE_UPGRADES as a module-level list of dicts
PASSIVE_UPGRADES = [
    {
        "name": "+20 Max HP",
        "description": "Increase maximum health by 20",
        "stat": "max_hp",
        "value": 20,
        "icon_color": (60, 200, 80)
    },
    {
        "name": "+5% Move Speed",
        "description": "Increase movement speed by 5%",
        "stat": "speed_pct",
        "value": 0.05,
        "icon_color": (100, 200, 255)
    },
    {
        "name": "+10% Pickup Radius",
        "description": "Increase item pickup radius by 10%",
        "stat": "pickup_radius_pct",
        "value": 0.10,
        "icon_color": (212, 175, 55)
    },
    {
        "name": "+5 Armor",
        "description": "Increase armor by 5",
        "stat": "armor",
        "value": 5,
        "icon_color": (160, 160, 160)
    },
    {
        "name": "+0.5 HP/s Regen",
        "description": "Increase health regeneration by 0.5 HP per second",
        "stat": "regen_rate",
        "value": 0.5,
        "icon_color": (120, 255, 120)
    },
    {
        "name": "+10% XP Gain",
        "description": "Increase XP gain by 10%",
        "stat": "xp_multiplier_pct",
        "value": 0.10,
        "icon_color": (80, 220, 255)
    },
    {
        "name": "+5% Cooldown Reduc",
        "description": "Reduce weapon cooldowns by 5%",
        "stat": "cooldown_reduction",
        "value": 0.05,
        "icon_color": (255, 140, 60)
    }
]

# Define WEAPON_CLASSES as module-level list of weapon class names (strings)
WEAPON_CLASSES = [
    "ArcaneBolt",
    "HolyNova",
    "SpectralBlade",
    "FlameWhip",
    "FrostRing",
    "LightningChain"
]

WEAPON_META = {
    "ArcaneBolt": {
        "name": "Arcane Bolt",
        "new_description": "Fires homing bolts that seek out nearby enemies.",
        "upgrade_description": "Upgrade Arcane Bolt — adds bolts and piercing at max level.",
        "icon_color": (120, 80, 220),
        "symbol": "AB",
    },
    "HolyNova": {
        "name": "Holy Nova",
        "new_description": "Emits a ring of holy energy that damages nearby enemies.",
        "upgrade_description": "Upgrade Holy Nova — increases radius and damage.",
        "icon_color": (255, 220, 80),
        "symbol": "HN",
    },
    "SpectralBlade": {
        "name": "Spectral Blade",
        "new_description": "Orbiting swords that continuously slash surrounding foes.",
        "upgrade_description": "Upgrade Spectral Blade — adds blades and increases damage.",
        "icon_color": (80, 220, 200),
        "symbol": "SB",
    },
    "FlameWhip": {
        "name": "Flame Whip",
        "new_description": "Cracks a fiery whip in a directional cone, applying burn.",
        "upgrade_description": "Upgrade Flame Whip — widens cone and increases burn damage.",
        "icon_color": (240, 100, 30),
        "symbol": "FW",
    },
    "FrostRing": {
        "name": "Frost Ring",
        "new_description": "Expands an ice ring that freezes enemies in place.",
        "upgrade_description": "Upgrade Frost Ring — increases radius and freeze duration.",
        "icon_color": (140, 210, 255),
        "symbol": "FR",
    },
    "LightningChain": {
        "name": "Lightning Chain",
        "new_description": "Strikes an enemy with lightning that chains to nearby foes.",
        "upgrade_description": "Upgrade Lightning Chain — adds more chain targets.",
        "icon_color": (255, 255, 100),
        "symbol": "LC",
    },
}

class UpgradeSystem:
    def __init__(self, projectile_group, enemy_group):
        self.projectile_group = projectile_group
        self.enemy_group = enemy_group

    def get_random_choices(self, player) -> list[dict]:
        """Get 3 random upgrade choices for the player."""
        # Build candidate list
        candidates = []

        # Add weapons the player does NOT have (offer as "new weapon" card)
        for weapon_class in WEAPON_CLASSES:
            has_weapon = False
            for weapon in player.weapons:
                if weapon.__class__.__name__ == weapon_class:
                    has_weapon = True
                    break
            if not has_weapon:
                meta = WEAPON_META.get(weapon_class, {})
                candidates.append({
                    "weapon_class": weapon_class,
                    "type": "new_weapon",
                    "name": meta.get("name", weapon_class),
                    "description": meta.get("new_description", "Unlock this weapon."),
                    "icon_color": meta.get("icon_color", (100, 100, 180)),
                    "symbol": meta.get("symbol", weapon_class[:2]),
                })

        # Add weapons the player HAS but not at level 5 (offer as "upgrade" card)
        for weapon in player.weapons:
            if weapon.level < 5:
                weapon_class = weapon.__class__.__name__
                meta = WEAPON_META.get(weapon_class, {})
                candidates.append({
                    "weapon_class": weapon_class,
                    "type": "upgrade",
                    "name": f"Upgrade {meta.get('name', weapon_class)}",
                    "description": meta.get("upgrade_description", f"Upgrade {weapon_class} to level {weapon.level + 1}."),
                    "icon_color": meta.get("icon_color", (100, 100, 180)),
                    "symbol": meta.get("symbol", weapon_class[:2]),
                })

        # Add all passive upgrades always available
        for passive in PASSIVE_UPGRADES:
            candidates.append({
                "stat": passive["stat"],
                "value": passive["value"],
                "name": passive["name"],
                "description": passive["description"],
                "icon_color": passive["icon_color"],
                "type": "passive"
            })

        # Ensure at least 1 passive is included
        if not any(c["type"] == "passive" for c in candidates):
            # If no passives, add one random passive
            candidates.append({
                "stat": PASSIVE_UPGRADES[0]["stat"],
                "value": PASSIVE_UPGRADES[0]["value"],
                "name": PASSIVE_UPGRADES[0]["name"],
                "description": PASSIVE_UPGRADES[0]["description"],
                "icon_color": PASSIVE_UPGRADES[0]["icon_color"],
                "type": "passive"
            })

        # If player has all weapons at max level: return 3 passives
        if all(weapon.level >= 5 for weapon in player.weapons if hasattr(weapon, 'level')):
            # Filter to only passives
            candidates = [c for c in candidates if c["type"] == "passive"]
            if len(candidates) >= 3:
                return random.sample(candidates, 3)
            else:
                # If not enough passives, add some random ones
                while len(candidates) < 3:
                    candidates.append(random.choice(PASSIVE_UPGRADES))

        # Return 3 randomly selected without duplicates
        if len(candidates) >= 3:
            return random.sample(candidates, 3)
        else:
            # If not enough candidates, return all available
            return candidates

    def apply_choice(self, choice: dict, player):
        """Apply the chosen upgrade."""
        if "weapon_class" in choice:
            weapon_class_name = choice["weapon_class"]

            if choice["type"] == "upgrade":
                player.upgrade_weapon(weapon_class_name)
            else:
                # Construct and add new weapon only when actually needed
                if weapon_class_name == "ArcaneBolt":
                    from src.weapons.arcane_bolt import ArcaneBolt
                    weapon = ArcaneBolt(player, self.projectile_group, self.enemy_group)
                elif weapon_class_name == "HolyNova":
                    from src.weapons.holy_nova import HolyNova
                    weapon = HolyNova(player, self.projectile_group, self.enemy_group)
                elif weapon_class_name == "SpectralBlade":
                    from src.weapons.spectral_blade import SpectralBlade
                    weapon = SpectralBlade(player, self.projectile_group, self.enemy_group)
                elif weapon_class_name == "FlameWhip":
                    from src.weapons.flame_whip import FlameWhip
                    weapon = FlameWhip(player, self.projectile_group, self.enemy_group)
                elif weapon_class_name == "FrostRing":
                    from src.weapons.frost_ring import FrostRing
                    weapon = FrostRing(player, self.projectile_group, self.enemy_group)
                elif weapon_class_name == "LightningChain":
                    from src.weapons.lightning_chain import LightningChain
                    weapon = LightningChain(player, self.projectile_group, self.enemy_group)
                else:
                    return
                player.add_weapon(weapon)
        else:
            # If choice has "stat" key: call _apply_passive(choice, player)
            self._apply_passive(choice, player)

    def _apply_passive(self, choice, player):
        """Handle passive upgrades."""
        stat = choice["stat"]
        value = choice["value"]

        # Handle each stat type:
        if stat == "max_hp":
            player.max_hp += value
            player.hp += value
        elif stat == "speed_pct":
            player.speed *= (1 + value)
        elif stat == "pickup_radius_pct":
            player.pickup_radius *= (1 + value)
        elif stat == "armor":
            player.armor += value
        elif stat == "regen_rate":
            player.regen_rate += value
        elif stat == "xp_multiplier_pct":
            player.xp_multiplier *= (1 + value)
        elif stat == "cooldown_reduction":
            player.cooldown_reduction = min(0.9, player.cooldown_reduction + value)