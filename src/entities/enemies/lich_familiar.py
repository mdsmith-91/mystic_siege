import pygame
from pygame.math import Vector2
from src.entities.enemy import Enemy
from src.entities.projectile import Projectile
from settings import WORLD_WIDTH, WORLD_HEIGHT

class LichFamiliar(Enemy):
    def __init__(self, pos, target, all_groups: tuple, projectile_group=None):
        # enemy_data = {name:"Lich", hp:35, speed:90, damage:12, xp_value:12, behavior:"ranged"}
        enemy_data = {
            "name": "Lich",
            "hp": 35,
            "speed": 90,
            "damage": 12,
            "xp_value": 12,
            "behavior": "ranged"
        }
        super().__init__(pos, target, all_groups, enemy_data)

        # Behavior:
        # - Maintains orbit distance of ~200px from player
        #   orbit_angle: float — increments each frame at 45 deg/sec
        #   target_pos = player.pos + Vector2 at orbit_angle at radius 200
        #   Moves toward target_pos rather than player directly

        # - fire_timer: float — fires a slow magic orb every 2.5s at player
        #   Orb: Projectile(pos, direction_to_player, speed=120, damage=12, pierce=0, homing=False, color=(200,60,255))

        self.projectile_group = projectile_group

        self.orbit_angle = 0.0
        self.orbit_radius = 200
        self.fire_timer = 0.0
        self.fire_interval = 2.5

        # Override image: 28x28 purple rect
        self.image = pygame.Surface((28, 28), pygame.SRCALPHA)
        self.image.fill((140, 60, 160))  # Purple

        # Update rect
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        """Update the lich familiar behavior."""
        # 1. Update orbit_angle
        self.orbit_angle += 45 * dt  # 45 degrees per second

        # 2. Move toward orbit target pos
        # target_pos = player.pos + Vector2 at orbit_angle at radius 200
        target_pos = self.target.pos + Vector2(1, 0).rotate(self.orbit_angle) * self.orbit_radius

        # Move toward target_pos rather than player directly
        direction = target_pos - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
            self.vel = direction * self.speed

        # Call super.update() to handle movement and other updates
        super().update(dt)

        # 3. Tick fire_timer, spawn orb when fires
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            # Fire a slow magic orb every 2.5s at player
            # Orb: Projectile(pos, direction_to_player, speed=120, damage=12, pierce=0, homing=False, color=(200,60,255))
            direction_to_player = (self.target.pos - self.pos).normalize()

            # Create projectile — add to projectile_group so collision works
            proj_groups = [self.projectile_group] if self.projectile_group else []
            projectile = Projectile(
                pos=self.pos,
                direction=direction_to_player,
                speed=120,
                damage=12,
                groups=proj_groups,
                enemy_group_ref=None,
                pierce=0,
                homing=False,
                color=(200, 60, 255)
            )

            # Reset fire timer
            self.fire_timer = self.fire_interval