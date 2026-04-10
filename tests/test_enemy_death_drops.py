#!/usr/bin/env python3
"""Validate enemy death rewards that should remain stable across refactors."""

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from pygame.math import Vector2

from settings import HERO_CLASSES, SKELETON_ENEMY_DATA
from src.entities.enemies.skeleton import Skeleton
from src.entities.player import Player


def test_skeleton_death_drops_xp_orb_and_awards_credit() -> None:
    pygame.init()
    try:
        all_sprites = pygame.sprite.Group()
        enemy_group = pygame.sprite.Group()
        xp_orb_group = pygame.sprite.Group()

        player = Player(Vector2(100, 100), HERO_CLASSES[0], ())
        skeleton = Skeleton(
            Vector2(200, 200),
            [player],
            (all_sprites, enemy_group),
            xp_orb_group=xp_orb_group,
        )

        assert len(xp_orb_group) == 0
        assert player.kill_count == 0

        skeleton.take_damage(SKELETON_ENEMY_DATA["hp"], attacker=player)

        assert skeleton.hp == 0
        assert not skeleton.is_alive
        assert player.kill_count == 1
        assert len(xp_orb_group) == 1

        xp_orb = next(iter(xp_orb_group))
        assert xp_orb.value == SKELETON_ENEMY_DATA["xp_value"]
        assert xp_orb.pos == Vector2(200, 200)
    finally:
        pygame.quit()


def main() -> None:
    test_skeleton_death_drops_xp_orb_and_awards_credit()
    print("Enemy death drop checks passed.")


if __name__ == "__main__":
    main()
