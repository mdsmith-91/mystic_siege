import pygame
from pygame.math import Vector2
from src.entities.base_entity import BaseEntity
from src.entities.xp_orb import XPOrb
from settings import WORLD_WIDTH, WORLD_HEIGHT

class Enemy(BaseEntity):
    def __init__(self, pos, target, all_groups: tuple, enemy_data: dict, xp_orb_group=None):
        super().__init__(pos, all_groups)
        self.all_groups = all_groups
        self.xp_orb_group = xp_orb_group

        # target = player reference
        self.target = target

        # enemy_data keys: name, hp, speed, damage, xp_value, behavior ("chase" or "ranged")
        self.name = enemy_data["name"]
        self.max_hp = enemy_data["hp"]
        self.hp = self.max_hp
        self.speed = enemy_data["speed"]
        self.damage = enemy_data["damage"]
        self.xp_value = enemy_data["xp_value"]
        self.behavior = enemy_data["behavior"]

        # Placeholder image: 32x32 surface filled with RED, first letter of name centered in WHITE
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.image.fill((255, 0, 0))  # RED background
        # Draw first letter of name
        font = pygame.font.SysFont(None, 24)
        text = font.render(self.name[0], True, (255, 255, 255))  # WHITE letter
        text_rect = text.get_rect(center=(16, 16))
        self.image.blit(text, text_rect)

        self.rect = self.image.get_rect(center=pos)

        # attack_timer: float = 0.0
        self.attack_timer = 0.0

        # attack_cooldown: float = 1.0
        self.attack_cooldown = 1.0

        # knockback_vel: Vector2 = Vector2(0,0)  (decays each frame)
        self.knockback_vel = Vector2(0, 0)

        # Set the enemy's hp to the value from enemy_data
        self.hp = enemy_data["hp"]
        self.max_hp = enemy_data["hp"]

    def update(self, dt):
        # Apply knockback: pos += knockback_vel * dt, knockback_vel *= (1 - 8*dt) clamped to 0
        self.pos += self.knockback_vel * dt
        self.knockback_vel *= max(0, 1 - 8 * dt)

        # If behavior == "chase": direction toward target, move
        # If behavior == "ranged": stop at 200px from target, face target
        if self.behavior == "chase":
            direction = self.target.pos - self.pos
            if direction.length() > 0:
                direction = direction.normalize()
                self.vel = direction * self.speed
        elif self.behavior == "ranged":
            direction = self.target.pos - self.pos
            distance = direction.length()
            if distance > 0:
                direction = direction.normalize()
                # Stop at 200px from target
                if distance > 200:
                    self.vel = direction * self.speed
                else:
                    self.vel = Vector2(0, 0)

        # Update position
        super().update(dt)

        # Attack timer counts down; when 0 and overlapping target: deal damage, always reset
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            if self.rect.colliderect(self.target.rect):
                self.target.take_damage(self.damage)
            self.attack_timer = self.attack_cooldown

    def take_damage(self, amount):
        """Override to trigger on_death after the entity is killed."""
        super().take_damage(amount)
        # Check if the entity is now dead (hp <= 0) and was not already dead
        if self.hp <= 0 and self.xp_orb_group is not None:
            self.on_death(self.xp_orb_group)

    def apply_knockback(self, direction: Vector2, force: float):
        """Apply knockback to the enemy."""
        self.knockback_vel = direction * force

    def on_death(self, xp_orb_group):
        """Handle enemy death by spawning an XP orb."""
        all_sprites = self.all_groups[0]
        XPOrb(self.pos, self.xp_value, (all_sprites, xp_orb_group))