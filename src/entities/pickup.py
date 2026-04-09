import math

import pygame
from pygame.math import Vector2

from settings import (
    HEALTH_POTION_HEAL_FLAT,
    HEALTH_POTION_HEAL_FRACTION,
    PICKUP_BATTLE_RAGE,
    PICKUP_BOB_HEIGHT,
    PICKUP_BOB_SPEED,
    PICKUP_DISPLAY_NAMES,
    PICKUP_DRAW_SIZE,
    PICKUP_GLOW_COLORS,
    PICKUP_HASTE,
    PICKUP_HEALTH_POTION,
    PICKUP_ICON_COLORS,
    PICKUP_IRON_SKIN,
    PICKUP_MAGNET,
    PICKUP_OUTLINE_WIDTH,
    PICKUP_PULSE_SPEED,
    PICKUP_TEXT_LIFETIME,
    WORLD_PICKUP_RADIUS,
)
from src.entities.effects import PickupText
from src.utils.audio_manager import AudioManager
from src.utils.resource_loader import ResourceLoader


class Pickup(pygame.sprite.Sprite):
    def __init__(self, pos, pickup_id: str, groups, effect_group=None):
        super().__init__(groups)
        self.pickup_id = pickup_id
        self.effect_group = effect_group
        self.pos = Vector2(pos)
        self.float_offset = 0.0
        self.pulse_offset = 0.0
        self.collect_radius = WORLD_PICKUP_RADIUS

        self.base_image = self._load_icon()
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=pos)

    @property
    def display_name(self) -> str:
        return PICKUP_DISPLAY_NAMES.get(self.pickup_id, self.pickup_id)

    def _asset_key(self) -> str:
        asset_names = {
            PICKUP_MAGNET: "magnet",
            PICKUP_HEALTH_POTION: "health_potion",
            PICKUP_BATTLE_RAGE: "battle_rage",
            PICKUP_IRON_SKIN: "iron_skin",
            PICKUP_HASTE: "haste",
        }
        return asset_names.get(self.pickup_id, "pickup")

    def _load_icon(self) -> pygame.Surface:
        icon = ResourceLoader.instance().load_image(
            f"assets/sprites/ui/{self._asset_key()}.png",
            scale=(PICKUP_DRAW_SIZE, PICKUP_DRAW_SIZE),
        )
        if icon.get_size() != (PICKUP_DRAW_SIZE, PICKUP_DRAW_SIZE):
            icon = pygame.transform.scale(icon, (PICKUP_DRAW_SIZE, PICKUP_DRAW_SIZE))

        return icon if not self._is_magenta_placeholder(icon) else self._build_fallback_icon()

    @staticmethod
    def _is_magenta_placeholder(surface: pygame.Surface) -> bool:
        width, height = surface.get_size()
        for x in (0, width // 2, width - 1):
            for y in (0, height // 2, height - 1):
                if surface.get_at((x, y))[:3] != (255, 0, 255):
                    return False
        return True

    def _build_fallback_icon(self) -> pygame.Surface:
        surface = pygame.Surface((PICKUP_DRAW_SIZE, PICKUP_DRAW_SIZE), pygame.SRCALPHA)
        base_color = PICKUP_ICON_COLORS[self.pickup_id]
        glow_color = PICKUP_GLOW_COLORS[self.pickup_id]
        center = PICKUP_DRAW_SIZE // 2
        radius = center - 2
        pygame.draw.circle(surface, (*glow_color, 80), (center, center), radius + 1)
        pygame.draw.circle(surface, base_color, (center, center), radius)
        pygame.draw.circle(surface, (25, 25, 35), (center, center), radius, PICKUP_OUTLINE_WIDTH)

        if self.pickup_id == PICKUP_MAGNET:
            pygame.draw.arc(surface, (255, 255, 255), (5, 5, 14, 14), math.pi * 0.05, math.pi * 0.95, 3)
            pygame.draw.line(surface, (255, 255, 255), (7, 14), (7, 20), 3)
            pygame.draw.line(surface, (255, 255, 255), (17, 14), (17, 20), 3)
        elif self.pickup_id == PICKUP_HEALTH_POTION:
            pygame.draw.rect(surface, (255, 255, 255), (9, 8, 6, 10), border_radius=2)
            pygame.draw.rect(surface, (210, 230, 255), (10, 5, 4, 4), border_radius=1)
        elif self.pickup_id == PICKUP_BATTLE_RAGE:
            pygame.draw.polygon(surface, (255, 255, 255), [(12, 5), (18, 12), (14, 12), (18, 19), (9, 11), (13, 11)])
        elif self.pickup_id == PICKUP_IRON_SKIN:
            pygame.draw.polygon(surface, (255, 255, 255), [(12, 5), (18, 7), (18, 14), (12, 19), (6, 14), (6, 7)])
        elif self.pickup_id == PICKUP_HASTE:
            pygame.draw.polygon(surface, (255, 255, 255), [(8, 14), (14, 8), (14, 12), (18, 12), (10, 20), (10, 16), (6, 16)])
        return surface

    def update(self, dt: float) -> None:
        self.float_offset += PICKUP_BOB_SPEED * dt
        self.pulse_offset += PICKUP_PULSE_SPEED * dt
        alpha_scale = 0.78 + (0.22 * ((math.sin(self.pulse_offset) + 1.0) * 0.5))
        self.image = self.base_image.copy()
        self.image.set_alpha(int(255 * alpha_scale))
        bob_y = math.sin(self.float_offset) * PICKUP_BOB_HEIGHT
        self.rect.center = (int(self.pos.x), int(self.pos.y + bob_y))

    def collect(self, player, game_scene) -> None:
        self._apply_effect(player, game_scene)
        AudioManager.instance().play_sfx(AudioManager.PICKUP_COLLECT)
        if self.effect_group is not None:
            PickupText(
                player.pos - Vector2(0, 36),
                self.display_name,
                PICKUP_GLOW_COLORS[self.pickup_id],
                [self.effect_group],
                lifetime=PICKUP_TEXT_LIFETIME,
            )
        self.kill()

    def _apply_effect(self, player, game_scene) -> None:
        if self.pickup_id == PICKUP_MAGNET:
            game_scene.apply_magnet(player)
            return

        if self.pickup_id == PICKUP_HEALTH_POTION:
            heal_amount = HEALTH_POTION_HEAL_FLAT
            if HEALTH_POTION_HEAL_FRACTION > 0:
                heal_amount += player.max_hp * HEALTH_POTION_HEAL_FRACTION
            player.heal(heal_amount)
            return

        if self.pickup_id in (PICKUP_BATTLE_RAGE, PICKUP_IRON_SKIN, PICKUP_HASTE):
            player.apply_timed_buff(self.pickup_id)
