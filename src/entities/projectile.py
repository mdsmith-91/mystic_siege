import pygame
from pygame.math import Vector2
import random
from settings import (
    WORLD_WIDTH, WORLD_HEIGHT, CRIT_MULTIPLIER,
    LONGBOW_PIN_SHOT_DURATION,
    THROWING_AXES_HANDLE_COLOR, THROWING_AXES_GUARD_COLOR, THROWING_AXES_OUTLINE_COLOR,
    THROWING_AXES_OUTLINE_WIDTH, THROWING_AXES_EDGE_HIGHLIGHT_WIDTH,
    THROWING_AXES_RICOCHET_RANGE, THROWING_AXES_RICOCHET_DAMAGE_PCT,
)

class Projectile(pygame.sprite.Sprite):
    ORDER_COLLISION_TARGETS = True

    def __init__(self, pos, direction: Vector2, speed: float, damage: float,
                 groups, enemy_group_ref, pierce: int = 0, homing: bool = False,
                 color: tuple = (200, 100, 255), target_enemy=None,
                 is_enemy_projectile: bool = False, owner_crit_chance: float = 0.0,
                 owner=None, lifetime: float = 4.0,
                 size: tuple[int, int] | None = None,
                 draw_shape: str = "circle",
                 rotate_to_direction: bool = False,
                 spin_speed: float = 0.0,
                 pin_shot: bool = False,
                 ricochet: bool = False):
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
        self.pin_shot = pin_shot
        self.ricochet = ricochet

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
            # Layers: handle → guard/bolster → outlined blade (6-point) → edge highlight
            #
            # All small offsets are derived from px (1 at the 18×18 reference canvas,
            # 2 at 36×36, etc.) so changing THROWING_AXES_PROJECTILE_SIZE in settings.py
            # uniformly rescales every detail.  THROWING_AXES_OUTLINE_WIDTH and
            # THROWING_AXES_EDGE_HIGHLIGHT_WIDTH tune border/bevel proportions independently.
            mid = height // 2
            px = max(1, min(width, height) // 18)   # scale factor relative to 18×18 reference
            ow = THROWING_AXES_OUTLINE_WIDTH * px    # blade outline inset thickness
            ehw = THROWING_AXES_EDGE_HIGHLIGHT_WIDTH * px  # edge bevel stripe width

            # Shaft runs along the lower portion of the canvas so the head sweeps upward,
            # matching a real hatchet/throwing-axe profile.
            shaft_y = mid + height // 5        # handle y-center, offset toward bottom
            handle_end = (width * 5) // 9      # longer grip (~55% of width)
            hb = handle_end + px               # head-back x-coordinate

            # 1. Handle (longer dark-wood shaft, offset below center)
            handle_h = max(2 * px, height // 6)
            pygame.draw.rect(surface, THROWING_AXES_HANDLE_COLOR,
                pygame.Rect(0, shaft_y - handle_h // 2, handle_end + 2 * px, handle_h))

            # 2. Guard/bolster at handle-to-blade joint (dark iron accent)
            guard_h = max(4 * px, height // 3)
            guard_w = 3 * px
            pygame.draw.rect(surface, THROWING_AXES_GUARD_COLOR,
                pygame.Rect(handle_end - px, shaft_y - guard_h // 2, guard_w, guard_h))

            # 3. Blade: 6-point polygon — compact hatchet head extending mostly above
            #    the shaft, with a small lower beard.  Blade height ≈ 10px on an 18px
            #    canvas so it reads as a stubby hand-axe, not an elongated cleaver.
            #    socket-top → top-spike → cutting-top → cutting-bot → beard → socket-bot
            q = height // 4    # quarter-height unit used for blade sizing
            blade_pts = [
                (hb,          shaft_y - q),           # socket top
                (hb + px,     q),                      # top spike/corner
                (width - px,  q),                      # cutting-edge top (flat top rail)
                (width - px,  height - q),             # cutting-edge bottom
                (hb + px,     height - q - px),        # beard
                (hb,          shaft_y + height // 6),  # socket bottom (small lower extension)
            ]
            # Inset fill produces ow-px dark border around all blade edges
            fill_pts = [
                (hb + ow,       shaft_y - q + ow),
                (hb + 2 * ow,   q + ow),
                (width - px - ow,  q + ow),
                (width - px - ow,  height - q - ow),
                (hb + 2 * ow,   height - q - 2 * ow),
                (hb + ow,       shaft_y + height // 6 - ow),
            ]
            pygame.draw.polygon(surface, THROWING_AXES_OUTLINE_COLOR, blade_pts)
            pygame.draw.polygon(surface, self.color, fill_pts)

            # 4. Edge highlight: bright bevel stripe on cutting edge for a sharp steel look
            highlight = tuple(min(255, c + 70) for c in self.color)
            highlight_x = width - px - ow - ehw        # inside the fill polygon, near cutting edge
            pygame.draw.line(surface, highlight,
                (highlight_x, q + 2 * px), (highlight_x, height - q - 2 * px), ehw)
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

        # Pin Shot: crit arrows briefly root the target (Longbow L5).
        if self.pin_shot and is_crit and enemy.alive():
            enemy.freeze_timer = max(getattr(enemy, "freeze_timer", 0.0), LONGBOW_PIN_SHOT_DURATION)
            if hasattr(enemy, "_refresh_speed"):
                enemy._refresh_speed()

        # Ricochet: axes that kill bounce to the nearest enemy (ThrowingAxes L5).
        if self.ricochet and not enemy.alive():
            bounce_pos = enemy.pos.copy()
            ricochet_sq = THROWING_AXES_RICOCHET_RANGE * THROWING_AXES_RICOCHET_RANGE
            nearest = None
            nearest_sq = float("inf")
            for candidate in self.enemy_group_ref:
                if not candidate.alive():
                    continue
                dist_sq = (candidate.pos - bounce_pos).length_squared()
                if dist_sq <= ricochet_sq and dist_sq < nearest_sq:
                    nearest_sq = dist_sq
                    nearest = candidate
            if nearest is not None:
                bounce_dmg = actual_damage * THROWING_AXES_RICOCHET_DAMAGE_PCT
                nearest.take_damage(bounce_dmg, hit_direction=None, attacker=self.owner)
                if effect_group is not None:
                    from src.entities.effects import DamageNumber, HitSpark
                    DamageNumber(nearest.pos - Vector2(0, 20), bounce_dmg, [effect_group])
                    HitSpark(nearest.pos, (255, 180, 60), [effect_group])

        if self.pierce <= 0:
            self.kill()
        else:
            self.pierce -= 1
