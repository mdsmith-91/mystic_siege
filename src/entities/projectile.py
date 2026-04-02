import pygame
from pygame.math import Vector2
import random
from settings import WORLD_WIDTH, WORLD_HEIGHT, CRIT_MULTIPLIER
import math

class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, direction: Vector2, speed: float, damage: float,
                 groups, enemy_group_ref, pierce: int = 0, homing: bool = False,
                 color: tuple = (200, 100, 255), target_enemy=None,
                 is_enemy_projectile: bool = False, owner_crit_chance: float = 0.0):
        super().__init__(groups)

        # image: 10x10 circle surface with given color
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (5, 5), 5)

        self.rect = self.image.get_rect(center=pos)

        # direction normalized on init
        self.direction = direction.normalize()

        # enemies_hit: set() — tracks enemy ids already hit (for pierce)
        self.enemies_hit = set()

        # lifetime: float = 4.0  (auto-destroy after 4 seconds)
        self.lifetime = 4.0

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
        enemy.take_damage(actual_damage, hit_direction=-self.direction)

        if effect_group is not None:
            from src.entities.effects import DamageNumber, HitSpark
            DamageNumber(enemy.pos - Vector2(0, 20), actual_damage, [effect_group], is_crit=is_crit)
            HitSpark(enemy.pos, (255, 200, 50), [effect_group])

        if self.pierce <= 0:
            self.kill()
        else:
            self.pierce -= 1