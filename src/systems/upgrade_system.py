import random
from settings import HERO_CLASSES, MAX_WEAPON_SLOTS, UPGRADE_MENU_CARD_COUNT
from src.weapons.factory import create_weapon

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
        "description": "Increase XP orb and item pickup radius by 10%",
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
        "name": "+5% Cooldown Reduction",
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
    },
    {
        "name": "+10% Physical Damage",
        "description": "Increase damage dealt by all physical weapons by 10%",
        "stat": "physical_damage_multiplier_pct",
        "value": 0.10,
        "icon_color": (180, 120, 80)
    },
    {
        "name": "+1 Projectile Pierce",
        "description": "Increase pierce for all projectile weapons by 1",
        "stat": "projectile_pierce_bonus",
        "value": 1,
        "icon_color": (150, 180, 255)
    },
    {
        "name": "+10% Damage Over Time",
        "description": "Increase all damage-over-time effects by 10%",
        "stat": "dot_damage_bonus_pct",
        "value": 0.10,
        "icon_color": (220, 80, 30)
    },
    {
        "name": "+10% Area Size",
        "description": "Increase the radius of all area-of-effect abilities by 10%",
        "stat": "area_size_bonus_pct",
        "value": 0.10,
        "icon_color": (80, 200, 180)
    },
    {
        "name": "+5% All Damage",
        "description": "Increase all outgoing damage by 5%",
        "stat": "base_damage_bonus_pct",
        "value": 0.05,
        "icon_color": (210, 50, 50)
    },
]

# Define WEAPON_CLASSES as module-level list of weapon class names (strings)
WEAPON_CLASSES = [
    "ArcaneBolt",
    "BrambleSeeds",
    "Caltrops",
    "ChainFlail",
    "HolyNova",
    "Sword",
    "FlameBlast",
    "FrostRing",
    "HexOrb",
    "LightningChain",
    "Longbow",
    "ShadowKnives",
    "Spear",
    "ThrowingAxes",
]

WEAPON_META = {
    "ArcaneBolt": {
        "name": "Arcane Bolt",
        "new_description": "Fires homing bolts that seek out nearby enemies.",
        "upgrade_description": "L2 +10 damage. L3 +1 bolt. L4 +1 pierce. L5 +1 bolt, +15 damage, and killing bolts explode.",
        "icon_color": (120, 80, 220),
        "symbol": "AB",
    },
    "BrambleSeeds": {
        "name": "Bramble Seeds",
        "new_description": "Throws seeds that grow thorn patches, damaging and slowing enemies inside.",
        "upgrade_description": "L2 larger patches. L3 stronger tick damage. L4 longer patches. L5 faster cooldown; kills bloom a second patch.",
        "icon_color": (82, 190, 95),
        "symbol": "BS",
    },
    "Caltrops": {
        "name": "Caltrops",
        "new_description": "Scatters physical traps that slow enemies and apply a small bleed over time.",
        "upgrade_description": "L2 +damage. L3 +1 caltrop. L4 longer duration and stronger bleed. L5 faster cooldown; kills inside traps explode.",
        "icon_color": (150, 150, 160),
        "symbol": "CT",
    },
    "ChainFlail": {
        "name": "Chain Flail",
        "new_description": "Extends a tethered flail, spins once around the wielder, then retracts.",
        "upgrade_description": "L2 +damage. L3 longer reach. L4 longer spin. L5 faster cooldown; flail snaps back for a second arc.",
        "icon_color": (180, 170, 130),
        "symbol": "CF",
    },
    "HolyNova": {
        "name": "Holy Nova",
        "new_description": "Emits an expanding ring of holy energy that damages all enemies it passes through.",
        "upgrade_description": "L2 +15 damage. L3 +40 radius. L4 -0.4s cooldown. L5 +20 damage; ring leaves consecrated ground.",
        "icon_color": (255, 220, 80),
        "symbol": "HN",
    },
    "Sword": {
        "name": "Sword",
        "new_description": "Delivers broad steel slashes against nearby enemies with heavy, readable timing.",
        "upgrade_description": "L2 +8 damage. L3 -0.12s cooldown. L4 +18 reach. L5 follow-up slash.",
        "icon_color": (185, 188, 194),
        "symbol": "SW",
    },
    "FlameBlast": {
        "name": "Flame Blast",
        "new_description": "Blasts a cone of fire toward the nearest enemy, applying burn over time.",
        "upgrade_description": "L2 +15 damage. L3 +40 range. L4 +1.5s burn duration. L5 +20 damage; blast leaves a lingering fire pool.",
        "icon_color": (240, 100, 30),
        "symbol": "FW",
    },
    "FrostRing": {
        "name": "Frost Ring",
        "new_description": "Expands a freezing ring outward, immobilizing and damaging enemies it touches.",
        "upgrade_description": "L2 +0.5s freeze. L3 +10 damage. L4 +0.5s freeze. L5 -0.8s cooldown, larger radius; frozen kills shatter.",
        "icon_color": (140, 210, 255),
        "symbol": "FR",
    },
    "HexOrb": {
        "name": "Hex Orb",
        "new_description": "Fires a slow dark orb that curses enemies and damages them over time.",
        "upgrade_description": "L2 stronger curse. L3 longer curse duration. L4 +1 orb. L5 +8 direct damage and curse splash.",
        "icon_color": (100, 45, 140),
        "symbol": "HX",
    },
    "LightningChain": {
        "name": "Lightning Chain",
        "new_description": "Strikes the nearest enemy with lightning that chains to nearby foes.",
        "upgrade_description": "L2 +15 damage. L3 +2 chain count. L4 +50 chain range. L5 +1 chain, 30% stun; stunned kills overload nearby foes.",
        "icon_color": (255, 255, 100),
        "symbol": "LC",
    },
    "Longbow": {
        "name": "Longbow",
        "new_description": "Fires fast, precise arrows in straight lines at nearby enemies.",
        "upgrade_description": "L2 +8 damage. L3 -0.15s cooldown. L4 +1 pierce. L5 +10% crit bonus; crits briefly root the target.",
        "icon_color": (170, 120, 60),
        "symbol": "LB",
    },
    "ShadowKnives": {
        "name": "Shadow Knives",
        "new_description": "Throws fast knives at the nearest enemy, then calls them back to the wielder.",
        "upgrade_description": "L2 +6 damage. L3 +1 knife. L4 -0.10s cooldown and +5% crit bonus. L5 +8 damage; knives apply venom on hit.",
        "icon_color": (105, 105, 135),
        "symbol": "SK",
    },
    "Spear": {
        "name": "Spear",
        "new_description": "Thrusts a spear forward in a narrow lane, piercing through enemies in line.",
        "upgrade_description": "L2 +10 damage. L3 longer reach and faster cooldown. L4 +1 pierce. L5 double thrust and +8% crit.",
        "icon_color": (185, 190, 200),
        "symbol": "SP",
    },
    "ThrowingAxes": {
        "name": "Throwing Axes",
        "new_description": "Hurls a spinning axe at the nearest enemy. Shorter range than a bow but hits harder.",
        "upgrade_description": "L2 +12 damage. L3 -0.20s cooldown. L4 +1 pierce. L5 +10% crit bonus; killing axes ricochet to a nearby enemy.",
        "icon_color": (160, 160, 170),
        "symbol": "TA",
    },
}

class UpgradeSystem:
    def __init__(self, projectile_group, enemy_group, effect_group=None):
        self.projectile_group = projectile_group
        self.enemy_group = enemy_group
        self.effect_group = effect_group

    def get_random_choices(self, player) -> list[dict]:
        """Get the configured number of random upgrade choices for the player."""
        choice_count = UPGRADE_MENU_CARD_COUNT

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

        # If player has all weapons at max level: return configured-count passives
        if all(weapon.level >= 5 for weapon in player.weapons if hasattr(weapon, 'level')):
            # Filter to only passives
            candidates = [c for c in candidates if c["type"] == "passive"]
            if len(candidates) >= choice_count:
                return random.sample(candidates, choice_count)
            else:
                # Fill with passives not already in candidates
                existing_names = {c["name"] for c in candidates}
                remaining = [p for p in PASSIVE_UPGRADES if p["name"] not in existing_names]
                random.shuffle(remaining)
                for p in remaining:
                    if len(candidates) >= choice_count:
                        break
                    candidates.append({
                        "stat": p["stat"], "value": p["value"], "name": p["name"],
                        "description": p["description"], "icon_color": p["icon_color"],
                        "type": "passive"
                    })

        # Return the configured number randomly selected without duplicates
        if len(candidates) >= choice_count:
            return random.sample(candidates, choice_count)
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
                weapon = create_weapon(
                    weapon_class_name,
                    player,
                    self.projectile_group,
                    self.enemy_group,
                    self.effect_group,
                )
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
            player.add_flat_max_hp(value)
        elif stat == "speed_pct":
            player.add_flat_percent_bonus(stat, value)
        elif stat == "pickup_radius_pct":
            player.add_flat_percent_bonus(stat, value)
        elif stat == "armor":
            player.add_flat_armor(value)
        elif stat == "regen_rate":
            player.regen_rate += value
        elif stat == "xp_multiplier_pct":
            player.add_flat_percent_bonus(stat, value)
        elif stat == "cooldown_reduction":
            player.base_cooldown_reduction = min(0.9, player.base_cooldown_reduction + value)
            player._rebuild_combat_modifiers()
        elif stat == "crit_chance":
            player.crit_chance += value
        elif stat == "spell_damage_multiplier_pct":
            player.add_flat_percent_bonus(stat, value)
        elif stat == "physical_damage_multiplier_pct":
            player.add_flat_percent_bonus(stat, value)
        elif stat == "dot_damage_bonus_pct":
            player.dot_damage_bonus_pct += value
            player._recalculate_pct_stats()
        elif stat == "area_size_bonus_pct":
            player.area_size_bonus_pct += value
        elif stat == "base_damage_bonus_pct":
            player.base_damage_bonus_pct += value
            player._rebuild_combat_modifiers()
        else:
            player.apply_passive(stat, value)
