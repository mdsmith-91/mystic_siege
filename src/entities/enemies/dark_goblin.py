import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from settings import WORLD_WIDTH, WORLD_HEIGHT

class DarkGoblin(Enemy):
    def __init__(self, pos, target, all_groups: tuple, xp_orb_group=None):
        enemy_data = {
            "name": "Goblin",
            "hp": 20,
            "speed": 160,
            "damage": 8,
            "xp_value": 4,
            "behavior": "chase"
        }
        super().__init__(pos, target, all_groups, enemy_data, xp_orb_group)

        # Image: 24x24 green rect on 32x32 transparent surface (smaller = feels faster)
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.image.fill((0, 0, 0, 0))  # Transparent background
        pygame.draw.rect(self.image, (0, 200, 0), (4, 4, 24, 24))  # Green rect

        self.rect = self.image.get_rect(center=pos)