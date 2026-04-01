import pygame
from pygame.math import Vector2
from src.entities.base_entity import BaseEntity
from settings import PICKUP_RADIUS, WORLD_WIDTH, WORLD_HEIGHT, MAX_WEAPON_SLOTS
from src.utils.audio_manager import AudioManager

class Player(BaseEntity):
    def __init__(self, pos, hero_class_data: dict, groups):
        super().__init__(pos, groups)

        # Store hero class name for passive checks
        self.hero_class = hero_class_data.get("name", "")

        # Read hp, speed, armor from hero_class_data
        self.max_hp = hero_class_data["hp"]
        self.hp = self.max_hp
        self.speed = hero_class_data["speed"]
        self.armor = hero_class_data["armor"]

        # Placeholder image: 32x32 surface filled with hero_class_data["color"], label "P" centered
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.image.fill(hero_class_data["color"])
        # Draw "P" label
        font = pygame.font.SysFont(None, 24)
        text = font.render("P", True, (255, 255, 255))
        text_rect = text.get_rect(center=(16, 16))
        self.image.blit(text, text_rect)

        self.rect = self.image.get_rect(center=pos)

        # Active weapons list (max 6 slots)
        self.weapons = []

        # Passive stats as instance variables
        self.regen_rate = 0.0       # HP per second
        self.xp_multiplier = 1.0
        self.pickup_radius = PICKUP_RADIUS
        self.cooldown_reduction = 0.0       # 0.0 to 0.9 max
        self.crit_chance = 0.0
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
        # Read WASD/arrow input, build direction vector, normalize if non-zero
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

        # Iframe countdown: iframes = max(0, iframes - dt)
        prev_iframes = self.iframes
        self.iframes = max(0, self.iframes - dt)

        # Flash effect during iframes
        if self.iframes > 0:
            self.flash_timer += dt
            if self.flash_timer >= 0.1:  # Flash every 0.1 seconds
                self.flash_timer = 0
                # Toggle alpha between 255 and 80
                if self.image.get_alpha() == 255:
                    self.image.set_alpha(80)
                else:
                    self.image.set_alpha(255)
        elif prev_iframes > 0:
            # Iframes just expired — restore full opacity and reset flash timer
            self.image.set_alpha(255)
            self.flash_timer = 0

        # Update all weapons: for w in weapons: w.update(dt)
        for weapon in self.weapons:
            weapon.update(dt)

        # Handle death fade
        if self.hp <= 0 and not self.dying:
            self.dying = True
            self.death_timer = 1.0
            self.image.set_alpha(255)
            AudioManager.instance().play_sfx(AudioManager.PLAYER_DEATH)

        if self.dying:
            self.death_timer -= dt
            if self.death_timer > 0:
                # Fade out
                alpha = int(255 * self.death_timer)
                self.image.set_alpha(alpha)
            else:
                # Death complete — kill() removes from groups; is_alive property returns False automatically
                super().kill()

        # Sync rect
        self.rect.center = self.pos

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