import pygame
from pygame.math import Vector2
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

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
            # Calculate health bar dimensions
            bar_width = 30
            bar_height = 4
            bar_x = self.rect.centerx - bar_width // 2
            bar_y = self.rect.top - 10

            # Draw background
            pygame.draw.rect(surface, (50, 50, 50), (bar_x - offset.x, bar_y - offset.y, bar_width, bar_height))

            # Calculate filled portion
            hp_ratio = self.hp / self.max_hp
            filled_width = int(bar_width * hp_ratio)

            # Set color based on health percentage
            if hp_ratio > 0.5:
                color = (60, 200, 80)  # Green
            elif hp_ratio > 0.25:
                color = (255, 255, 0)  # Yellow
            else:
                color = (220, 60, 60)  # Red

            # Draw filled portion
            pygame.draw.rect(surface, color, (bar_x - offset.x, bar_y - offset.y, filled_width, bar_height))

    @property
    def is_alive(self):
        """Return if the entity is alive."""
        return self.alive()