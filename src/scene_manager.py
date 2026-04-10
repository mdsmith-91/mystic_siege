import pygame
from src.ui.main_menu import MainMenu
from src.ui.class_select import ClassSelect
from src.ui.lobby_scene import LobbyScene
from src.game_scene import GameScene
from src.ui.game_over import GameOver
from src.ui.settings_menu import SettingsMenu
from src.ui.stats_menu import StatsMenu
from src.utils.audio_manager import AudioManager
from settings import (
    STATE_MENU, STATE_CLASS_SELECT, STATE_PLAYING, STATE_GAMEOVER,
    STATE_SETTINGS, STATE_STATS, STATE_LOBBY,
    MENU_MUSIC_PATH, GAME_MUSIC_PATH,
)

# Scenes recreated from scratch on every entry (never reuse stale instance)
_ALWAYS_FRESH = frozenset({STATE_PLAYING, STATE_GAMEOVER, STATE_LOBBY, STATE_CLASS_SELECT})
_MENU_MUSIC_SCENES = frozenset({
    STATE_MENU,
    STATE_LOBBY,
    STATE_CLASS_SELECT,
    STATE_GAMEOVER,
    STATE_SETTINGS,
    STATE_STATS,
})


class SceneManager:
    def __init__(self):
        self.scenes = {
            STATE_MENU: None,
            STATE_LOBBY: None,
            STATE_CLASS_SELECT: None,
            STATE_PLAYING: None,
            STATE_GAMEOVER: None,
            STATE_SETTINGS: None,
            STATE_STATS: None,
        }
        self.current_scene = None
        self._switch_to(STATE_MENU)

    def _switch_to(self, scene_name, **kwargs):
        """Internal method to switch to a scene, creating it if needed."""
        if scene_name not in self.scenes:
            raise ValueError(f"Unknown scene: {scene_name}")

        self._sync_music_for_scene(scene_name)

        # Always-fresh scenes are discarded before (re)creation
        if scene_name in _ALWAYS_FRESH:
            self.scenes[scene_name] = None

        # Create the scene if it doesn't exist
        if self.scenes[scene_name] is None:
            if scene_name == STATE_MENU:
                self.scenes[scene_name] = MainMenu()
            elif scene_name == STATE_LOBBY:
                self.scenes[scene_name] = LobbyScene()
            elif scene_name == STATE_CLASS_SELECT:
                self.scenes[scene_name] = ClassSelect(**kwargs)
            elif scene_name == STATE_PLAYING:
                self.scenes[scene_name] = GameScene(**kwargs)
            elif scene_name == STATE_GAMEOVER:
                self.scenes[scene_name] = GameOver(**kwargs)
            elif scene_name == STATE_SETTINGS:
                self.scenes[scene_name] = SettingsMenu()
            elif scene_name == STATE_STATS:
                self.scenes[scene_name] = StatsMenu()

        self.current_scene = self.scenes[scene_name]

    @staticmethod
    def _sync_music_for_scene(scene_name: str) -> None:
        audio_manager = AudioManager.instance()
        if scene_name == STATE_PLAYING:
            audio_manager.play_music(GAME_MUSIC_PATH)
        elif scene_name in _MENU_MUSIC_SCENES:
            audio_manager.play_music(MENU_MUSIC_PATH)

    def switch_to(self, scene_name, **kwargs):
        """Switch to a new scene, passing kwargs to scene constructor if needed."""
        self._switch_to(scene_name, **kwargs)

    @staticmethod
    def _discard_pending_synthetic_controller_keys() -> None:
        """Prevent controller button bleed into the next scene after a transition."""
        pending_key_events = pygame.event.get((pygame.KEYDOWN, pygame.KEYUP))
        for event in pending_key_events:
            if getattr(event, "synthetic_controller_event", False):
                continue
            pygame.event.post(event)

    def update(self, dt, events=None):
        """Update the current scene."""
        if self.current_scene is None:
            return

        # Use the events collected by the caller; fall back to polling if not provided
        if events is None:
            events = pygame.event.get()
        self.current_scene.handle_events(events)

        # Update scene
        self.current_scene.update(dt)

        # Check for scene transition
        if hasattr(self.current_scene, 'next_scene') and self.current_scene.next_scene is not None:
            previous_scene = self.current_scene
            next_scene = self.current_scene.next_scene
            next_scene_kwargs = getattr(self.current_scene, 'next_scene_kwargs', {})
            self._switch_to(next_scene, **next_scene_kwargs)
            self._discard_pending_synthetic_controller_keys()
            # Clear the transition flags on the scene that requested the switch.
            previous_scene.next_scene = None
            previous_scene.next_scene_kwargs = {}

    def draw(self, screen):
        """Draw the current scene."""
        if self.current_scene is not None:
            self.current_scene.draw(screen)
