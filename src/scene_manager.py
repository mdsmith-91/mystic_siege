import pygame
from src.ui.main_menu import MainMenu
from src.ui.class_select import ClassSelect
from src.game_scene import GameScene
from src.ui.game_over import GameOver
from settings import STATE_MENU, STATE_CLASS_SELECT, STATE_PLAYING, STATE_GAMEOVER

class SceneManager:
    def __init__(self):
        self.scenes = {
            STATE_MENU: None,
            STATE_CLASS_SELECT: None,
            STATE_PLAYING: None,
            STATE_GAMEOVER: None
        }
        self.current_scene = None
        self._switch_to(STATE_MENU)

    def _switch_to(self, scene_name, **kwargs):
        """Internal method to switch to a scene, creating it if needed."""
        if scene_name not in self.scenes:
            raise ValueError(f"Unknown scene: {scene_name}")

        # Create the scene if it doesn't exist
        if self.scenes[scene_name] is None:
            if scene_name == STATE_MENU:
                self.scenes[scene_name] = MainMenu()
            elif scene_name == STATE_CLASS_SELECT:
                self.scenes[scene_name] = ClassSelect()
            elif scene_name == STATE_PLAYING:
                # GameScene is created fresh each time to get fresh state
                self.scenes[scene_name] = GameScene(**kwargs)
            elif scene_name == STATE_GAMEOVER:
                self.scenes[scene_name] = GameOver(**kwargs)

        self.current_scene = self.scenes[scene_name]

    def switch_to(self, scene_name, **kwargs):
        """Switch to a new scene, passing kwargs to scene constructor if needed."""
        self._switch_to(scene_name, **kwargs)

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
            next_scene = self.current_scene.next_scene
            next_scene_kwargs = getattr(self.current_scene, 'next_scene_kwargs', {})
            self._switch_to(next_scene, **next_scene_kwargs)
            # Clear the transition flags after switching
            self.current_scene.next_scene = None
            self.current_scene.next_scene_kwargs = {}

    def draw(self, screen):
        """Draw the current scene."""
        if self.current_scene is not None:
            self.current_scene.draw(screen)