import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from settings import WORLD_WIDTH, WORLD_HEIGHT

class Skeleton(Enemy):
    def __init__(self, pos, target, all_groups: tuple):
        # enemy_data = {name:"Skeleton", hp:30, speed:80, damage:10, xp_value:5, behavior:"chase"}
        enemy_data = {
            "name": "Skeleton",
            "hp": 30,
            "speed": 80,
            "damage": 10,
            "xp_value": 5,
            "behavior": "chase"
        }
        super().__init__(pos, target, all_groups, enemy_data)

        # Add small random angle offset (±5 degrees, change every 0.5s) so they spread out
        self.angle_offset = 0.0
        self.angle_change_timer = 0.0

        # Image: 28x28 light gray rect on 32x32 transparent surface
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))  # Transparent background
        pygame.draw.rect(self.image, (200, 200, 200), (2, 2, 28, 28))  # Light gray rect

        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        # Add small random angle offset (±5 degrees, change every 0.5s) so they spread out
        self.angle_change_timer += dt
        if self.angle_change_timer >= 0.5:
            self.angle_offset = (pygame.time.get_ticks() % 1000) / 1000.0 * 10 - 5  # ±5 degrees
            self.angle_change_timer = 0.0

        # Apply the angle offset to movement
        direction = self.target.pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            # Apply angle offset to direction
            angle = direction.angle_to(Vector2(1, 0))
            angle += self.angle_offset
            new_direction = Vector2(1, 0).rotate(angle)
            self.vel = new_direction * self.speed

        # Call parent update method
        super().update(dt)