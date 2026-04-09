class PickupSystem:
    @staticmethod
    def _can_collect(player) -> bool:
        return getattr(player, "can_collect_xp", player.is_alive)

    @staticmethod
    def _slot_order(player) -> int:
        slot = getattr(player, "slot", None)
        return slot.index if slot is not None else 0

    @classmethod
    def update_all(cls, players, pickup_group, game_scene) -> None:
        collectors = [player for player in players if cls._can_collect(player)]
        if not collectors:
            return

        for pickup in list(pickup_group):
            best_player = None
            best_dist_sq = 0.0
            best_slot_order = 0
            pickup_center = pickup.pos
            pickup_radius_sq = pickup.collect_radius * pickup.collect_radius

            for player in collectors:
                diff = player.pos - pickup_center
                dist_sq = diff.length_squared()
                if dist_sq > pickup_radius_sq:
                    continue

                slot_order = cls._slot_order(player)
                if (
                    best_player is None
                    or dist_sq < best_dist_sq
                    or (dist_sq == best_dist_sq and slot_order < best_slot_order)
                ):
                    best_player = player
                    best_dist_sq = dist_sq
                    best_slot_order = slot_order

            if best_player is not None:
                pickup.collect(best_player, game_scene)
