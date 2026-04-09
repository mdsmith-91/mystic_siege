import random

import pygame
from pygame.math import Vector2
from src.entities.base_entity import BaseEntity
from src.entities.pickup import Pickup
from src.entities.xp_orb import XPOrb
from settings import (
    ENEMY_BASE_ATTACK_COOLDOWN,
    ENEMY_KNOCKBACK_FORCE,
    ENEMY_RETARGET_INTERVAL,
    PICKUP_CATEGORY_NONE,
    PICKUP_DROP_CHANCE_BY_CATEGORY,
    PICKUP_DROP_WEIGHTS_BY_CATEGORY,
    PICKUP_ENEMY_DROP_CATEGORY,
)
from src.utils.audio_manager import AudioManager

class Enemy(BaseEntity):
    def __init__(
        self,
        pos,
        player_list,
        all_groups: tuple,
        enemy_data: dict,
        xp_orb_group=None,
        effect_group=None,
        pickup_group=None,
    ):
        super().__init__(pos, all_groups)
        self.all_groups = all_groups
        self.xp_orb_group = xp_orb_group
        self.effect_group = effect_group
        self.pickup_group = pickup_group

        self.player_list = player_list
        self._target = None
        self._retarget_timer = 0.0
        self.last_attacker = None

        # enemy_data keys: name, hp, speed, damage, xp_value, behavior ("chase" or "ranged")
        self.name = enemy_data["name"]
        self.max_hp = enemy_data["hp"]
        self.hp = self.max_hp
        self.base_speed = enemy_data["speed"]
        self.speed_multiplier = 1.0
        self.freeze_timer = 0.0
        self.slow_effects: dict[object, dict[str, float]] = {}
        self.speed = self.base_speed
        self.damage = enemy_data["damage"]
        self.xp_value = enemy_data["xp_value"]
        self.behavior = enemy_data["behavior"]
        self.cc_immune = enemy_data.get("cc_immune", False)
        self.knockback_immune = enemy_data.get("knockback_immune", False)
        self.is_elite = False

        # Placeholder image: 32x32 surface filled with RED, first letter of name centered in WHITE
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.image.fill((255, 0, 0))  # RED background
        # Draw first letter of name
        font = pygame.font.SysFont(None, 24)
        text = font.render(self.name[0], True, (255, 255, 255))  # WHITE letter
        text_rect = text.get_rect(center=(16, 16))
        self.image.blit(text, text_rect)

        self.rect = self.image.get_rect(center=pos)

        # attack_timer: float = 0.0
        self.attack_timer = 0.0

        # attack_cooldown: float = 1.0
        self.attack_cooldown = enemy_data.get("attack_cooldown", ENEMY_BASE_ATTACK_COOLDOWN)

        # Guard against on_death being triggered twice by simultaneous projectile hits
        self._death_handled = False

        # knockback_vel: Vector2 = Vector2(0,0)  (decays each frame)
        self.knockback_vel = Vector2(0, 0)

        # Set the enemy's hp to the value from enemy_data
        self.hp = enemy_data["hp"]
        self.max_hp = enemy_data["hp"]
        self._refresh_target()

    def apply_elite_scaling(
        self,
        hp_multiplier: float,
        damage_multiplier: float,
        preserve_hp_ratio: bool = True,
    ) -> None:
        """Apply elite stat scaling once to this enemy instance."""
        if self.is_elite:
            return

        previous_max_hp = max(1.0, float(self.max_hp))
        current_hp_ratio = max(0.0, min(1.0, self.hp / previous_max_hp))

        self.max_hp = max(1, int(self.max_hp * hp_multiplier))
        if preserve_hp_ratio:
            self.hp = self.max_hp * current_hp_ratio
        else:
            self.hp = self.max_hp

        self.damage = max(1, int(self.damage * damage_multiplier))
        if hasattr(self, "projectile_damage"):
            self.projectile_damage = max(1, int(self.projectile_damage * damage_multiplier))
        if hasattr(self, "shockwave_damage"):
            self.shockwave_damage = max(1, int(self.shockwave_damage * damage_multiplier))

        self.is_elite = True

    @property
    def target(self):
        if self._target is None or not self._target.is_alive:
            self._refresh_target()
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    def _pick_target(self):
        best_player = None
        best_dist_sq = 0.0
        for player in self.player_list:
            if not player.is_alive:
                continue
            dist_sq = (player.pos - self.pos).length_squared()
            if best_player is None or dist_sq < best_dist_sq:
                best_player = player
                best_dist_sq = dist_sq
        return best_player

    def _refresh_target(self) -> None:
        """Refresh the cached target on demand instead of on every access."""
        self._target = self._pick_target()
        self._retarget_timer = ENEMY_RETARGET_INTERVAL

    def _refresh_speed(self) -> None:
        """Rebuild effective move speed from persistent enemy state."""
        if self.cc_immune:
            self.slow_effects.clear()
            self.speed = self.base_speed * self.speed_multiplier
            return
        if self.freeze_timer > 0.0:
            self.speed = 0.0
            return
        slow_multiplier = min(
            (effect["multiplier"] for effect in self.slow_effects.values()),
            default=1.0,
        )
        self.speed = self.base_speed * self.speed_multiplier * slow_multiplier

    def apply_slow(self, multiplier: float, duration: float, source: object | None = None) -> None:
        """Apply a reusable timed slow keyed by source."""
        if self.cc_immune or duration <= 0.0:
            return
        slow_source = source if source is not None else self
        self.slow_effects[slow_source] = {
            "multiplier": max(0.0, min(1.0, multiplier)),
            "remaining": duration,
        }
        self._refresh_speed()

    def remove_slow(self, source: object) -> None:
        """Remove a source-keyed slow effect without touching other control sources."""
        if source in self.slow_effects:
            del self.slow_effects[source]
            self._refresh_speed()

    def _tick_status_timers(self, dt: float) -> None:
        """Update transient enemy status timers before movement is evaluated."""
        if self.cc_immune:
            self.freeze_timer = 0.0
            self.slow_effects.clear()
            self._refresh_speed()
            return
        if self.freeze_timer > 0.0:
            self.freeze_timer = max(0.0, self.freeze_timer - dt)
        for source in list(self.slow_effects.keys()):
            effect = self.slow_effects[source]
            effect["remaining"] = max(0.0, effect["remaining"] - dt)
            if effect["remaining"] <= 0.0:
                del self.slow_effects[source]
        self._refresh_speed()

    def _compute_velocity(self, target: pygame.sprite.Sprite | None) -> Vector2:
        """Return the desired movement velocity for this frame."""
        if target is None:
            return Vector2(0, 0)
        if self.behavior == "chase":
            direction = target.pos - self.pos
            distance_sq = direction.length_squared()
            if distance_sq > 0:
                return direction * (self.speed / (distance_sq ** 0.5))
            return Vector2(0, 0)
        if self.behavior == "ranged":
            direction = target.pos - self.pos
            distance_sq = direction.length_squared()
            if distance_sq > 0:
                distance = distance_sq ** 0.5
                direction *= 1.0 / distance
                if distance > 200:
                    return direction * self.speed
            return Vector2(0, 0)
        return self.vel

    def update(self, dt):
        # Apply knockback: pos += knockback_vel * dt, knockback_vel *= (1 - 8*dt) clamped to 0
        self.pos += self.knockback_vel * dt
        self.knockback_vel *= max(0, 1 - 8 * dt)
        self._tick_status_timers(dt)
        if self._target is None or not self._target.is_alive:
            self._refresh_target()
        else:
            self._retarget_timer -= dt
            if self._retarget_timer <= 0.0:
                self._refresh_target()
        target = self.target

        self.vel = self._compute_velocity(target)

        # Update position
        super().update(dt)

        # Attack timer counts down; contact damage is handled by CollisionSystem (which
        # enforces iframes), so the timer here is kept as a hook for ranged subclasses.
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.attack_timer = self.attack_cooldown

    def take_damage(self, amount, hit_direction=None, attacker=None, knockback_force=None):
        """Override to trigger on_death after the entity is killed."""
        if self._death_handled:
            return
        if attacker is not None:
            self.last_attacker = attacker
        super().take_damage(amount)
        if hit_direction is not None and hit_direction.length() > 0:
            force = ENEMY_KNOCKBACK_FORCE if knockback_force is None else knockback_force
            if force > 0:
                self.apply_knockback(-hit_direction, force)
        if self.hp <= 0 and self.xp_orb_group is not None:
            self._death_handled = True
            self.on_death(self.xp_orb_group)

    def apply_knockback(self, direction: Vector2, force: float):
        """Apply knockback to the enemy."""
        if self.knockback_immune:
            return
        self.knockback_vel = direction * force

    def on_death(self, xp_orb_group):
        """Handle enemy death by spawning an XP orb and crediting the player."""
        AudioManager.instance().play_sfx(AudioManager.ENEMY_DEATH)
        credited_player = self.last_attacker or self.target
        if credited_player is not None:
            credited_player.kill_count += 1
        all_sprites = self.all_groups[0]
        XPOrb(self.pos, self.xp_value, (all_sprites, xp_orb_group))
        self._maybe_spawn_pickup(all_sprites)
        if self.effect_group is not None:
            from src.entities.effects import DeathExplosion
            DeathExplosion(self.pos, 40, (200, 100, 50), [self.effect_group])

    def _maybe_spawn_pickup(self, all_sprites) -> None:
        if self.pickup_group is None:
            return

        category_key = PICKUP_ENEMY_DROP_CATEGORY.get(self.name.replace(" ", ""), PICKUP_CATEGORY_NONE)
        drop_chance = PICKUP_DROP_CHANCE_BY_CATEGORY.get(category_key, 0.0)
        if drop_chance <= 0.0 or random.random() > drop_chance:
            return

        weight_map = PICKUP_DROP_WEIGHTS_BY_CATEGORY.get(category_key)
        if not weight_map:
            return

        pickup_ids = list(weight_map.keys())
        pickup_weights = list(weight_map.values())
        pickup_id = random.choices(pickup_ids, weights=pickup_weights, k=1)[0]
        Pickup(self.pos, pickup_id, (all_sprites, self.pickup_group), effect_group=self.effect_group)
