import pygame
from pygame.math import Vector2
from src.entities.base_entity import BaseEntity
from settings import PICKUP_RADIUS, WORLD_WIDTH, WORLD_HEIGHT, MAX_WEAPON_SLOTS, CRIT_CHANCE_BASE, WIZARD_SPELL_DAMAGE_BONUS
from src.utils.audio_manager import AudioManager
from src.utils.input_manager import InputManager
from src.utils.spritesheet import Spritesheet

# Column indices matching DIRECTION_ORDER in generate_sprite.py
_DIR_DOWN  = 0
_DIR_LEFT  = 1
_DIR_RIGHT = 2
_DIR_UP    = 3

class Player(BaseEntity):
    def __init__(self, pos, hero_class_data: dict, groups):
        super().__init__(pos, groups)

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
        self.pickup_radius = PICKUP_RADIUS
        self.cooldown_reduction = 0.0       # 0.0 to 0.9 max
        self.crit_chance = CRIT_CHANCE_BASE
        self.spell_damage_multiplier = 1.0
        if self.hero_class == "Wizard":
            self.crit_chance += 0.10
            self.spell_damage_multiplier += WIZARD_SPELL_DAMAGE_BONUS
        self.damage_multiplier = 1.0

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

        # Death state
        self.dying = False
        self.death_timer = 0.0

    def update(self, dt):
        # Read WASD/arrow keys and merge with analog stick input
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

        # Add analog stick contribution (deadzone already applied in InputManager)
        ax, ay = InputManager.instance().get_movement()
        direction.x += ax
        direction.y += ay

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

        # Handle death fade
        if self.hp <= 0 and not self.dying:
            self.dying = True
            self.death_timer = 1.0
            self._alpha = 255
            AudioManager.instance().play_sfx(AudioManager.PLAYER_DEATH)

        if self.dying:
            self.death_timer -= dt
            if self.death_timer > 0:
                self._alpha = int(255 * self.death_timer)
            else:
                # Death complete — kill() removes from groups; is_alive property returns False automatically
                super().kill()

        # Select directional frame then apply current alpha
        self.image = self._frame_for_facing()
        self.image.set_alpha(self._alpha)

        # Sync rect
        self.rect.center = self.pos

    def _frame_for_facing(self) -> pygame.Surface:
        """Pick the directional frame that best matches the current facing vector."""
        if abs(self.facing.x) >= abs(self.facing.y):
            return self._frames[_DIR_RIGHT] if self.facing.x >= 0 else self._frames[_DIR_LEFT]
        return self._frames[_DIR_DOWN] if self.facing.y >= 0 else self._frames[_DIR_UP]

    def take_damage(self, amount: float):
        """Play hit sound and apply damage."""
        AudioManager.instance().play_sfx(AudioManager.PLAYER_HIT)
        super().take_damage(amount)

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