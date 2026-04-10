#!/usr/bin/env python3
"""Validate elite-mode health and damage scaling for every enemy type."""

import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pygame
from pygame.math import Vector2

from settings import (
    ENEMY_DATA_BY_ID,
    ENEMY_ELITE_DAMAGE_MULTIPLIER,
    ENEMY_ELITE_HP_MULTIPLIER,
    HERO_CLASSES,
    MINI_BAT_ENEMY_DATA,
)
from src.entities.enemies.plague_bat import MiniBat
from src.entities.player import Player
from src.systems.wave_manager import WaveManager


SPECIAL_DAMAGE_FIELDS = ("projectile_damage", "shockwave_damage")
BASE_DAMAGE_FIELD = "damage"


def _scaled_stat(value: float, multiplier: float) -> int:
    return max(1, int(value * multiplier))


def _custom_damage_fields(base_data: dict) -> set[str]:
    return {
        field
        for field in base_data
        if field != BASE_DAMAGE_FIELD and (field.endswith("_damage") or field.endswith("damage"))
    }


def _assert_known_damage_fields(base_data: dict) -> None:
    custom_fields = _custom_damage_fields(base_data)
    unknown_fields = custom_fields - set(SPECIAL_DAMAGE_FIELDS)
    assert not unknown_fields, (
        f"{base_data['name']} defines unvalidated elite damage field(s): "
        f"{', '.join(sorted(unknown_fields))}. Reuse '{BASE_DAMAGE_FIELD}' or add each "
        "field to SPECIAL_DAMAGE_FIELDS and Enemy.apply_elite_scaling()."
    )


def _make_player() -> Player:
    return Player(Vector2(100, 100), HERO_CLASSES[0], ())


def _make_wave_manager(players: list[Player]) -> WaveManager:
    return WaveManager(
        players=players,
        all_sprites=pygame.sprite.Group(),
        enemy_group=pygame.sprite.Group(),
        xp_orb_group=pygame.sprite.Group(),
        projectile_group=pygame.sprite.Group(),
        effect_group=pygame.sprite.Group(),
        pickup_group=pygame.sprite.Group(),
    )


def _assert_enemy_scaled(enemy, base_data: dict) -> None:
    _assert_known_damage_fields(base_data)

    expected_hp = _scaled_stat(base_data["hp"], ENEMY_ELITE_HP_MULTIPLIER)
    expected_damage = _scaled_stat(base_data["damage"], ENEMY_ELITE_DAMAGE_MULTIPLIER)

    assert enemy.is_elite, f"{base_data['name']} was not marked elite"
    assert enemy.max_hp == expected_hp, (
        f"{base_data['name']} max_hp {enemy.max_hp} != expected {expected_hp}"
    )
    assert enemy.hp == expected_hp, f"{base_data['name']} hp {enemy.hp} != expected {expected_hp}"
    assert enemy.damage == expected_damage, (
        f"{base_data['name']} damage {enemy.damage} != expected {expected_damage}"
    )

    for field in SPECIAL_DAMAGE_FIELDS:
        if field in base_data:
            expected = _scaled_stat(base_data[field], ENEMY_ELITE_DAMAGE_MULTIPLIER)
            actual = getattr(enemy, field)
            assert actual == expected, (
                f"{base_data['name']} {field} {actual} != expected {expected}"
            )


def test_wave_manager_elite_spawn_scaling() -> None:
    player = _make_player()

    for enemy_id, base_data in ENEMY_DATA_BY_ID.items():
        if enemy_id == "MiniBat":
            continue

        wave_manager = _make_wave_manager([player])
        wave_manager.elite_mode = True
        wave_manager._spawn_enemy(base_data)

        assert len(wave_manager.enemy_group) == 1, f"{enemy_id} did not spawn exactly once"
        enemy = next(iter(wave_manager.enemy_group))
        _assert_enemy_scaled(enemy, base_data)


def test_existing_enemy_scaling_preserves_hp_ratio_and_is_idempotent() -> None:
    player = _make_player()
    wave_manager = _make_wave_manager([player])
    base_data = ENEMY_DATA_BY_ID["Skeleton"]

    wave_manager._spawn_enemy(base_data)
    enemy = next(iter(wave_manager.enemy_group))
    enemy.hp = enemy.max_hp / 2

    wave_manager._apply_elite_scaling_to_existing_enemies()

    expected_max_hp = _scaled_stat(base_data["hp"], ENEMY_ELITE_HP_MULTIPLIER)
    expected_hp = expected_max_hp / 2
    expected_damage = _scaled_stat(base_data["damage"], ENEMY_ELITE_DAMAGE_MULTIPLIER)
    assert enemy.max_hp == expected_max_hp
    assert enemy.hp == expected_hp
    assert enemy.damage == expected_damage

    wave_manager._apply_elite_scaling_to_existing_enemies()
    assert enemy.max_hp == expected_max_hp
    assert enemy.hp == expected_hp
    assert enemy.damage == expected_damage


def test_mini_bat_elite_scaling() -> None:
    player = _make_player()
    all_sprites = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()

    mini_bat = MiniBat(Vector2(200, 200), [player], (all_sprites, enemy_group))
    mini_bat.apply_elite_scaling(
        ENEMY_ELITE_HP_MULTIPLIER,
        ENEMY_ELITE_DAMAGE_MULTIPLIER,
        preserve_hp_ratio=False,
    )

    _assert_enemy_scaled(mini_bat, MINI_BAT_ENEMY_DATA)


def main() -> None:
    pygame.init()
    try:
        test_wave_manager_elite_spawn_scaling()
        test_existing_enemy_scaling_preserves_hp_ratio_and_is_idempotent()
        test_mini_bat_elite_scaling()
    finally:
        pygame.quit()
    print("Elite scaling checks passed.")


if __name__ == "__main__":
    main()
