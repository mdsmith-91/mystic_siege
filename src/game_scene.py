import os
import pygame
from pygame.math import Vector2
from settings import (SCREEN_WIDTH, SCREEN_HEIGHT, WORLD_WIDTH, WORLD_HEIGHT,
                       STATE_MENU, STATE_LOBBY, GOLD,
                       PAUSE_BUTTON_WIDTH, PAUSE_BUTTON_HEIGHT, PAUSE_BUTTON_SPACING,
                       PAUSE_BUTTON_COLOR, PAUSE_BUTTON_HOVER_COLOR, PAUSE_BUTTON_TEXT_COLOR,
                       SPAWN_OFFSETS, STATE_GAMEOVER,
                       REVIVE_RADIUS, REVIVE_DURATION, REVIVE_HEALTH_FRACTION,
                       REVIVE_IFRAME_DURATION)
from src.core.player_slot import PlayerSlot
from src.systems.save_system import SaveSystem
from src.utils.resource_loader import ResourceLoader, _get_base_path
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
    def __init__(self, slots: list[PlayerSlot]):
        # Create groups: all_sprites, player_group, enemy_group, projectile_group,
        #                 xp_orb_group, effect_group
        self.all_sprites = pygame.sprite.Group()
        self.player_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.projectile_group = pygame.sprite.Group()
        self.xp_orb_group = pygame.sprite.Group()
        self.effect_group = pygame.sprite.Group()

        if not slots:
            raise ValueError("GameScene requires at least one PlayerSlot")

        self.slots = list(slots)

        # Instantiate players from slot metadata. Keep a legacy player alias below
        # until collision, camera, HUD, and wave systems are migrated in later phases.
        center_of_world = Vector2(WORLD_WIDTH // 2, WORLD_HEIGHT // 2)
        self.players: list[Player] = []
        for slot in self.slots:
            spawn_offset = Vector2(SPAWN_OFFSETS[slot.index])
            player = Player(
                center_of_world + spawn_offset,
                slot.hero_data,
                (self.all_sprites, self.player_group),
                slot=slot,
                supports_revive=len(self.slots) > 1,
            )
            player.add_weapon(self._create_starting_weapon(player, slot.hero_data))
            self.players.append(player)

        # 3. camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.wave_manager = WaveManager(
            self.players,
            self.all_sprites,
            self.enemy_group,
            self.xp_orb_group,
            self.projectile_group,
            self.effect_group,
        )

        # Per-player XP state is required before multiplayer collision/camera/HUD land.
        self.xp_systems = [XPSystem() for _ in self.players]

        # 6. upgrade_system = UpgradeSystem()
        self.upgrade_system = UpgradeSystem(self.projectile_group, self.enemy_group, self.effect_group)

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
        self.active_upgrade_context: tuple[Player, XPSystem] | None = None
        self.upgrade_queue: list[tuple[Player, XPSystem]] = []

        # 10. paused = False
        self.paused = False
        self.pause_selected = 0  # keyboard-nav index for pause menu (0=RESUME…3=MAIN MENU)
        self.pause_keyboard_active = False
        self._settings_open = False
        self._settings_menu = None

        # 11. next_scene: str = None
        self.next_scene = None

        # 12. next_scene_kwargs: dict = {}
        self.next_scene_kwargs = {}

        # 13. show_fps — read from saved settings so the settings menu toggle takes effect
        save_system = SaveSystem()
        self.show_fps = save_system.get_setting("show_fps")
        self._smooth_dt = 1 / 60  # exponential moving average of dt for stable FPS display

        # 14. background — use Gemini-generated image if available, else procedural tiles
        bg_path = "assets/backgrounds/game_bg.png"
        self.background = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))

        if os.path.exists(os.path.join(_get_base_path(), bg_path)):
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

    @property
    def player(self) -> Player:
        return self.players[0]

    def _create_starting_weapon(self, player: Player, hero_data: dict):
        starting_weapon = hero_data["starting_weapon"]

        if starting_weapon == "ArcaneBolt":
            from src.weapons.arcane_bolt import ArcaneBolt
            return ArcaneBolt(player, self.projectile_group, self.enemy_group, self.effect_group)
        if starting_weapon == "HolyNova":
            from src.weapons.holy_nova import HolyNova
            return HolyNova(player, self.projectile_group, self.enemy_group, self.effect_group)
        if starting_weapon == "SpectralBlade":
            from src.weapons.spectral_blade import SpectralBlade
            return SpectralBlade(player, self.projectile_group, self.enemy_group, self.effect_group)
        if starting_weapon == "FlameWhip":
            from src.weapons.flame_whip import FlameWhip
            return FlameWhip(player, self.projectile_group, self.enemy_group, self.effect_group)
        if starting_weapon == "FrostRing":
            from src.weapons.frost_ring import FrostRing
            return FrostRing(player, self.projectile_group, self.enemy_group, self.effect_group)
        if starting_weapon == "LightningChain":
            from src.weapons.lightning_chain import LightningChain
            return LightningChain(player, self.projectile_group, self.enemy_group, self.effect_group)

        from src.weapons.arcane_bolt import ArcaneBolt
        return ArcaneBolt(player, self.projectile_group, self.enemy_group, self.effect_group)

    def _queue_pending_levelups(self) -> None:
        for player, xp_system in zip(self.players, self.xp_systems):
            if not player.can_collect_xp:
                continue

            queued_count = sum(1 for _player, queued_xp in self.upgrade_queue if queued_xp is xp_system)
            if (
                self.active_upgrade_context is not None
                and self.active_upgrade_context[1] is xp_system
                and self.upgrade_menu is not None
                and not self.upgrade_menu.done
            ):
                queued_count += 1

            for _ in range(max(0, xp_system.levelup_count - queued_count)):
                self.upgrade_queue.append((player, xp_system))

    def _start_next_upgrade_menu(self) -> None:
        if self.upgrade_menu is not None or not self.upgrade_queue:
            return

        next_index = next(
            (
                index for index, (player, _xp_system) in enumerate(self.upgrade_queue)
                if player.can_collect_xp
            ),
            None,
        )
        if next_index is None:
            return

        player, xp_system = self.upgrade_queue.pop(next_index)
        choices = self.upgrade_system.get_random_choices(player)
        self.upgrade_menu = UpgradeMenu(choices, self.upgrade_system, player)
        self.active_upgrade_context = (player, xp_system)

    def _complete_upgrade_menu(self) -> None:
        if self.upgrade_menu is None or not self.upgrade_menu.done or self.active_upgrade_context is None:
            return

        from src.entities.effects import LevelUpEffect

        player, xp_system = self.active_upgrade_context
        LevelUpEffect(player.pos, [self.effect_group])
        xp_system.consume_levelup()
        self.upgrade_menu = None
        self.active_upgrade_context = None

    def _build_gameover_stats(self) -> dict:
        weapons: list[str] = []
        for player in self.players:
            if len(self.players) == 1:
                weapons.extend(weapon.name for weapon in player.weapons)
            else:
                weapons.extend(
                    f"P{player.slot.index + 1}: {weapon.name}"
                    for weapon in player.weapons
                )

        return {
            "time_str": self.wave_manager.get_elapsed_str(),
            "time_survived": self.wave_manager.elapsed,
            "kills": sum(player.kill_count for player in self.players),
            "level": max(xp_system.current_level for xp_system in self.xp_systems),
            "weapons": weapons,
        }

    def _build_player_results(self) -> list[dict]:
        player_results: list[dict] = []
        for player, xp_system, slot in zip(self.players, self.xp_systems, self.slots):
            player_results.append(
                {
                    "slot_index": slot.index,
                    "hero_name": player.hero_class,
                    "kills": player.kill_count,
                    "level": xp_system.current_level,
                    "weapons": [weapon.name for weapon in player.weapons],
                    "color": slot.color,
                }
            )
        return player_results

    def _trigger_gameover(self, victory: bool) -> None:
        self.next_scene = STATE_GAMEOVER
        stats = self._build_gameover_stats()
        player_results = self._build_player_results()
        self.next_scene_kwargs = {
            "victory": victory,
            "stats": stats,
            "player_results": player_results if len(player_results) > 1 else None,
        }

    def _revive_player(self, player: Player) -> None:
        player.hp = max(1.0, player.max_hp * REVIVE_HEALTH_FRACTION)
        player.is_downed = False
        player.revive_timer = 0.0
        player.iframes = REVIVE_IFRAME_DURATION
        player.flash_timer = 0.0
        player.knockback_vel = Vector2(0, 0)
        player.vel = Vector2(0, 0)
        player._alpha = 255

    def _update_revive(self, dt: float) -> None:
        downed_players = [player for player in self.players if player.is_downed]
        alive_players = [player for player in self.players if player.is_alive]

        if not downed_players:
            return

        revive_radius_sq = REVIVE_RADIUS * REVIVE_RADIUS
        for downed_player in downed_players:
            rescuer = next(
                (
                    player for player in alive_players
                    if (player.pos - downed_player.pos).length_squared() <= revive_radius_sq
                ),
                None,
            )

            if rescuer is None:
                downed_player.revive_timer = max(0.0, downed_player.revive_timer - dt)
                continue

            downed_player.revive_timer = min(
                REVIVE_DURATION,
                downed_player.revive_timer + dt,
            )
            if downed_player.revive_timer >= REVIVE_DURATION:
                self._revive_player(downed_player)

        if downed_players and not alive_players:
            self._trigger_gameover(victory=False)

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

    def _activate_pause_button(self, index: int):
        """Fire the action for the pause menu button at the given index."""
        if index == 0:
            self.paused = False
        elif index == 1:
            from src.ui.settings_menu import SettingsMenu
            self._settings_menu = SettingsMenu()
            self._settings_open = True
        elif index == 2:
            self.next_scene = STATE_LOBBY
        elif index == 3:
            self.next_scene = STATE_MENU

    def handle_events(self, events):
        """Handle user input events."""
        # When settings overlay is open, delegate entirely to it
        if self._settings_open:
            self._settings_menu.handle_events(events)
            if self._settings_menu.next_scene is not None:
                # Back/ESC in settings returns to pause screen
                self._settings_open = False
                self.show_fps = self._settings_menu.show_fps
                self._settings_menu.next_scene = None
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    was_paused = self.paused
                    self.paused = not self.paused
                    if not was_paused:
                        self.pause_selected = 0
                        self.pause_keyboard_active = False
                elif self.paused and event.key in (pygame.K_UP, pygame.K_w):
                    self.pause_keyboard_active = True
                    self.pause_selected = max(0, self.pause_selected - 1)
                elif self.paused and event.key in (pygame.K_DOWN, pygame.K_s):
                    self.pause_keyboard_active = True
                    self.pause_selected = min(3, self.pause_selected + 1)
                elif self.paused and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._activate_pause_button(self.pause_selected)
                elif event.key == pygame.K_F3:
                    # F3: toggle show_fps
                    self.show_fps = not self.show_fps
            elif event.type == pygame.MOUSEMOTION and self.paused:
                self.pause_keyboard_active = False
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
                    self.next_scene = STATE_LOBBY
                elif menu_rect.collidepoint(event.pos):
                    self.next_scene = STATE_MENU
            elif event.type == pygame.QUIT:
                # Do NOT call pygame.quit() here. game.py already sets running=False
                # when it sees this event, so the main loop exits cleanly after this
                # frame and main.py's finally block calls pygame.quit() exactly once.
                # Calling it here would deinitialize pygame mid-frame, causing hangs
                # on Linux and swallowing crash tracebacks on all platforms.
                return

        if self.upgrade_menu and not self.upgrade_menu.done:
            self.upgrade_menu.handle_events(events)

    def update(self, dt):
        """Update the game scene."""
        # When in-game settings overlay is open, delegate update to the settings menu
        if self._settings_open:
            self._settings_menu.update(dt)
            return

        # If paused or upgrade_menu is open (and not yet dismissed): return
        if self.paused:
            return
        if self.upgrade_menu and not self.upgrade_menu.done:
            self.upgrade_menu.update(dt)
            return

        self._smooth_dt = dt * 0.1 + self._smooth_dt * 0.9

        # all_sprites.update(dt)  — this updates player, enemies, orbs
        self.all_sprites.update(dt)

        # projectile_group is separate from all_sprites, update explicitly
        self.projectile_group.update(dt)

        # wave_manager.update(dt)
        self.wave_manager.update(dt)

        self.collision_system.check_all(
            self.players,
            self.enemy_group,
            self.projectile_group,
            self.effect_group,
        )

        # Update effect_group AFTER collision so spawned effects move in the same frame
        self.effect_group.update(dt)

        # xp_system.update(dt, player, xp_orb_group)
        for player, xp_system in zip(self.players, self.xp_systems):
            xp_system.update(dt, player, self.xp_orb_group)

        camera_targets = [player.pos for player in self.players if player.is_alive]
        self.camera.update_multi(camera_targets, dt)

        self._complete_upgrade_menu()
        self._queue_pending_levelups()
        self._start_next_upgrade_menu()
        self._update_revive(dt)

        # Check win: if wave_manager.victory_flag: transition to game_over with victory=True
        if self.wave_manager.victory_flag:
            self._trigger_gameover(victory=True)
            return

        if self.next_scene == STATE_GAMEOVER:
            return

        if all(not player.is_alive for player in self.players):
            self._trigger_gameover(victory=False)
            return

    def draw(self, screen):
        """Draw the game scene."""
        visible_rect = self.camera.get_view_rect()
        visible_rect.clamp_ip(pygame.Rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT))
        world_surface = pygame.Surface(visible_rect.size).convert()
        world_surface.blit(self.background, (0, 0), visible_rect)
        local_offset = Vector2(visible_rect.x, visible_rect.y)

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
            screen_pos = sprite.rect.move(-local_offset)
            world_surface.blit(sprite.image, screen_pos)

            # Draw health bar if it's an enemy
            if hasattr(sprite, 'hp') and hasattr(sprite, 'max_hp') and sprite not in self.player_group:
                sprite.draw_health_bar(world_surface, local_offset)

        # 3. Draw weapon effects that need explicit draw calls (SpectralBlade, HolyNova, FrostRing, etc.)
        for player in self.players:
            for weapon in player.weapons:
                if hasattr(weapon, 'draw'):
                    weapon.draw(world_surface, local_offset)
                if hasattr(weapon, 'draw_effect'):
                    weapon.draw_effect(world_surface, local_offset)

        # 4. Draw effects (damage numbers, sparks, explosions) on top of sprites
        for sprite in self.effect_group:
            screen_pos = sprite.rect.move(-local_offset)
            world_surface.blit(sprite.image, screen_pos)

        if world_surface.get_size() == (SCREEN_WIDTH, SCREEN_HEIGHT):
            screen.blit(world_surface, (0, 0))
        else:
            scaled_world = pygame.transform.smoothscale(world_surface, (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(scaled_world, (0, 0))

        # 6. hud.draw(screen, player, xp_system, wave_manager, show_fps, clock_fps)
        fps = 1.0 / self._smooth_dt if self._smooth_dt > 0 else 0
        self.hud.draw_threat_arrows(screen, self.enemy_group, self.camera, self.players)
        self.hud.draw(
            screen,
            self.players,
            self.xp_systems,
            self.wave_manager,
            self.show_fps,
            fps,
            self.camera,
        )

        # 7. If upgrade_menu: upgrade_menu.draw(screen)
        if self.upgrade_menu:
            self.upgrade_menu.draw(screen)

        # 8. If paused: draw pause overlay or settings overlay
        if self.paused:
            if self._settings_open:
                self._settings_menu.draw(screen)
            else:
                self._draw_pause_overlay(screen)

    def _draw_pause_overlay(self, screen):
        """Draw the pause menu: overlay, title, and four interactive buttons."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        title_font = pygame.font.SysFont("serif", 72)
        btn_font = pygame.font.SysFont("serif", 28)

        cx = SCREEN_WIDTH // 2
        resume_rect, settings_rect, restart_rect, menu_rect = self._pause_button_rects()

        title_surf = title_font.render("PAUSED", True, GOLD)
        title_shadow = title_font.render("PAUSED", True, (0, 0, 0))
        title_y = resume_rect.top - title_surf.get_height() - 20
        screen.blit(title_shadow, (cx - title_surf.get_width() // 2 + 3, title_y + 3))
        screen.blit(title_surf, (cx - title_surf.get_width() // 2, title_y))

        mouse_pos = pygame.mouse.get_pos()
        labels = [
            ("RESUME", resume_rect),
            ("SETTINGS", settings_rect),
            ("RESTART", restart_rect),
            ("MAIN MENU", menu_rect),
        ]

        for i, (label, rect) in enumerate(labels):
            highlighted = rect.collidepoint(mouse_pos) or (self.pause_keyboard_active and i == self.pause_selected)
            color = PAUSE_BUTTON_HOVER_COLOR if highlighted else PAUSE_BUTTON_COLOR
            pygame.draw.rect(screen, color, rect, border_radius=6)
            pygame.draw.rect(screen, GOLD, rect, width=2, border_radius=6)
            text_surf = btn_font.render(label, True, PAUSE_BUTTON_TEXT_COLOR)
            screen.blit(text_surf, (rect.centerx - text_surf.get_width() // 2,
                                    rect.centery - text_surf.get_height() // 2))
