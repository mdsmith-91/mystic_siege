import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from settings import WORLD_WIDTH, WORLD_HEIGHT

class Wraith(Enemy):
    def __init__(self, pos, target, all_groups: tuple):
        # enemy_data = {name:"Wraith", hp:40, speed:120, damage:15, xp_value:10, behavior:"chase"}
        enemy_data = {
            "name": "Wraith",
            "hp": 40,
            "speed": 120,
            "damage": 15,
            "xp_value": 10,
            "behavior": "chase"
        }
        super().__init__(pos, target, all_groups, enemy_data)

        # Override image: 28x28 semi-transparent blue-gray surface (alpha=180)
        self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
        self.image.fill((100, 100, 180, 180))  # Blue-gray with alpha

        # Update rect
        self.rect = self.image.get_rect(center=pos)

        # lunge_timer: float — every 3 seconds, briefly triple speed for 0.4s
        # (lunge_active: bool, lunge_duration countdown)
        self.lunge_timer = 0.0
        self.lunge_active = False
        self.lunge_duration = 0.0

    def update(self, dt):
        # lunge_timer: float — every 3 seconds, briefly triple speed for 0.4s
        # (lunge_active: bool, lunge_duration countdown)
        if not self.lunge_active:
            self.lunge_timer -= dt
            if self.lunge_timer <= 0:
                # Start lunge
                self.lunge_active = True
                self.lunge_duration = 0.4
                self.speed *= 3  # Triple speed
        else:
            # During lunge
            self.lunge_duration -= dt
            if self.lunge_duration <= 0:
                # End lunge
                self.lunge_active = False
                self.speed /= 3  # Return to normal speed
            else:
                # Continue lunge
                pass

        # Call super.update() but after movement, handle lunge timing
        super().update(dt)

        # Note: Wraith ignores wall collision (no clamping to world bounds in update)
        # This means it can pass through walls, which is the intended behavior