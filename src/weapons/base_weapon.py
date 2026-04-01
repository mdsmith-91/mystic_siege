import pygame
from abc import ABC, abstractmethod

class BaseWeapon(ABC):
    def __init__(self, owner, projectile_group, enemy_group):
        self.owner = owner
        self.level = 1
        self.cooldown_timer = 0.0
        self.projectile_group = projectile_group
        self.enemy_group = enemy_group
        self.upgrade_levels = []  # Defined by subclasses

        # Subclasses define name, description, base_damage, base_cooldown as class attributes

    def update(self, dt: float):
        """Update the weapon's cooldown timer."""
        self.cooldown_timer -= dt
        if self.cooldown_timer <= 0:
            self.fire()
            self.cooldown_timer = self._get_effective_cooldown()

    def _get_effective_cooldown(self) -> float:
        """Calculate the effective cooldown based on owner's cooldown reduction."""
        return self.base_cooldown * (1.0 - self.owner.cooldown_reduction)

    def upgrade(self):
        """Upgrade the weapon to the next level."""
        if self.level >= 5:
            return

        # Apply upgrade level attributes
        if self.level < len(self.upgrade_levels):
            upgrade = self.upgrade_levels[self.level]
            for key, value in upgrade.items():
                if hasattr(self, key):
                    setattr(self, key, getattr(self, key) + value)

        self.level += 1

    @abstractmethod
    def fire(self):
        """Fire the weapon - must be implemented by subclasses."""
        pass