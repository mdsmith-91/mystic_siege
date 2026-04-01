import pygame
from pygame.math import Vector2
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

IFRAME_DURATION = 0.5  # seconds of invincibility after player takes a hit

class CollisionSystem:
    def check_all(self, player, enemy_group, projectile_group):
        """Handle all collision detection."""
        # Call all three check methods below
        self.check_player_enemy_contact(player, enemy_group)
        self.check_projectile_enemies(projectile_group, enemy_group)
        self.check_weapon_hits(player, enemy_group)

    def check_player_enemy_contact(self, player, enemy_group):
        """Check for player-enemy contact collisions."""
        # For each enemy in enemy_group:
        for enemy in enemy_group:
            # if player.rect.colliderect(enemy.rect) and player.iframes <= 0:
            if player.rect.colliderect(enemy.rect) and player.iframes <= 0:
                player.take_damage(enemy.damage)
                player.iframes = IFRAME_DURATION
                if player.hero_class != "Knight of the Burning Crown":
                    diff = player.pos - enemy.pos
                    knockback_dir = diff.normalize() if diff.length() > 0 else Vector2(1, 0)
                    player.knockback_vel = knockback_dir * 300

    def check_projectile_enemies(self, projectile_group, enemy_group):
        """Check for projectile-enemy collisions."""
        # Use pygame.sprite.groupcollide(projectile_group, enemy_group, False, False)
        collisions = pygame.sprite.groupcollide(projectile_group, enemy_group, False, False)

        # For each (projectile, enemy_list) in result:
        for projectile, enemy_list in collisions.items():
            # for enemy in enemy_list: projectile.on_hit(enemy)
            for enemy in enemy_list:
                projectile.on_hit(enemy)

    def check_weapon_hits(self, player, enemy_group):
        """Check for weapon collisions."""
        # For orbit weapons (SpectralBlade): handled internally in weapon.update()
        # For area weapons (HolyNova, FrostRing): handled internally in weapon.update()
        # This method is a hook for any weapon that needs external collision checking
        pass  # Implementation handled in individual weapon classes