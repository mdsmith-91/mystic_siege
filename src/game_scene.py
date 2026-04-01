import os
import pygame
from pygame.math import Vector2
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT,
                       STATE_MENU, STATE_CLASS_SELECT,
                       PAUSE_BUTTON_WIDTH, PAUSE_BUTTON_HEIGHT, PAUSE_BUTTON_SPACING,
                       PAUSE_BUTTON_COLOR, PAUSE_BUTTON_HOVER_COLOR, PAUSE_BUTTON_TEXT_COLOR)
from src.systems.save_system import SaveSystem
from src.utils.resource_loader import ResourceLoader
from src.entities.player import Player
from src.systems.camera import Camera
from src.systems.wave_manager import WaveManager
from src.systems.xp_system import XPSystem
from src.systems.upgrade_system import UpgradeSystem
from src.systems.collision import CollisionSystem
from src.ui.hud import HUD
from src.ui.upgrade_menu import UpgradeMenu
from src.utils.audio_manager import AudioManager

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

        # Load all SFX into AudioManager cache
        _am = AudioManager.instance()
        _am.load_sfx(AudioManager.PLAYER_HIT,    "assets/audio/sfx/player_hit.wav")
        _am.load_sfx(AudioManager.PLAYER_DEATH,  "assets/audio/sfx/player_death.wav")
        _am.load_sfx(AudioManager.ENEMY_DEATH,   "assets/audio/sfx/enemy_death.wav")
        _am.load_sfx(AudioManager.XP_PICKUP,     "assets/audio/sfx/xp_pickup.wav")
        _am.load_sfx(AudioManager.LEVEL_UP,      "assets/audio/sfx/level_up.wav")
        _am.load_sfx(AudioManager.WEAPON_ARCANE, "assets/audio/sfx/arcane_bolt.wav")
        _am.load_sfx(AudioManager.WEAPON_NOVA,   "assets/audio/sfx/holy_nova.wav")
        _am.load_sfx(AudioManager.WEAPON_WHIP,   "assets/audio/sfx/flame_whip.wav")
        _am.load_sfx(AudioManager.WEAPON_BLADE,  "assets/audio/sfx/spectral_blade.wav")
        _am.load_sfx(AudioManager.WEAPON_CHAIN,  "assets/audio/sfx/lightning_chain.wav")
        _am.load_sfx(AudioManager.WEAPON_FROST,  "assets/audio/sfx/frost_ring.wav")

        # 7. collision_system = CollisionSystem()
        self.collision_system = CollisionSystem()

        # 8. hud = HUD()
        self.hud = HUD()

        # 9. upgrade_menu = None  (created when leveling up)
        self.upgrade_menu = None

        # 10. paused = False
        self.paused = False
        self._settings_open = False
        self._settings_menu = None

        # 11. next_scene: str = None
        self.next_scene = None

        # 12. next_scene_kwargs: dict = {}
        self.next_scene_kwargs = {}

        # 13. show_fps — read from saved settings so the settings menu toggle takes effect
        save_system = SaveSystem()
        self.show_fps = save_system.get_setting("show_fps")
        self._fps_clock = pygame.time.Clock()

        # 14. background — use Gemini-generated image if available, else procedural tiles
        bg_path = "assets/backgrounds/game_bg.png"
        self.background = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))

        if os.path.exists(bg_path):
            # Tile the generated image across the world surface
            tile = ResourceLoader.instance().load_image(bg_path)
            tile_w, tile_h = tile.get_size()
            for y in range(0, WORLD_HEIGHT, tile_h):
                for x in range(0, WORLD_WIDTH, tile_w):
                    self.background.blit(tile, (x, y))
        else:
            # Procedural checkerboard fallback
            tile_size = 32
            tile_pattern = pygame.Surface((tile_size * 2, tile_size * 2))
            pygame.draw.rect(tile_pattern, (30, 35, 25), (0, 0, tile_size, tile_size))
            pygame.draw.rect(tile_pattern, (25, 30, 20), (tile_size, 0, tile_size, tile_size))
            pygame.draw.rect(tile_pattern, (25, 30, 20), (0, tile_size, tile_size, tile_size))
            pygame.draw.rect(tile_pattern, (30, 35, 25), (tile_size, tile_size, tile_size, tile_size))
            scaled_pattern = pygame.transform.scale(tile_pattern, (WORLD_WIDTH, WORLD_HEIGHT))
            self.background.blit(scaled_pattern, (0, 0))

    def _pause_button_rects(self):
        """Return (resume_rect, settings_rect, restart_rect, menu_rect) for the pause menu buttons."""
        cx = SCREEN_WIDTH // 2
        # Shift up to vertically center 4 buttons on screen
        top = SCREEN_HEIGHT // 2 - 100
        step = PAUSE_BUTTON_HEIGHT + PAUSE_BUTTON_SPACING
        make = lambda row: pygame.Rect(
            cx - PAUSE_BUTTON_WIDTH // 2,
            top + row * step,
            PAUSE_BUTTON_WIDTH,
            PAUSE_BUTTON_HEIGHT,
        )
        return make(0), make(1), make(2), make(3)

    def handle_events(self, events):
        """Handle user input events."""
        # When settings overlay is open, delegate entirely to it
        if self._settings_open:
            self._settings_menu.handle_events(events)
            if self._settings_menu.next_scene is not None:
                # Back/ESC in settings returns to pause screen
                self._settings_open = False
                self._settings_menu.next_scene = None
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # ESC: toggle paused (also acts as resume when paused)
                    self.paused = not self.paused
                elif event.key == pygame.K_r and self.paused:
                    # R: resume from pause
                    self.paused = False
                elif event.key == pygame.K_m and self.paused:
                    # M: return to main menu from pause
                    self.next_scene = STATE_MENU
                elif event.key == pygame.K_F3:
                    # F3: toggle show_fps
                    self.show_fps = not self.show_fps
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.paused:
                # Click on pause menu buttons
                resume_rect, settings_rect, restart_rect, menu_rect = self._pause_button_rects()
                if resume_rect.collidepoint(event.pos):
                    self.paused = False
                elif settings_rect.collidepoint(event.pos):
                    from src.ui.settings_menu import SettingsMenu
                    self._settings_menu = SettingsMenu()
                    self._settings_open = True
                elif restart_rect.collidepoint(event.pos):
                    self.next_scene = STATE_CLASS_SELECT
                elif menu_rect.collidepoint(event.pos):
                    self.next_scene = STATE_MENU
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

        # all_sprites.update(dt)  — this updates player, enemies, orbs
        self.all_sprites.update(dt)

        # projectile_group is separate from all_sprites, update it explicitly
        self.projectile_group.update(dt)

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
                "time_survived": self.wave_manager.elapsed,
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
                "time_survived": self.wave_manager.elapsed,
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

        # 2. For each sprite in all_sprites + projectile_group (sorted by rect.bottom for depth):
        #    screen.blit(sprite.image, camera.apply(sprite))
        #    sprite.draw_health_bar(screen, camera.offset) if enemy
        # Sort sprites by y-position for proper drawing order (projectiles are not in all_sprites)
        sorted_sprites = sorted(
            list(self.all_sprites) + list(self.projectile_group),
            key=lambda s: s.rect.bottom,
        )

        for sprite in sorted_sprites:
            # Apply camera offset
            screen_pos = self.camera.apply(sprite)
            screen.blit(sprite.image, screen_pos)

            # Draw health bar if it's an enemy
            if hasattr(sprite, 'hp') and hasattr(sprite, 'max_hp') and sprite != self.player:
                sprite.draw_health_bar(screen, self.camera.offset)

        # 3. Draw weapon effects that need explicit draw calls (SpectralBlade, HolyNova, FrostRing, etc.)
        for weapon in self.player.weapons:
            if hasattr(weapon, 'draw'):
                weapon.draw(screen, self.camera.offset)
            if hasattr(weapon, 'draw_effect'):
                weapon.draw_effect(screen, self.camera.offset)

        # 4. hud.draw(screen, player, xp_system, wave_manager, show_fps, clock_fps)
        self.hud.draw(screen, self.player, self.xp_system, self.wave_manager, self.show_fps, self._fps_clock.get_fps())

        # 5. If upgrade_menu: upgrade_menu.draw(screen)
        if self.upgrade_menu:
            self.upgrade_menu.draw(screen)

        # 6. If paused: draw pause overlay or settings overlay
        if self.paused:
            if self._settings_open:
                self._settings_menu.draw(screen)
            else:
                self._draw_pause_overlay(screen)

    def _draw_pause_overlay(self, screen):
        """Draw the pause menu: overlay, title, and four interactive buttons."""
        # Semi-transparent darkening overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        title_font = pygame.font.SysFont("serif", 72)
        btn_font = pygame.font.SysFont("serif", 28)
        hint_font = pygame.font.SysFont("serif", 18)

        # "PAUSED" title above the buttons
        title_surf = title_font.render("PAUSED", True, (255, 255, 255))
        cx = SCREEN_WIDTH // 2
        resume_rect, settings_rect, restart_rect, menu_rect = self._pause_button_rects()
        title_y = resume_rect.top - title_surf.get_height() - 20
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, title_y))

        mouse_pos = pygame.mouse.get_pos()
        labels = [
            ("RESUME", resume_rect),
            ("SETTINGS", settings_rect),
            ("RESTART", restart_rect),
            ("MAIN MENU", menu_rect),
        ]

        for label, rect in labels:
            color = PAUSE_BUTTON_HOVER_COLOR if rect.collidepoint(mouse_pos) else PAUSE_BUTTON_COLOR
            pygame.draw.rect(screen, color, rect, border_radius=6)
            pygame.draw.rect(screen, (120, 90, 180), rect, width=2, border_radius=6)
            text_surf = btn_font.render(label, True, PAUSE_BUTTON_TEXT_COLOR)
            screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2,
                                    rect.centery - text_surf.get_height() // 2))

        # Keyboard hint below the buttons
        hint_surf = hint_font.render("ESC or R to resume  •  M for main menu", True, (180, 180, 180))
        screen.blit(hint_surf, (cx - hint_surf.get_width() // 2, menu_rect.bottom + 16))