import pygame
from pygame.math import Vector2
from src.entities.base_entity import BaseEntity
from settings import (
    PICKUP_RADIUS,
    WORLD_WIDTH,
    WORLD_HEIGHT,
    MAX_WEAPON_SLOTS,
    CRIT_CHANCE_BASE,
    DOWNED_ALPHA,
)
from src.utils.audio_manager import AudioManager
from src.utils.input_manager import InputManager
from src.utils.spritesheet import Spritesheet
from src.core.player_slot import PlayerSlot

# Column indices matching DIRECTION_ORDER in generate_sprite.py
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

class Player(BaseEntity):
    def __init__(self, pos, hero_class_data: dict, groups,
                 slot: PlayerSlot | None = None,
                 supports_revive: bool = False):
        super().__init__(pos, groups)

        self.hero_data = hero_class_data

        # Store hero class name for passive checks
        self.hero_class = hero_class_data.get("name", "")

        # Read hp, speed, armor from hero_class_data
        self.max_hp = hero_class_data["hp"]
        self.hp = self.max_hp
        self.speed = hero_class_data["speed"]
        self.base_speed = self.speed
        self.armor = hero_class_data["armor"]

        # Load 4-direction spritesheet: cols = [down, left, right, up]
        sheet = Spritesheet(hero_class_data["sprite"], 32, 32)
        self._frames = {
            _DIR_DOWN:  sheet.get_frame(0, 0),
            _DIR_LEFT:  sheet.get_frame(1, 0),
            _DIR_RIGHT: sheet.get_frame(2, 0),
            _DIR_UP:    sheet.get_frame(3, 0),
        }

        # Track desired alpha separately so it survives frame swaps each update
        self._alpha = 255

        self.image = self._frames[_DIR_DOWN]
        self.rect = self.image.get_rect(center=pos)

        # Active weapons list (max 6 slots)
        self.weapons = []

        # Passive stats as instance variables
        self.regen_rate = 0.0       # HP per second
        self.xp_multiplier = 1.0
        self.base_xp_multiplier = 1.0
        self.xp_multiplier_bonus_pct = 0.0
        self.pickup_radius = PICKUP_RADIUS
        self.base_pickup_radius = PICKUP_RADIUS
        self.pickup_radius_bonus_pct = 0.0
        self.cooldown_reduction = 0.0       # 0.0 to 0.9 max
        self.crit_chance = CRIT_CHANCE_BASE
        self.spell_damage_multiplier = 1.0
        self.base_spell_damage_multiplier = 1.0
        self.spell_damage_bonus_pct = 0.0
        self.projectile_pierce_bonus = 0
        self.speed_bonus_pct = 0.0
        self.damage_taken_multiplier = 1.0
        self.knockback_immune = False
        self.heal_per_xp = 0.0
        self._apply_hero_passives()
        self.damage_multiplier = 1.0
        self._recalculate_pct_stats()

        # iframes: float = 0.0  (countdown timer for invincibility frames)
        self.iframes = 0.0
        self.flash_timer = 0.0

        # knockback_vel: separate from movement vel so WASD doesn't cancel it
        self.knockback_vel = Vector2(0, 0)

        # facing: Vector2 = Vector2(1, 0)  (updated each frame from movement)
        self.facing = Vector2(1, 0)

        # kill_count: int = 0
        self.kill_count = 0

        # orbs_collected: int = 0  (for Friar passive)
        self.orbs_collected = 0

        # Slot metadata from the lobby path.
        self.slot = slot
        self.supports_revive = supports_revive

        # Death / downed state
        self.dying = False
        self.death_timer = 0.0
        # Downed state: player stays in sprite groups at 0 HP for revive flow.
        self.is_downed = False
        self.revive_timer = 0.0

    def update(self, dt):
        if self.is_downed:
            self.vel = Vector2(0, 0)
            self.knockback_vel = Vector2(0, 0)
            self._alpha = DOWNED_ALPHA
        elif self.dying:
            self.vel = Vector2(0, 0)
            self.knockback_vel = Vector2(0, 0)
            self.death_timer -= dt
            if self.death_timer > 0:
                self._alpha = int(255 * self.death_timer)
            else:
                super().kill()
        else:
            direction = self._read_input()

            # Normalize direction if moving
            if direction.length() > 0:
                direction = direction.normalize()
                # Update facing if moving
                self.facing = direction

            # pos += direction * speed * dt, plus decaying knockback
            self.vel = direction * self.speed + self.knockback_vel
            self.knockback_vel *= max(0.0, 1.0 - 8.0 * dt)
            super().update(dt)

            # Clamp pos to world bounds (WORLD_WIDTH, WORLD_HEIGHT from settings)
            self.pos.x = max(0, min(WORLD_WIDTH - self.rect.width, self.pos.x))
            self.pos.y = max(0, min(WORLD_HEIGHT - self.rect.height, self.pos.y))

            # Regen tick: heal(regen_rate * dt)
            self.heal(self.regen_rate * dt)

            # Iframe countdown
            prev_iframes = self.iframes
            self.iframes = max(0, self.iframes - dt)

            # Flash effect during iframes — track desired alpha, apply after frame swap
            if self.iframes > 0:
                self.flash_timer += dt
                if self.flash_timer >= 0.1:
                    self.flash_timer = 0
                    self._alpha = 80 if self._alpha == 255 else 255
            elif prev_iframes > 0:
                # Iframes just expired — restore full opacity
                self._alpha = 255
                self.flash_timer = 0

            # Update all weapons
            for weapon in self.weapons:
                weapon.update(dt)

        # Select directional frame then apply current alpha
        self.image = self._frame_for_facing()
        self.image.set_alpha(self._alpha)

        # Sync rect
        self.rect.center = self.pos

    @property
    def is_alive(self) -> bool:
        """Override: downed players remain in sprite groups but are not alive."""
        return self.alive() and not self.is_downed

    @property
    def can_collect_xp(self) -> bool:
        """Whether the player can currently collect XP and queue upgrades."""
        return self.alive() and not self.is_downed and not self.dying

    def _recalculate_pct_stats(self) -> None:
        """Recompute effective percent-based stats from their base values."""
        self.speed = self.base_speed * (1.0 + self.speed_bonus_pct)
        self.pickup_radius = self.base_pickup_radius * (1.0 + self.pickup_radius_bonus_pct)
        self.xp_multiplier = self.base_xp_multiplier * (1.0 + self.xp_multiplier_bonus_pct)
        self.spell_damage_multiplier = self.base_spell_damage_multiplier * (1.0 + self.spell_damage_bonus_pct)

    def _apply_hero_passives(self) -> None:
        """Apply declarative passive bonuses from the hero config."""
        passives = self.hero_data.get("passives", {})
        self.crit_chance += passives.get("crit_chance_bonus", 0.0)
        self.spell_damage_bonus_pct += passives.get("spell_damage_bonus_pct", 0.0)
        self.projectile_pierce_bonus += passives.get("projectile_pierce_bonus", 0)
        self.damage_taken_multiplier = passives.get("damage_taken_multiplier", 1.0)
        self.knockback_immune = passives.get("knockback_immune", False)
        self.heal_per_xp = passives.get("heal_per_xp", 0.0)

    def add_flat_percent_bonus(self, stat: str, value: float) -> None:
        """Apply a percent bonus additively from the stat's base value."""
        if stat == "speed_pct":
            self.speed_bonus_pct += value
        elif stat == "pickup_radius_pct":
            self.pickup_radius_bonus_pct += value
        elif stat == "xp_multiplier_pct":
            self.xp_multiplier_bonus_pct += value
        elif stat == "spell_damage_multiplier_pct":
            self.spell_damage_bonus_pct += value
        else:
            return
        self._recalculate_pct_stats()

    def _read_input(self) -> Vector2:
        """Return the raw (un-normalized) movement direction for this player.

        Dispatches on self.slot.input_config when a slot is assigned.
        Falls back to the legacy global-keyboard + first-joystick behavior only
        when no concrete input_config is available.
        """
        cfg = self.slot.input_config if self.slot is not None else None

        if cfg is None:
            # Legacy 1P: global keyboard (WASD + arrows) + first active joystick
            direction = Vector2(0, 0)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                direction.x -= 1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                direction.x += 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                direction.y -= 1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                direction.y += 1
            ax, ay = InputManager.instance().get_movement()
            direction.x += ax
            direction.y += ay
            return direction

        if cfg["type"] == "keyboard":
            k = cfg["keys"]
            direction = Vector2(0, 0)
            keys = pygame.key.get_pressed()
            if keys[k["left"]]:
                direction.x -= 1
            if keys[k["right"]]:
                direction.x += 1
            if keys[k["up"]]:
                direction.y -= 1
            if keys[k["down"]]:
                direction.y += 1
            return direction

        if cfg["type"] == "controller":
            input_manager = InputManager.instance()
            joystick_id = input_manager.resolve_joystick_id(
                cfg.get("joystick_id"),
                profile_key=cfg.get("profile_key"),
                guid=cfg.get("guid"),
                name=cfg.get("name"),
            )
            if joystick_id is None:
                return Vector2(0, 0)
            if joystick_id != cfg.get("joystick_id"):
                self.slot.input_config = input_manager.build_controller_input_config(joystick_id)
            ax, ay = input_manager.get_movement_for_joystick(joystick_id)
            return Vector2(ax, ay)

        return Vector2(0, 0)

    def _frame_for_facing(self) -> pygame.Surface:
        """Pick the directional frame that best matches the current facing vector."""
        if abs(self.facing.x) >= abs(self.facing.y):
            return self._frames[_DIR_RIGHT] if self.facing.x >= 0 else self._frames[_DIR_LEFT]
        return self._frames[_DIR_DOWN] if self.facing.y >= 0 else self._frames[_DIR_UP]

    def take_damage(self, amount: float) -> float:
        """Apply damage and return the actual HP removed after mitigation."""
        if self.is_downed or self.dying:
            return 0.0

        AudioManager.instance().play_sfx(AudioManager.PLAYER_HIT)
        armor = getattr(self, 'armor', 0)
        damage = amount * (1.0 - armor / 100.0) if armor else amount
        damage *= self.damage_taken_multiplier
        previous_hp = self.hp
        self.hp = max(0.0, self.hp - damage)
        actual_damage = previous_hp - self.hp

        if self.supports_revive:
            if self.hp <= 0:
                for weapon in self.weapons:
                    weapon.on_owner_inactive()
                self.is_downed = True
                self.revive_timer = 0.0
                self.iframes = 0.0
                self.flash_timer = 0.0
                self.knockback_vel = Vector2(0, 0)
                self.vel = Vector2(0, 0)
                self._alpha = DOWNED_ALPHA
                AudioManager.instance().play_sfx(AudioManager.PLAYER_DEATH)
            return actual_damage

        if self.hp <= 0:
            for weapon in self.weapons:
                weapon.on_owner_inactive()
            self.dying = True
            self.death_timer = 1.0
            self.iframes = 0.0
            self.flash_timer = 0.0
            self.knockback_vel = Vector2(0, 0)
            self.vel = Vector2(0, 0)
            self._alpha = 255
            AudioManager.instance().play_sfx(AudioManager.PLAYER_DEATH)

        return actual_damage

    def add_weapon(self, weapon_instance):
        """Add a weapon to the player's inventory if there's space."""
        if len(self.weapons) < MAX_WEAPON_SLOTS:
            self.weapons.append(weapon_instance)

    def upgrade_weapon(self, weapon_class_name: str):
        """Find weapon by class name and upgrade it."""
        for weapon in self.weapons:
            if weapon.__class__.__name__ == weapon_class_name:
                weapon.upgrade()
                break

    def apply_passive(self, stat: str, value: float):
        """Add value to named stat attribute."""
        if hasattr(self, stat):
            setattr(self, stat, getattr(self, stat) + value)
