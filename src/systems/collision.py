import pygame
from pygame.math import Vector2
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, ENEMY_MIN_SEPARATION

IFRAME_DURATION = 0.5  # seconds of invincibility after player takes a hit

class CollisionSystem:
    def check_all(self, players, enemy_group, projectile_group, effect_group=None):
        """Handle all collision detection."""
        self.check_player_enemy_contact(players, enemy_group, effect_group)
        self.check_projectile_enemies(projectile_group, enemy_group, effect_group)
        self.check_enemy_projectiles_player(projectile_group, players, effect_group)
        self.check_weapon_hits(players, enemy_group)
        self.check_enemy_separation(enemy_group)

    def check_player_enemy_contact(self, players, enemy_group, effect_group=None):
        """Check for player-enemy contact collisions."""
        active_players = [
            player for player in players
            if player.is_alive and player.iframes <= 0
        ]
        if not active_players:
            return

        for player in active_players:
            for enemy in enemy_group:
                if player.rect.colliderect(enemy.rect) and player.iframes <= 0:
                    actual_damage = player.take_damage(enemy.damage)
                    player.iframes = IFRAME_DURATION
                    if not getattr(player, "knockback_immune", False):
                        diff = player.pos - enemy.pos
                        knockback_dir = diff.normalize() if diff.length() > 0 else Vector2(1, 0)
                        player.knockback_vel = knockback_dir * 300
                    if effect_group is not None:
                        from src.entities.effects import DamageNumber
                        DamageNumber(player.pos - Vector2(0, 30), actual_damage,
                                     [effect_group], is_player_damage=True)

    def check_projectile_enemies(self, projectile_group, enemy_group, effect_group=None):
        """Check for player-projectile-enemy collisions (skips enemy projectiles)."""
        collisions = pygame.sprite.groupcollide(projectile_group, enemy_group, False, False)
        for projectile, enemy_list in collisions.items():
            if projectile.is_enemy_projectile:
                continue
            for enemy in enemy_list:
                projectile.on_hit(enemy, effect_group)

    def check_enemy_projectiles_player(self, projectile_group, players, effect_group=None):
        """Check for enemy-projectile-player collisions."""
        active_players = [
            player for player in players
            if player.is_alive and player.iframes <= 0
        ]
        if not active_players:
            return

        for projectile in projectile_group:
            if not projectile.is_enemy_projectile:
                continue
            for player in active_players:
                if projectile.rect.colliderect(player.rect):
                    actual_damage = player.take_damage(projectile.damage)
                    player.iframes = IFRAME_DURATION
                    if not getattr(player, "knockback_immune", False):
                        diff = player.pos - projectile.pos
                        knockback_dir = diff.normalize() if diff.length() > 0 else Vector2(1, 0)
                        player.knockback_vel = knockback_dir * 300
                    if effect_group is not None:
                        from src.entities.effects import DamageNumber
                        DamageNumber(player.pos - Vector2(0, 30), actual_damage,
                                     [effect_group], is_player_damage=True)
                    projectile.kill()
                    break

    def check_weapon_hits(self, players, enemy_group):
        """Check for weapon collisions."""
        # For orbit weapons (SpectralBlade): handled internally in weapon.update()
        # For area weapons (HolyNova, FrostRing): handled internally in weapon.update()
        # This method is a hook for any weapon that needs external collision checking
        pass  # Implementation handled in individual weapon classes

    def check_enemy_separation(self, enemy_group):
        """Push overlapping enemies apart so they don't stack on each other."""
        enemies = enemy_group.sprites()
        min_separation_sq = ENEMY_MIN_SEPARATION * ENEMY_MIN_SEPARATION
        for i, e1 in enumerate(enemies):
            for e2 in enemies[i + 1:]:
                diff = e1.pos - e2.pos
                dist_sq = diff.length_squared()
                if 0 < dist_sq < min_separation_sq:
                    dist = dist_sq ** 0.5
                    push_scale = ((ENEMY_MIN_SEPARATION - dist) * 0.5) / dist
                    push = diff * push_scale
                    e1.pos += push
                    e2.pos -= push
                    e1.rect.center = (int(e1.pos.x), int(e1.pos.y))
                    e2.rect.center = (int(e2.pos.x), int(e2.pos.y))
