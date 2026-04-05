import pygame
from pygame.math import Vector2
from src.entities.base_entity import BaseEntity
from src.entities.xp_orb import XPOrb
from settings import WORLD_WIDTH, WORLD_HEIGHT, ENEMY_KNOCKBACK_FORCE, ENEMY_RETARGET_INTERVAL
from src.utils.audio_manager import AudioManager

class Enemy(BaseEntity):
    def __init__(self, pos, player_list, all_groups: tuple, enemy_data: dict, xp_orb_group=None, effect_group=None):
        super().__init__(pos, all_groups)
        self.all_groups = all_groups
        self.xp_orb_group = xp_orb_group
        self.effect_group = effect_group

        self.player_list = player_list
        self._target = None
        self._retarget_timer = 0.0
        self.last_attacker = None

        # enemy_data keys: name, hp, speed, damage, xp_value, behavior ("chase" or "ranged")
        self.name = enemy_data["name"]
        self.max_hp = enemy_data["hp"]
        self.hp = self.max_hp
        self.speed = enemy_data["speed"]
        self.damage = enemy_data["damage"]
        self.xp_value = enemy_data["xp_value"]
        self.behavior = enemy_data["behavior"]

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
        self.attack_cooldown = 1.0

        # Guard against on_death being triggered twice by simultaneous projectile hits
        self._death_handled = False

        # knockback_vel: Vector2 = Vector2(0,0)  (decays each frame)
        self.knockback_vel = Vector2(0, 0)

        # Set the enemy's hp to the value from enemy_data
        self.hp = enemy_data["hp"]
        self.max_hp = enemy_data["hp"]
        self._refresh_target()

    @property
    def target(self):
        if self._target is None or not self._target.is_alive:
            self._refresh_target()
        return self._target

    @target.setter
    def target(self, value):
        self._target = value

    def _pick_target(self):
        alive_players = [player for player in self.player_list if player.is_alive]
        if not alive_players:
            return None
        return min(alive_players, key=lambda player: (player.pos - self.pos).length_squared())

    def _refresh_target(self) -> None:
        """Refresh the cached target on demand instead of on every access."""
        self._target = self._pick_target()
        self._retarget_timer = ENEMY_RETARGET_INTERVAL

    def update(self, dt):
        # Apply knockback: pos += knockback_vel * dt, knockback_vel *= (1 - 8*dt) clamped to 0
        self.pos += self.knockback_vel * dt
        self.knockback_vel *= max(0, 1 - 8 * dt)
        if self._target is None or not self._target.is_alive:
            self._refresh_target()
        else:
            self._retarget_timer -= dt
            if self._retarget_timer <= 0.0:
                self._refresh_target()
        target = self.target

        # If behavior == "chase": direction toward target, move
        # If behavior == "ranged": stop at 200px from target, face target
        if target is None:
            self.vel = Vector2(0, 0)
        elif self.behavior == "chase":
            direction = target.pos - self.pos
            if direction.length() > 0:
                direction = direction.normalize()
                self.vel = direction * self.speed
        elif self.behavior == "ranged":
            direction = target.pos - self.pos
            distance = direction.length()
            if distance > 0:
                direction = direction.normalize()
                # Stop at 200px from target
                if distance > 200:
                    self.vel = direction * self.speed
                else:
                    self.vel = Vector2(0, 0)

        # Update position
        super().update(dt)

        # Attack timer counts down; contact damage is handled by CollisionSystem (which
        # enforces iframes), so the timer here is kept as a hook for ranged subclasses.
        self.attack_timer -= dt
        if self.attack_timer <= 0:
            self.attack_timer = self.attack_cooldown

    def take_damage(self, amount, hit_direction=None, attacker=None):
        """Override to trigger on_death after the entity is killed."""
        if self._death_handled:
            return
        if attacker is not None:
            self.last_attacker = attacker
        super().take_damage(amount)
        if hit_direction is not None and hit_direction.length() > 0:
            self.apply_knockback(-hit_direction, ENEMY_KNOCKBACK_FORCE)
        if self.hp <= 0 and self.xp_orb_group is not None:
            self._death_handled = True
            self.on_death(self.xp_orb_group)

    def apply_knockback(self, direction: Vector2, force: float):
        """Apply knockback to the enemy."""
        self.knockback_vel = direction * force

    def on_death(self, xp_orb_group):
        """Handle enemy death by spawning an XP orb and crediting the player."""
        AudioManager.instance().play_sfx(AudioManager.ENEMY_DEATH)
        credited_player = self.last_attacker or self.target
        if credited_player is not None:
            credited_player.kill_count += 1
        all_sprites = self.all_groups[0]
        XPOrb(self.pos, self.xp_value, (all_sprites, xp_orb_group))
        if self.effect_group is not None:
            from src.entities.effects import DeathExplosion
            DeathExplosion(self.pos, 40, (200, 100, 50), [self.effect_group])
