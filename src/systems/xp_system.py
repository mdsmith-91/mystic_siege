from settings import BASE_XP_REQUIRED, XP_SCALE_FACTOR, FRIAR_HEAL_PER_XP
from src.utils.audio_manager import AudioManager

class XPSystem:
    def __init__(self):
        self.current_xp = 0.0
        self.current_level = 1
        self.xp_to_next = BASE_XP_REQUIRED
        self.levelup_count = 0

    def update(self, dt, player, xp_orb_group):
        """Handle XP collection and orb pickup."""
        if not getattr(player, "can_collect_xp", player.is_alive):
            return

        pickup_radius_sq = player.pickup_radius * player.pickup_radius

        # For each orb in xp_orb_group:
        for orb in xp_orb_group:
            # dist_sq = squared distance from player.pos to orb.rect.center
            dist_sq = (player.pos - orb.rect.center).length_squared()

            # if dist_sq <= pickup_radius_sq and not orb.collected:
            if dist_sq <= pickup_radius_sq and not orb.collected:
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
