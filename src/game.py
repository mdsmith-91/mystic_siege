import pygame
from src.scene_manager import SceneManager
from settings import STATE_MENU
from datetime import datetime, timezone

class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.scene_manager = SceneManager()
        self.scene_manager.switch_to(STATE_MENU)

    def run(self):
        running = True
        while running:
            # Collect events once per frame so nothing is dropped
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        # Toggle fullscreen
                        pygame.display.toggle_fullscreen()
                    elif event.key == pygame.K_F12:
                        # Take screenshot
                        filename = f"screenshot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.png"
                        pygame.image.save(self.screen, filename)
                        print(f"Screenshot saved: {filename}")

            # Update with dt capped at 0.05 to prevent spiral-of-death on lag spikes
            dt = self.clock.tick() / 1000.0
            if dt > 0.05:
                dt = 0.05

            # Update and draw — pass the already-collected events so the queue isn't drained twice
            self.scene_manager.update(dt, events)
            self.scene_manager.draw(self.screen)

            # Update display
            pygame.display.flip()