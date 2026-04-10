import pygame
from pygame.math import Vector2
import random
import math

_damage_numbers_enabled: bool = True


def set_damage_numbers_enabled(enabled: bool) -> None:
    global _damage_numbers_enabled
    _damage_numbers_enabled = enabled


class DamageNumber(pygame.sprite.Sprite):
    def __init__(self, pos, amount: float, groups, is_player_damage=False, is_crit=False):
        if not _damage_numbers_enabled:
            return
        super().__init__(groups)

        # Display nearest-integer damage instead of truncating fractional hits.
        self.text = str(int(amount + 0.5))

        # Color: red for player damage, gold for crits, white for regular hits
        if is_player_damage:
            self.color = (255, 80, 80)
        elif is_crit:
            self.color = (255, 220, 60)
        else:
            self.color = (255, 255, 255)

        # Font size: 18 + min(int(amount/10), 14); crits are 1.25x larger and bold
        font_size = 18 + min(int(amount / 10), 14)
        if is_crit:
            font_size = int(font_size * 1.25)
        self.font = pygame.font.SysFont(None, font_size, bold=is_crit)

        # Text surface
        self.image = self.font.render(self.text, True, self.color)
        self.rect = self.image.get_rect(center=pos)

        # Velocity: Vector2(random -20 to 20, -80)
        self.vel = Vector2(random.uniform(-20, 20), -80)

        # lifetime = 0.8
        self.lifetime = 0.8

        # Store original position for updating
        self.pos = Vector2(pos)

    def update(self, dt):
        # pos += vel*dt
        self.pos += self.vel * dt

        # vel.y += 40*dt (gravity)
        self.vel.y += 40 * dt

        # lifetime -= dt
        self.lifetime -= dt

        # Update position
        self.rect.center = self.pos

        # Alpha fades out in last 0.3s
        if self.lifetime < 0.3:
            alpha = int(255 * (self.lifetime / 0.3))
            self.image.set_alpha(alpha)

        # kill() when done
        if self.lifetime <= 0:
            self.kill()

class HitSpark(pygame.sprite.Sprite):
    def __init__(self, pos, color: tuple, groups):
        super().__init__(groups)

        # 6 particles: list of dicts {pos, vel (random outward), radius, lifetime}
        self.particles = []
        for _ in range(6):
            angle = random.uniform(0, 2 * 3.14159)
            distance = random.uniform(5, 15)
            vel = Vector2(distance * 5, 0)
            vel.rotate_ip(angle)

            self.particles.append({
                "pos": Vector2(pos),
                "vel": vel,
                "radius": random.uniform(2, 5),
                "lifetime": 0.25,
                "color": color
            })

        # image: transparent surface sized to contain particles at full travel distance
        self.image = pygame.Surface((200, 200), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)

        # Store original position
        self.pos = Vector2(pos)
        self.lifetime = 0.25

    def update(self, dt):
        # Move particles, shrink radius, fade
        for particle in self.particles:
            # Move particle
            particle["pos"] += particle["vel"] * dt

            # Shrink radius
            particle["radius"] = max(0, particle["radius"] - 0.5 * dt)

            # Fade (decrease lifetime)
            particle["lifetime"] -= dt

        self.lifetime -= dt
        self.rect.center = self.pos

        # Remove dead particles and update image
        self.particles = [p for p in self.particles if p["lifetime"] > 0]
        if self.lifetime <= 0 or not self.particles:
            self.kill()
            return

        # Redraw image
        self.image.fill((0, 0, 0, 0))  # Clear surface
        for particle in self.particles:
            alpha = int(255 * (particle["lifetime"] / 0.25))
            pygame.draw.circle(self.image, (*particle["color"], alpha),
                             (particle["pos"].x - self.rect.x,
                              particle["pos"].y - self.rect.y),
                             particle["radius"])

class DeathExplosion(pygame.sprite.Sprite):
    def __init__(self, pos, radius: int, color: tuple, groups):
        super().__init__(groups)

        # Expanding circle, starts at radius/4, expands to radius over 0.4s
        self.radius = radius / 4
        self.target_radius = radius
        self.expansion_speed = (radius - radius / 4) / 0.4  # pixels per second

        # Alpha fades from 200 to 0
        self.alpha = 200

        # lifetime = 0.4s
        self.lifetime = 0.4
        self.color = color

        # image: transparent surface
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)

        # Store original position
        self.pos = Vector2(pos)

    def update(self, dt):
        # Expand, fade, kill when done
        # Expand
        self.radius += self.expansion_speed * dt

        # Fade
        self.lifetime -= dt
        self.alpha = max(0, 200 - (200 * (0.4 - self.lifetime) / 0.4))

        # Update image
        self.image.fill((0, 0, 0, 0))  # Clear surface
        pygame.draw.circle(self.image, (*self.color, self.alpha),
                         (self.rect.width // 2, self.rect.height // 2),
                         int(self.radius))

        # Kill when done
        if self.lifetime <= 0:
            self.kill()

class LevelUpEffect(pygame.sprite.Sprite):
    def __init__(self, pos, groups):
        super().__init__(groups)

        # Ring of 12 gold particles orbiting outward
        self.particles = []
        for i in range(12):
            angle = i * (2 * 3.14159 / 12)
            distance = 0
            self.particles.append({
                "pos": Vector2(pos),
                "angle": angle,
                "distance": distance,
                "speed": 100,  # pixels per second
                "lifetime": 1.5,
                "radius": 3
            })

        # lifetime = 1.5s
        self.lifetime = 1.5

        # image: transparent surface
        self.image = pygame.Surface((200, 200), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)

        # Store original position
        self.pos = Vector2(pos)

    def update(self, dt):
        # Move particles outward, then fade
        self.lifetime -= dt
        for particle in self.particles:
            # Move outward
            particle["distance"] += particle["speed"] * dt

            # Update position
            particle["pos"].x = self.pos.x + particle["distance"] * math.cos(particle["angle"])
            particle["pos"].y = self.pos.y + particle["distance"] * math.sin(particle["angle"])

            # Fade (decrease lifetime)
            particle["lifetime"] -= dt

            # Update radius (fade out)
            particle["radius"] = max(0, 3 - (3 * (1.5 - particle["lifetime"]) / 1.5))

        # Remove dead particles
        self.particles = [p for p in self.particles if p["lifetime"] > 0]
        if self.lifetime <= 0 or not self.particles:
            self.kill()
            return

        # Update image
        self.image.fill((0, 0, 0, 0))  # Clear surface
        for particle in self.particles:
            alpha = int(255 * (particle["lifetime"] / 1.5))
            pygame.draw.circle(self.image, (212, 175, 55, alpha),
                             (particle["pos"].x - self.rect.x,
                              particle["pos"].y - self.rect.y),
                             particle["radius"])


class PickupText(pygame.sprite.Sprite):
    def __init__(self, pos, text: str, color: tuple[int, int, int], groups, lifetime: float = 0.8):
        super().__init__(groups)
        self.font = pygame.font.SysFont(None, 20, bold=True)
        self.image = self.font.render(text, True, color)
        self.rect = self.image.get_rect(center=pos)
        self.pos = Vector2(pos)
        self.vel = Vector2(random.uniform(-12, 12), -55)
        self.lifetime = lifetime
        self._initial_lifetime = max(0.001, lifetime)

    def update(self, dt):
        self.lifetime -= dt
        self.pos += self.vel * dt
        self.rect.center = self.pos
        if self.lifetime <= 0:
            self.kill()
            return

        alpha = int(255 * (self.lifetime / self._initial_lifetime))
        self.image.set_alpha(max(0, min(255, alpha)))


class ExpandingRingEffect(pygame.sprite.Sprite):
    def __init__(
        self,
        pos,
        radius: float,
        color: tuple[int, int, int],
        groups,
        lifetime: float,
        ring_width: int,
        start_radius: float = 0.0,
        alpha: int = 160,
    ):
        super().__init__(groups)
        diameter = max(2, int(radius * 2) + ring_width * 4)
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.pos = Vector2(pos)
        self.start_radius = max(0.0, start_radius)
        self.target_radius = max(self.start_radius, radius)
        self.color = color
        self.ring_width = max(1, ring_width)
        self.lifetime = lifetime
        self._initial_lifetime = max(0.001, lifetime)
        self.alpha = max(0, min(255, alpha))

    def update(self, dt):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.kill()
            return

        progress = 1.0 - (self.lifetime / self._initial_lifetime)
        radius = self.start_radius + ((self.target_radius - self.start_radius) * progress)
        current_alpha = int(self.alpha * (self.lifetime / self._initial_lifetime))
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(
            self.image,
            (*self.color, max(0, min(255, current_alpha))),
            (self.rect.width // 2, self.rect.height // 2),
            max(1, int(radius)),
            self.ring_width,
        )
        self.rect.center = self.pos
