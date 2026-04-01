import pygame
from pygame.math import Vector2
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT
from src.systems.save_system import SaveSystem
from src.entities.player import Player
from src.systems.camera import Camera
from src.systems.wave_manager import WaveManager
from src.systems.xp_system import XPSystem
from src.systems.upgrade_system import UpgradeSystem
from src.systems.collision import CollisionSystem
from src.ui.hud import HUD
from src.ui.upgrade_menu import UpgradeMenu

class GameScene:
    def __init__(self, hero: dict):
        # Create groups: all_sprites, player_group, enemy_group, projectile_group,
        #                 xp_orb_group, effect_group
        self.all_sprites = pygame.sprite.Group()
        self.player_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.projectile_group = pygame.sprite.Group()
        self.xp_orb_group = pygame.sprite.Group()
        self.effect_group = pygame.sprite.Group()

        # Instantiate in this order:
        # 1. player = Player(center_of_world, hero, (all_sprites, player_group))
        center_of_world = Vector2(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
        self.player = Player(center_of_world, hero, (self.all_sprites, self.player_group))

        # 2. Give player its starting weapon:
        #    Import the correct weapon class from hero["starting_weapon"]
        #    Instantiate it with (player, projectile_group, enemy_group)
        #    player.add_weapon(weapon)
        starting_weapon = hero["starting_weapon"]
        if starting_weapon == "ArcaneBolt":
            from src.weapons.arcane_bolt import ArcaneBolt
            weapon = ArcaneBolt(self.player, self.projectile_group, self.enemy_group)
        elif starting_weapon == "HolyNova":
            from src.weapons.holy_nova import HolyNova
            weapon = HolyNova(self.player, self.projectile_group, self.enemy_group)
        elif starting_weapon == "SpectralBlade":
            from src.weapons.spectral_blade import SpectralBlade
            weapon = SpectralBlade(self.player, self.projectile_group, self.enemy_group)
        elif starting_weapon == "FlameWhip":
            from src.weapons.flame_whip import FlameWhip
            weapon = FlameWhip(self.player, self.projectile_group, self.enemy_group)
        elif starting_weapon == "FrostRing":
            from src.weapons.frost_ring import FrostRing
            weapon = FrostRing(self.player, self.projectile_group, self.enemy_group)
        elif starting_weapon == "LightningChain":
            from src.weapons.lightning_chain import LightningChain
            weapon = LightningChain(self.player, self.projectile_group, self.enemy_group)
        else:
            # Default to ArcaneBolt if unknown
            from src.weapons.arcane_bolt import ArcaneBolt
            weapon = ArcaneBolt(self.player, self.projectile_group, self.enemy_group)

        self.player.add_weapon(weapon)

        # 3. camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        # 4. wave_manager = WaveManager(player, all_sprites, enemy_group, xp_orb_group, projectile_group)
        self.wave_manager = WaveManager(self.player, self.all_sprites, self.enemy_group, self.xp_orb_group, self.projectile_group)

        # 5. xp_system = XPSystem()
        self.xp_system = XPSystem()

        # 6. upgrade_system = UpgradeSystem()
        self.upgrade_system = UpgradeSystem(self.projectile_group, self.enemy_group)

        # 7. collision_system = CollisionSystem()
        self.collision_system = CollisionSystem()

        # 8. hud = HUD()
        self.hud = HUD()

        # 9. upgrade_menu = None  (created when leveling up)
        self.upgrade_menu = None

        # 10. paused = False
        self.paused = False

        # 11. next_scene: str = None
        self.next_scene = None

        # 12. next_scene_kwargs: dict = {}
        self.next_scene_kwargs = {}

        # 13. show_fps — read from saved settings so the settings menu toggle takes effect
        save_system = SaveSystem()
        self.show_fps = save_system.get_setting("show_fps")
        self._fps_clock = pygame.time.Clock()

        # 14. background = generate a 3000x3000 surface tiled with 32x32 dark gray/green rects
        #     (checkerboard of (30,35,25) and (25,30,20) to suggest ground tiles)
        #     Do this efficiently: draw a small tile pattern then scale — NOT 3000*3000 loops
        self.background = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))

        # Create a small tile pattern
        tile_size = 32
        tile_pattern = pygame.Surface((tile_size * 2, tile_size * 2))
        pygame.draw.rect(tile_pattern, (30, 35, 25), (0, 0, tile_size, tile_size))
        pygame.draw.rect(tile_pattern, (25, 30, 20), (tile_size, 0, tile_size, tile_size))
        pygame.draw.rect(tile_pattern, (25, 30, 20), (0, tile_size, tile_size, tile_size))
        pygame.draw.rect(tile_pattern, (30, 35, 25), (tile_size, tile_size, tile_size, tile_size))

        # Scale the pattern to fill the background
        scaled_pattern = pygame.transform.scale(tile_pattern, (WORLD_WIDTH, WORLD_HEIGHT))
        self.background.blit(scaled_pattern, (0, 0))

    def handle_events(self, events):
        """Handle user input events."""
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC: toggle paused
                    self.paused = not self.paused
                elif event.key == pygame.K_F3:
                    # F3: toggle show_fps
                    self.show_fps = not self.show_fps
            elif event.type == pygame.QUIT:
                pygame.quit()
                return

        if self.upgrade_menu and not self.upgrade_menu.done:
            self.upgrade_menu.handle_events(events)

    def update(self, dt):
        """Update the game scene."""
        # If paused or upgrade_menu is open (and not yet dismissed): return
        if self.paused or (self.upgrade_menu and not self.upgrade_menu.done):
            return

        self._fps_clock.tick()

        # all_sprites.update(dt)  — this updates player, enemies, projectiles, orbs
        self.all_sprites.update(dt)

        # wave_manager.update(dt)
        self.wave_manager.update(dt)

        # collision_system.check_all(player, enemy_group, projectile_group)
        self.collision_system.check_all(self.player, self.enemy_group, self.projectile_group)

        # xp_system.update(dt, player, xp_orb_group)
        self.xp_system.update(dt, self.player, self.xp_orb_group)

        # camera.update(player.pos, dt)
        self.camera.update(self.player.pos, dt)

        # Check levelup:
        # if xp_system.levelup_pending and upgrade_menu is None:
        if self.xp_system.levelup_pending and self.upgrade_menu is None:
            choices = self.upgrade_system.get_random_choices(self.player)
            self.upgrade_menu = UpgradeMenu(choices, self.upgrade_system, self.player)

        # Check win: if wave_manager.victory_flag: transition to game_over with victory=True
        if self.wave_manager.victory_flag:
            self.next_scene = "gameover"
            self.next_scene_kwargs = {"victory": True, "stats": {
                "time_str": self.wave_manager.get_elapsed_str(),
                "kills": self.player.kill_count,
                "level": self.xp_system.current_level,
                "weapons": [w.name for w in self.player.weapons]
            }}
            return

        # Check lose: if not player.is_alive: transition to game_over with victory=False
        if not self.player.is_alive:
            self.next_scene = "gameover"
            self.next_scene_kwargs = {"victory": False, "stats": {
                "time_str": self.wave_manager.get_elapsed_str(),
                "kills": self.player.kill_count,
                "level": self.xp_system.current_level,
                "weapons": [w.name for w in self.player.weapons]
            }}

        # Handle upgrade menu completion (apply already happened inside upgrade_menu)
        if self.upgrade_menu and self.upgrade_menu.done:
            self.upgrade_menu = None
            self.xp_system.consume_levelup()

    def draw(self, screen):
        """Draw the game scene."""
        # 1. Blit background with camera offset (only the visible portion — use subsurface or clip)
        # Get visible portion of background
        camera_offset_x = int(self.camera.offset.x)
        camera_offset_y = int(self.camera.offset.y)

        # Calculate visible rect
        visible_rect = pygame.Rect(camera_offset_x, camera_offset_y, SCREEN_WIDTH, SCREEN_HEIGHT)

        # Ensure we don't go out of bounds
        visible_rect.clamp_ip(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))

        # Blit the visible portion
        screen.blit(self.background, (0, 0), visible_rect)

        # 2. For each sprite in all_sprites (sorted by rect.bottom for depth):
        #    screen.blit(sprite.image, camera.apply(sprite))
        #    sprite.draw_health_bar(screen, camera.offset) if enemy
        # Sort sprites by y-position for proper drawing order
        sorted_sprites = sorted(self.all_sprites, key=lambda s: s.rect.bottom)

        for sprite in sorted_sprites:
            # Apply camera offset
            screen_pos = self.camera.apply(sprite)
            screen.blit(sprite.image, screen_pos)

            # Draw health bar if it's an enemy
            if hasattr(sprite, 'hp') and hasattr(sprite, 'max_hp') and sprite != self.player:
                sprite.draw_health_bar(screen, self.camera.offset)

        # 3. Draw weapon effects that need explicit draw calls (SpectralBlade, FlameWhip arc, etc.)
        # Draw SpectralBlade effects
        for weapon in self.player.weapons:
            if weapon.__class__.__name__ == "SpectralBlade":
                weapon.draw(screen, self.camera.offset)
            elif weapon.__class__.__name__ == "FlameWhip":
                weapon.draw_effect(screen, self.camera.offset)

        # 4. hud.draw(screen, player, xp_system, wave_manager, show_fps, clock_fps)
        self.hud.draw(screen, self.player, self.xp_system, self.wave_manager, self.show_fps, self._fps_clock.get_fps())

        # 5. If upgrade_menu: upgrade_menu.draw(screen)
        if self.upgrade_menu:
            self.upgrade_menu.draw(screen)

        # 6. If paused: draw "PAUSED" centered in large text with semi-transparent overlay
        if self.paused:
            # Semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            screen.blit(overlay, (0, 0))

            # "PAUSED" text
            font = pygame.font.SysFont("serif", 72)
            paused_text = font.render("PAUSED", True, (255, 255, 255))
            screen.blit(paused_text, (SCREEN_WIDTH // 2 - paused_text.get_width() // 2, SCREEN_HEIGHT // 2 - paused_text.get_height() // 2))