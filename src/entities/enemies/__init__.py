from src.entities.enemy import Enemy
from src.entities.enemies.cursed_knight import CursedKnight
from src.entities.enemies.dark_goblin import DarkGoblin
from src.entities.enemies.lich_familiar import LichFamiliar
from src.entities.enemies.plague_bat import PlagueBat
from src.entities.enemies.skeleton import Skeleton
from src.entities.enemies.stone_golem import StoneGolem
from src.entities.enemies.wraith import Wraith


ENEMY_CLASS_REGISTRY = {
    "Skeleton": Skeleton,
    "Goblin": DarkGoblin,
    "Wraith": Wraith,
    "Bat": PlagueBat,
    "Knight": CursedKnight,
    "Lich": LichFamiliar,
    "Golem": StoneGolem,
}


def create_enemy(
    enemy_id: str,
    pos,
    players,
    all_groups: tuple,
    enemy_data: dict,
    xp_orb_group=None,
    effect_group=None,
    pickup_group=None,
    projectile_group=None,
):
    enemy_class = ENEMY_CLASS_REGISTRY.get(enemy_id)
    if enemy_class is None:
        return Enemy(pos, players, all_groups, enemy_data, xp_orb_group, effect_group, pickup_group)

    return enemy_class(
        pos,
        players,
        all_groups,
        xp_orb_group=xp_orb_group,
        effect_group=effect_group,
        pickup_group=pickup_group,
        projectile_group=projectile_group,
    )


__all__ = ["ENEMY_CLASS_REGISTRY", "create_enemy"]
