import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from settings import WORLD_WIDTH, WORLD_HEIGHT

class StoneGolem(Enemy):
    def __init__(self, pos, target, all_groups: tuple):
        # enemy_data = {name:"Golem", hp:500, speed:40, damage:40, xp_value:80, behavior:"chase"}
        enemy_data = {
            "name": "Golem",
            "hp": 500,
            "speed": 40,
            "damage": 40,
            "xp_value": 80,
            "behavior": "chase"
        }
        super().__init__(pos, target, all_groups, enemy_data)

        # Override image: 48x48 dark gray rect
        self.image = pygame.Surface((48, 48), pygame.SRCALPHA)
        self.image.fill((120, 100, 80))  # Dark gray

        # Update rect
        self.rect = self.image.get_rect(center=pos)