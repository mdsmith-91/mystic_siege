import pygame
from collections import deque
from pygame.math import Vector2
from settings import (
    ARCANE_BOLT_PROJECTILE_SIZE,
    ARCANE_BOLT_HITBOX_SIZE,
    ARCANE_BOLT_OUTER_GLOW_RADIUS,
    ARCANE_BOLT_OUTER_GLOW_COLOR,
    ARCANE_BOLT_OUTER_GLOW_ALPHA,
    ARCANE_BOLT_MID_GLOW_RADIUS,
    ARCANE_BOLT_MID_GLOW_COLOR,
    ARCANE_BOLT_MID_GLOW_ALPHA,
    ARCANE_BOLT_CORE_RADIUS,
    ARCANE_BOLT_CORE_COLOR,
    ARCANE_BOLT_CENTER_RADIUS,
    ARCANE_BOLT_CENTER_COLOR,
    ARCANE_BOLT_TRAIL_LENGTH,
    ARCANE_BOLT_TRAIL_RECORD_INTERVAL,
    ARCANE_BOLT_EXPLOSION_RADIUS,
    ARCANE_BOLT_EXPLOSION_DAMAGE_PCT,
    ARCANE_BOLT_EXPLOSION_COLOR,
)
from src.entities.projectile import Projectile


class ArcaneBoltProjectile(Projectile):
    """Arcane Bolt projectile with a layered magical orb visual and fading trail."""

    def __init__(self, pos, direction: Vector2, speed: float, damage: float,
                 groups, enemy_group_ref, pierce: int = 0, homing: bool = False,
                 color: tuple = (160, 80, 255), target_enemy=None,
                 owner_crit_chance: float = 0.0, owner=None, lifetime: float = 4.0,
                 explode_on_kill: bool = False):
        super().__init__(
            pos=pos,
            direction=direction,
            speed=speed,
            damage=damage,
            groups=groups,
            enemy_group_ref=enemy_group_ref,
            pierce=pierce,
            homing=homing,
            color=color,
            target_enemy=target_enemy,
            owner_crit_chance=owner_crit_chance,
            owner=owner,
            lifetime=lifetime,
            size=ARCANE_BOLT_PROJECTILE_SIZE,
        )
        # Restore collision rect to original hitbox size — the visual surface is larger
        # than the hit zone and should not widen collision detection.
        self.rect = pygame.Rect(0, 0, *ARCANE_BOLT_HITBOX_SIZE)
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Trail: bounded history of world positions for the arcane trail effect
        self._trail: deque[Vector2] = deque(maxlen=ARCANE_BOLT_TRAIL_LENGTH)
        self._trail_timer: float = 0.0

        # L5 capstone: detonate on kill
        self.explode_on_kill = explode_on_kill

    def _build_image(self) -> pygame.Surface:
        """Build a 4-layer arcane orb: outer bloom, mid glow, core, center sparkle."""
        w, h = ARCANE_BOLT_PROJECTILE_SIZE
        surface = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, h // 2

        # Layer 1: outer soft violet bloom
        pygame.draw.circle(
            surface,
            (*ARCANE_BOLT_OUTER_GLOW_COLOR, ARCANE_BOLT_OUTER_GLOW_ALPHA),
            (cx, cy),
            ARCANE_BOLT_OUTER_GLOW_RADIUS,
        )
        # Layer 2: saturated purple mid glow
        pygame.draw.circle(
            surface,
            (*ARCANE_BOLT_MID_GLOW_COLOR, ARCANE_BOLT_MID_GLOW_ALPHA),
            (cx, cy),
            ARCANE_BOLT_MID_GLOW_RADIUS,
        )
        # Layer 3: bright lavender core
        pygame.draw.circle(
            surface,
            (*ARCANE_BOLT_CORE_COLOR, 255),
            (cx, cy),
            ARCANE_BOLT_CORE_RADIUS,
        )
        # Layer 4: near-white center sparkle
        pygame.draw.circle(
            surface,
            (*ARCANE_BOLT_CENTER_COLOR, 255),
            (cx, cy),
            ARCANE_BOLT_CENTER_RADIUS,
        )
        return surface

    def on_hit(self, enemy, effect_group=None) -> None:
        """Handle hit; detonate on kill at L5."""
        kill_pos = enemy.pos.copy()
        super().on_hit(enemy, effect_group)

        if not self.explode_on_kill or enemy.alive():
            return

        # Enemy was killed by this bolt — deal splash damage to nearby enemies.
        radius_sq = ARCANE_BOLT_EXPLOSION_RADIUS * ARCANE_BOLT_EXPLOSION_RADIUS
        splash_damage = self.damage * ARCANE_BOLT_EXPLOSION_DAMAGE_PCT
        for nearby in list(self.enemy_group_ref):
            if not nearby.alive():
                continue
            if (nearby.pos - kill_pos).length_squared() <= radius_sq:
                nearby.take_damage(splash_damage, hit_direction=None, attacker=self.owner)

        if effect_group is not None:
            from src.entities.effects import DeathExplosion
            DeathExplosion(
                kill_pos,
                int(ARCANE_BOLT_EXPLOSION_RADIUS),
                ARCANE_BOLT_EXPLOSION_COLOR,
                [effect_group],
            )

    def update(self, dt: float) -> None:
        super().update(dt)
        # Record trail positions while the projectile is alive
        if self.alive():
            self._trail_timer += dt
            if self._trail_timer >= ARCANE_BOLT_TRAIL_RECORD_INTERVAL:
                self._trail.append(self.pos.copy())
                self._trail_timer = 0.0
