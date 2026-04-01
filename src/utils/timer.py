import pygame

class Timer:
    def __init__(self, duration: float, repeat: bool = False):
        self.duration = duration
        self.repeat = repeat
        self.reset()

    def update(self, dt: float) -> bool:
        """Update the timer and return True the frame the timer fires."""
        if self.is_finished:
            return False

        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = 0.0
            if not self.repeat:
                self.is_finished = True
            return True
        return False

    def reset(self):
        """Reset the timer."""
        self.elapsed = 0.0
        self.is_finished = False

    def pause(self):
        """Pause the timer."""
        pass  # Timer is updated based on dt, so we don't need to store a paused state

    def resume(self):
        """Resume the timer."""
        pass  # Timer is updated based on dt, so we don't need to store a paused state

    @property
    def elapsed(self) -> float:
        """Seconds since last reset."""
        return self._elapsed

    @elapsed.setter
    def elapsed(self, value: float):
        self._elapsed = value