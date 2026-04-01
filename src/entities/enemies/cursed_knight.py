import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from settings import WORLD_WIDTH, WORLD_HEIGHT

class CursedKnight(Enemy):
    def __init__(self, pos, target, all_groups: tuple):
        # enemy_data = {name:"Knight", hp:80, speed:110, damage:20, xp_value:15, behavior:"chase"}
        enemy_data = {
            "name": "Knight",
            "hp": 80,
            "speed": 110,
            "damage": 20,
            "xp_value": 15,
            "behavior": "chase"
        }
        super().__init__(pos, target, all_groups, enemy_data)

        # Shield mechanic
        self.shield_facing = Vector2(1, 0)  # Points toward player each frame

        # Override image: 32x32 steel-gray rect with a small blue square on the "front"
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.image.fill((100, 100, 100))  # Steel-gray

        # Draw small blue square on front
        pygame.draw.rect(self.image, (0, 100, 255), (24, 12, 6, 6))  # Blue square on right side

        # Update rect
        self.rect = self.image.get_rect(center=pos)

    def take_damage(self, amount, hit_direction=None):
        """Apply damage with shield mechanic."""
        # If hit_direction is provided and we have a shield
        if hit_direction is not None and hasattr(self, 'shield_facing'):
            # Calculate angle between shield_facing and hit_direction
            angle = self.shield_facing.angle_to(hit_direction)

            # If angle < 60 degrees (frontal): apply 20% of damage (80% reduction)
            if abs(angle) < 60:
                amount = amount * 0.2  # 80% damage reduction
        else:
            # No shield or no hit direction, apply full damage
            pass

        # Call parent take_damage
        super().take_damage(amount)

    def update(self, dt):
        """Update the cursed knight."""
        # Update shield_facing = (target.pos - self.pos).normalize()
        if hasattr(self, 'target') and self.target:
            direction = self.target.pos - self.pos
            if direction.length() > 0:
                self.shield_facing = direction.normalize()
            else:
                self.shield_facing = Vector2(1, 0)

        # Call super.update() to handle movement and other updates
        super().update(dt)

        # Update visual representation to show shield facing
        # Redraw the image to show the shield facing correctly
        self.image.fill((100, 100, 100))  # Steel-gray background

        # Draw small blue square on front (determined by shield_facing)
        # For simplicity, we'll draw it on the right side (assuming facing right means right side is front)
        # In a real implementation, you'd want to be more precise about which side is front
        pygame.draw.rect(self.image, (0, 100, 255), (24, 12, 6, 6))  # Blue square on right side