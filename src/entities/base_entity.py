import pygame
from pygame.math import Vector2
from settings import (
    ENTITY_HEALTH_BAR_BG_COLOR,
    ENTITY_HEALTH_BAR_HEIGHT,
    ENTITY_HEALTH_BAR_HIGH_COLOR,
    ENTITY_HEALTH_BAR_LOW_COLOR,
    ENTITY_HEALTH_BAR_MED_COLOR,
    ENTITY_HEALTH_BAR_WIDTH,
    ENTITY_HEALTH_BAR_Y_OFFSET,
)

class BaseEntity(pygame.sprite.Sprite):
    def __init__(self, pos: tuple, groups: tuple):
        super().__init__(groups)
        self.pos = Vector2(pos)
        self.vel = Vector2(0, 0)
        self.hp = 0
        self.max_hp = 0
        self.speed = 0
        self.sprite_id = id(self)

        # image and rect must be set by subclasses before calling super().__init__
        # This is a placeholder - subclasses should set these before calling super().__init__()

    def update(self, dt: float):
        """Update position based on velocity."""
        self.pos += self.vel * dt
        # Sync rect.center to pos
        self.rect.center = self.pos

    def take_damage(self, amount: float):
        """Apply damage to the entity, accounting for armor."""
        # Reduce damage by armor percentage (e.g. armor=15 means 15% reduction)
        armor = getattr(self, 'armor', 0)
        damage = amount * (1.0 - armor / 100.0) if armor else amount

        self.hp -= damage
        if self.hp <= 0:
            self.hp = 0
            self.kill()

    def heal(self, amount: float):
        """Heal the entity."""
        self.hp = min(self.max_hp, self.hp + amount)

    def draw_health_bar(self, surface, offset: Vector2):
        """Draw a health bar above the entity."""
        if self.hp < self.max_hp:
            bar_x = self.rect.centerx - ENTITY_HEALTH_BAR_WIDTH // 2
            bar_y = self.rect.top - ENTITY_HEALTH_BAR_Y_OFFSET

            # Draw background
            pygame.draw.rect(
                surface,
                ENTITY_HEALTH_BAR_BG_COLOR,
                (
                    bar_x - offset.x,
                    bar_y - offset.y,
                    ENTITY_HEALTH_BAR_WIDTH,
                    ENTITY_HEALTH_BAR_HEIGHT,
                ),
            )

            # Calculate filled portion
            hp_ratio = self.hp / self.max_hp
            filled_width = int(ENTITY_HEALTH_BAR_WIDTH * hp_ratio)

            # Set color based on health percentage
            if hp_ratio > 0.5:
                color = ENTITY_HEALTH_BAR_HIGH_COLOR
            elif hp_ratio > 0.25:
                color = ENTITY_HEALTH_BAR_MED_COLOR
            else:
                color = ENTITY_HEALTH_BAR_LOW_COLOR

            # Draw filled portion
            pygame.draw.rect(
                surface,
                color,
                (
                    bar_x - offset.x,
                    bar_y - offset.y,
                    filled_width,
                    ENTITY_HEALTH_BAR_HEIGHT,
                ),
            )

    @property
    def is_alive(self):
        """Return if the entity is alive."""
        return self.alive()
