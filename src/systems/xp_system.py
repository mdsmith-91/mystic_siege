from settings import BASE_XP_REQUIRED, XP_SCALE_FACTOR, FRIAR_HEAL_PER_XP
from src.utils.audio_manager import AudioManager

class XPSystem:
    def __init__(self):
        self.current_xp = 0.0
        self.current_level = 1
        self.xp_to_next = BASE_XP_REQUIRED
        self.levelup_count = 0

    def _slot_order(self, player) -> int:
        slot = getattr(player, "slot", None)
        return slot.index if slot is not None else 0

    @staticmethod
    def _can_collect(player) -> bool:
        return getattr(player, "can_collect_xp", player.is_alive)

    @classmethod
    def update_all(cls, players, xp_systems, xp_orb_group) -> None:
        """Resolve orb collection in one pass to avoid repeated player-orb scans."""
        collector_entries = [
            (player, xp_system)
            for player, xp_system in zip(players, xp_systems)
            if cls._can_collect(player)
        ]
        if not collector_entries:
            return

        for orb in xp_orb_group:
            if orb.collected:
                continue

            best_player = None
            best_xp_system = None
            best_dist_sq = 0.0
            best_slot_order = 0
            orb_center = orb.rect.center

            for player, xp_system in collector_entries:
                diff = player.pos - orb_center
                dist_sq = diff.length_squared()
                pickup_radius_sq = player.pickup_radius * player.pickup_radius
                if dist_sq > pickup_radius_sq:
                    continue

                slot_order = xp_system._slot_order(player)
                if (
                    best_player is None
                    or dist_sq < best_dist_sq
                    or (dist_sq == best_dist_sq and slot_order < best_slot_order)
                ):
                    best_player = player
                    best_xp_system = xp_system
                    best_dist_sq = dist_sq
                    best_slot_order = slot_order

            if best_player is not None and best_xp_system is not None:
                best_xp_system.collect_orb(orb, best_player)

    def update(self, dt, player, xp_orb_group, players=None):
        """Handle XP collection and orb pickup."""
        if not self._can_collect(player):
            return

        players = players or [player]
        pickup_radius_sq = player.pickup_radius * player.pickup_radius

        # For each orb in xp_orb_group:
        for orb in xp_orb_group:
            if orb.collected:
                continue

            # dist_sq = squared distance from player.pos to orb.rect.center
            orb_center = orb.rect.center
            dist_sq = (player.pos - orb_center).length_squared()

            chosen_collector = None
            chosen_dist_sq = 0.0
            chosen_slot_order = 0
            for candidate in players:
                if not self._can_collect(candidate):
                    continue
                candidate_dist_sq = (candidate.pos - orb_center).length_squared()
                candidate_radius_sq = candidate.pickup_radius * candidate.pickup_radius
                if candidate_dist_sq > candidate_radius_sq:
                    continue
                slot_order = self._slot_order(candidate)
                if (
                    chosen_collector is None
                    or candidate_dist_sq < chosen_dist_sq
                    or (candidate_dist_sq == chosen_dist_sq and slot_order < chosen_slot_order)
                ):
                    chosen_collector = candidate
                    chosen_dist_sq = candidate_dist_sq
                    chosen_slot_order = slot_order

            if chosen_collector is not player:
                continue

            # if dist_sq <= pickup_radius_sq and not orb.collected:
            if dist_sq <= pickup_radius_sq:
                self.collect_orb(orb, player)

    def collect_orb(self, orb, player):
        """Collect an XP orb."""
        # orb.collected = True
        orb.collected = True

        # orb.kill()
        orb.kill()
        AudioManager.instance().play_sfx(AudioManager.XP_PICKUP)

        # gained = orb.value * player.xp_multiplier
        gained = orb.value * player.xp_multiplier

        # current_xp += gained
        self.current_xp += gained

        # player.orbs_collected += 1
        player.orbs_collected += 1

        # Friar passive: heal based on XP gained, not orb count
        if player.hero_class == "Friar":
            player.heal(gained * FRIAR_HEAL_PER_XP)

        # check_levelup()
        self.check_levelup()

    def check_levelup(self) -> bool:
        """Check if the player has leveled up."""
        # While current_xp >= xp_to_next:
        while self.current_xp >= self.xp_to_next:
            # current_xp -= xp_to_next
            self.current_xp -= self.xp_to_next

            # current_level += 1
            self.current_level += 1

            # xp_to_next = int(BASE_XP_REQUIRED * (XP_SCALE_FACTOR ** current_level))
            self.xp_to_next = int(BASE_XP_REQUIRED * (XP_SCALE_FACTOR ** self.current_level))

            # increment levelup_count
            self.levelup_count += 1
            AudioManager.instance().play_sfx(AudioManager.LEVEL_UP)

        # return whether any levelup is pending
        return self.levelup_count > 0

    def consume_levelup(self):
        """Consume one pending level up."""
        self.levelup_count = max(0, self.levelup_count - 1)

    def xp_progress(self) -> float:
        """Return XP progress toward next level (0.0 to 1.0)."""
        return min(1.0, self.current_xp / self.xp_to_next)
