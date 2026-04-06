import random
from settings import HERO_CLASSES, MAX_WEAPON_SLOTS

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
    },
    {
        "name": "+5% Crit Chance",
        "description": "Increase critical hit chance by 5%",
        "stat": "crit_chance",
        "value": 0.05,
        "icon_color": (255, 220, 60)
    },
    {
        "name": "+10% Spell Damage",
        "description": "Increase damage dealt by all spell weapons by 10%",
        "stat": "spell_damage_multiplier_pct",
        "value": 0.10,
        "icon_color": (160, 80, 255)
    }
]

# Define WEAPON_CLASSES as module-level list of weapon class names (strings)
WEAPON_CLASSES = [
    "ArcaneBolt",
    "HolyNova",
    "SpectralBlade",
    "FlameWhip",
    "FrostRing",
    "LightningChain",
    "Longbow",
]

WEAPON_META = {
    "ArcaneBolt": {
        "name": "Arcane Bolt",
        "new_description": "Fires homing bolts that seek out nearby enemies.",
        "upgrade_description": "More damage, +1 bolt at L3 and L5 (up to 3), pierce at L4.",
        "icon_color": (120, 80, 220),
        "symbol": "AB",
    },
    "HolyNova": {
        "name": "Holy Nova",
        "new_description": "Emits an expanding ring of holy energy that damages all enemies it passes through.",
        "upgrade_description": "More damage at L2 and L5, wider ring at L3, faster cooldown at L4.",
        "icon_color": (255, 220, 80),
        "symbol": "HN",
    },
    "SpectralBlade": {
        "name": "Spectral Blade",
        "new_description": "Orbiting swords that continuously slash surrounding foes.",
        "upgrade_description": "Adds a blade at L2 and L5 (up to 4), faster spin at L3, wider orbit at L4.",
        "icon_color": (80, 220, 200),
        "symbol": "SB",
    },
    "FlameWhip": {
        "name": "Flame Whip",
        "new_description": "Lashes a cone of fire toward the nearest enemy, applying a burn over time.",
        "upgrade_description": "More damage at L2 and L5, longer range at L3, longer burn duration at L4, wider cone at L5.",
        "icon_color": (240, 100, 30),
        "symbol": "FW",
    },
    "FrostRing": {
        "name": "Frost Ring",
        "new_description": "Expands a freezing ring outward, immobilizing and damaging enemies it touches.",
        "upgrade_description": "Longer freeze at L2, more damage at L3, faster ring expansion at L4, shorter cooldown and wider reach at L5.",
        "icon_color": (140, 210, 255),
        "symbol": "FR",
    },
    "LightningChain": {
        "name": "Lightning Chain",
        "new_description": "Strikes the nearest enemy with lightning that chains to nearby foes.",
        "upgrade_description": "More damage at L2 and L3, chains to 5 enemies at L3, longer chain range at L4, 6 chains and stun chance at L5.",
        "icon_color": (255, 255, 100),
        "symbol": "LC",
    },
    "Longbow": {
        "name": "Longbow",
        "new_description": "Fires fast, precise arrows in straight lines at nearby enemies.",
        "upgrade_description": "More damage at L2, faster shots at L3, pierce at L4, and an extra arrow plus higher crit at L5.",
        "icon_color": (170, 120, 60),
        "symbol": "LB",
    },
}

class UpgradeSystem:
    def __init__(self, projectile_group, enemy_group, effect_group=None):
        self.projectile_group = projectile_group
        self.enemy_group = enemy_group
        self.effect_group = effect_group

    def get_random_choices(self, player) -> list[dict]:
        """Get 3 random upgrade choices for the player."""
        # Build candidate list
        candidates = []

        # Do not offer new weapons when the inventory is already full.
        if len(player.weapons) < MAX_WEAPON_SLOTS:
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
                # Fill with passives not already in candidates
                existing_names = {c["name"] for c in candidates}
                remaining = [p for p in PASSIVE_UPGRADES if p["name"] not in existing_names]
                random.shuffle(remaining)
                for p in remaining:
                    if len(candidates) >= 3:
                        break
                    candidates.append({
                        "stat": p["stat"], "value": p["value"], "name": p["name"],
                        "description": p["description"], "icon_color": p["icon_color"],
                        "type": "passive"
                    })

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
                    weapon = ArcaneBolt(player, self.projectile_group, self.enemy_group, self.effect_group)
                elif weapon_class_name == "HolyNova":
                    from src.weapons.holy_nova import HolyNova
                    weapon = HolyNova(player, self.projectile_group, self.enemy_group, self.effect_group)
                elif weapon_class_name == "SpectralBlade":
                    from src.weapons.spectral_blade import SpectralBlade
                    weapon = SpectralBlade(player, self.projectile_group, self.enemy_group, self.effect_group)
                elif weapon_class_name == "FlameWhip":
                    from src.weapons.flame_whip import FlameWhip
                    weapon = FlameWhip(player, self.projectile_group, self.enemy_group, self.effect_group)
                elif weapon_class_name == "FrostRing":
                    from src.weapons.frost_ring import FrostRing
                    weapon = FrostRing(player, self.projectile_group, self.enemy_group, self.effect_group)
                elif weapon_class_name == "LightningChain":
                    from src.weapons.lightning_chain import LightningChain
                    weapon = LightningChain(player, self.projectile_group, self.enemy_group, self.effect_group)
                elif weapon_class_name == "Longbow":
                    from src.weapons.longbow import Longbow
                    weapon = Longbow(player, self.projectile_group, self.enemy_group, self.effect_group)
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
            player.add_flat_percent_bonus(stat, value)
        elif stat == "pickup_radius_pct":
            player.add_flat_percent_bonus(stat, value)
        elif stat == "armor":
            player.armor += value
        elif stat == "regen_rate":
            player.regen_rate += value
        elif stat == "xp_multiplier_pct":
            player.add_flat_percent_bonus(stat, value)
        elif stat == "cooldown_reduction":
            player.cooldown_reduction = min(0.9, player.cooldown_reduction + value)
        elif stat == "crit_chance":
            player.crit_chance += value
        elif stat == "spell_damage_multiplier_pct":
            player.add_flat_percent_bonus(stat, value)
