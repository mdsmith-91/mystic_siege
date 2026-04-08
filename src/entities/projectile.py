import pygame
from pygame.math import Vector2
import random
from settings import (
    WORLD_WIDTH, WORLD_HEIGHT, CRIT_MULTIPLIER,
    THROWING_AXES_HANDLE_COLOR, THROWING_AXES_GUARD_COLOR, THROWING_AXES_OUTLINE_COLOR,
)

class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, direction: Vector2, speed: float, damage: float,
                 groups, enemy_group_ref, pierce: int = 0, homing: bool = False,
                 color: tuple = (200, 100, 255), target_enemy=None,
                 is_enemy_projectile: bool = False, owner_crit_chance: float = 0.0,
                 owner=None, lifetime: float = 4.0,
                 size: tuple[int, int] | None = None,
                 draw_shape: str = "circle",
                 rotate_to_direction: bool = False,
                 spin_speed: float = 0.0):
        super().__init__(groups)

        # direction normalized on init
        self.direction = direction.normalize()
        self.draw_shape = draw_shape
        self.projectile_size = size or (10, 10)
        self.rotate_to_direction = rotate_to_direction
        self.color = color
        self.spin_speed = spin_speed
        self._spin_angle = 0.0
        self._base_image = self._build_image()
        self.image = self._base_image
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
            # All dimensions scale with height so tuning LONGBOW_PROJECTILE_SIZE
            # in settings.py automatically re-proportions every zone.
            mid = height // 2
            nock_x = height // 2          # V-tip of fletching (where wings converge)
            head_x = width - height       # x where arrowhead base begins
            # Shaft: thin 2px centred stick from nock to arrowhead base
            pygame.draw.rect(surface, self.color,
                pygame.Rect(nock_x, mid - 1, head_x - nock_x, 2))
            # Arrowhead: right-pointing filled triangle
            pygame.draw.polygon(surface, self.color, [
                (width - 1, mid),       # tip
                (head_x, 1),            # shoulder top
                (head_x, height - 2),   # shoulder bottom
            ])
            # Fletching: 2px-wide V-wings spreading from the nock to the tail corners
            pygame.draw.line(surface, self.color,
                (nock_x - 1, mid), (0, 1), 2)
            pygame.draw.line(surface, self.color,
                (nock_x - 1, mid), (0, height - 2), 2)
        elif self.draw_shape == "axe":
            # Hand axe pointing RIGHT — rotate_to_direction orients it toward the target;
            # spin_speed tumbles it continuously in flight.
            # Layers: glow bloom → handle → guard/bolster → outlined blade → edge highlight
            mid = height // 2
            handle_w = width // 2
            blade_back_x = handle_w - 1        # socket edge of blade, overlaps guard slightly
            blade_front_x = width - 1          # cutting edge (rightmost column)
            blade_back_top = mid - height // 4  # top of socket (narrower back)
            blade_back_bot = mid + height // 4  # bottom of socket
            blade_front_top = 1                 # top of cutting edge (nearly full height)
            blade_front_bot = height - 2        # bottom of cutting edge

            # 1. Handle (dark wood, wider than before for readability)
            handle_h = max(3, height // 4)
            pygame.draw.rect(surface, THROWING_AXES_HANDLE_COLOR,
                pygame.Rect(0, mid - handle_h // 2, handle_w, handle_h))

            # 2. Guard/bolster at handle-to-blade joint (dark iron accent)
            guard_h = max(5, height // 3 + 1)
            pygame.draw.rect(surface, THROWING_AXES_GUARD_COLOR,
                pygame.Rect(blade_back_x - 2, mid - guard_h // 2, 4, guard_h))

            # 3. Blade: fill in outline color first, then inset fill in blade color
            #    — net effect is a 1px dark border on all blade edges
            blade_pts = [
                (blade_back_x,  blade_back_top),
                (blade_front_x, blade_front_top),
                (blade_front_x, blade_front_bot),
                (blade_back_x,  blade_back_bot),
            ]
            fill_pts = [
                (blade_back_x + 1,  blade_back_top + 1),
                (blade_front_x - 1, blade_front_top + 1),
                (blade_front_x - 1, blade_front_bot - 1),
                (blade_back_x + 1,  blade_back_bot - 1),
            ]
            pygame.draw.polygon(surface, THROWING_AXES_OUTLINE_COLOR, blade_pts)
            pygame.draw.polygon(surface, self.color, fill_pts)

            # 4. Edge highlight: 2px bright stripe on cutting edge to convey a sharp steel bevel
            highlight = tuple(min(255, c + 70) for c in self.color)
            pygame.draw.line(surface, highlight,
                (blade_front_x - 2, blade_front_top + 2),
                (blade_front_x - 2, blade_front_bot - 2), 2)
        else:
            radius = min(width, height) // 2
            pygame.draw.circle(surface, self.color, (width // 2, height // 2), radius)

        if self.rotate_to_direction:
            # Negate angle: Vector2.angle_to() uses Cartesian Y-up convention,
            # but pygame.transform.rotate() uses screen Y-down convention.
            # Without negation, non-horizontal arrows rotate in the wrong direction.
            angle = -Vector2(1, 0).angle_to(self.direction)
            surface = pygame.transform.rotate(surface, angle)

        return surface

    def update(self, dt):
        # Home toward original target only while it's still alive — fly straight once it dies
        if self.homing and self.original_target and self.original_target.alive():
            target_offset = self.original_target.pos - self.pos
            if target_offset.length_squared() > 0:
                target_direction = target_offset.normalize()
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

        # Continuously spin the image when spin_speed is set (e.g. throwing axe tumble)
        if self.spin_speed != 0.0:
            self._spin_angle = (self._spin_angle + self.spin_speed * dt) % 360
            self.image = pygame.transform.rotate(self._base_image, self._spin_angle)
            self.rect = self.image.get_rect(center=self.rect.center)

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
