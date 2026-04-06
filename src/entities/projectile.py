import pygame
from pygame.math import Vector2
import random
from settings import WORLD_WIDTH, WORLD_HEIGHT, CRIT_MULTIPLIER
import math

class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, direction: Vector2, speed: float, damage: float,
                 groups, enemy_group_ref, pierce: int = 0, homing: bool = False,
                 color: tuple = (200, 100, 255), target_enemy=None,
                 is_enemy_projectile: bool = False, owner_crit_chance: float = 0.0,
                 owner=None, lifetime: float = 4.0,
                 size: tuple[int, int] | None = None,
                 draw_shape: str = "circle",
                 rotate_to_direction: bool = False):
        super().__init__(groups)

        # direction normalized on init
        self.direction = direction.normalize()
        self.draw_shape = draw_shape
        self.projectile_size = size or (10, 10)
        self.rotate_to_direction = rotate_to_direction
        self.color = color
        self.image = self._build_image()
        self.rect = self.image.get_rect(center=pos)

        # enemies_hit: set() — tracks enemy ids already hit (for pierce)
        self.enemies_hit = set()

        # lifetime: float (auto-destroy after this many seconds)
        self.lifetime = lifetime

        # Additional attributes
        self.speed = speed
        self.damage = damage
        self.enemy_group_ref = enemy_group_ref
        self.pierce = pierce
        self.homing = homing
        self.pos = Vector2(pos)

        # Store the original target enemy (for homing projectiles that should not track new enemies)
        self.original_target = target_enemy

        # True for projectiles fired by enemies (hit player, not enemies)
        self.is_enemy_projectile = is_enemy_projectile

        self.owner_crit_chance = owner_crit_chance
        self.owner = owner

    def _build_image(self) -> pygame.Surface:
        width, height = self.projectile_size
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        if self.draw_shape == "arrow":
            shaft_width = max(2, height // 3)
            shaft_rect = pygame.Rect(0, 0, max(1, width - height), shaft_width)
            shaft_rect.centery = height // 2
            pygame.draw.rect(surface, self.color, shaft_rect)
            head_points = [
                (width - 1, height // 2),
                (max(0, width - height), 0),
                (max(0, width - height), height - 1),
            ]
            pygame.draw.polygon(surface, self.color, head_points)
        else:
            radius = min(width, height) // 2
            pygame.draw.circle(surface, self.color, (width // 2, height // 2), radius)

        if self.rotate_to_direction:
            angle = -self.direction.angle_to(Vector2(1, 0))
            surface = pygame.transform.rotate(surface, angle)

        return surface

    def update(self, dt):
        # Home toward original target only while it's still alive — fly straight once it dies
        if self.homing and self.original_target and self.original_target.alive():
            target_direction = (self.original_target.pos - self.pos).normalize()
            angle_diff = self.direction.angle_to(target_direction)

            # Limit turning speed to 120 degrees per second
            max_turn = 120 * dt
            if angle_diff > max_turn:
                angle_diff = max_turn
            elif angle_diff < -max_turn:
                angle_diff = -max_turn

            self.direction = self.direction.rotate(angle_diff)

        # pos += direction * speed * dt
        self.pos += self.direction * self.speed * dt

        # Update rect position
        self.rect.center = self.pos

        # lifetime -= dt; if <= 0: kill()
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()

        # If pos outside world bounds: kill()
        if (self.pos.x < 0 or self.pos.x > WORLD_WIDTH or
            self.pos.y < 0 or self.pos.y > WORLD_HEIGHT):
            self.kill()

    def on_hit(self, enemy, effect_group=None):
        """Handle projectile hitting an enemy."""
        if enemy.sprite_id in self.enemies_hit:
            return

        self.enemies_hit.add(enemy.sprite_id)

        is_crit = random.random() < self.owner_crit_chance
        actual_damage = self.damage * (CRIT_MULTIPLIER if is_crit else 1.0)

        # hit_direction: from enemy back toward the projectile source, for shield checks
        enemy.take_damage(actual_damage, hit_direction=-self.direction, attacker=self.owner)

        if effect_group is not None:
            from src.entities.effects import DamageNumber, HitSpark
            DamageNumber(enemy.pos - Vector2(0, 20), actual_damage, [effect_group], is_crit=is_crit)
            HitSpark(enemy.pos, (255, 200, 50), [effect_group])

        if self.pierce <= 0:
            self.kill()
        else:
            self.pierce -= 1
