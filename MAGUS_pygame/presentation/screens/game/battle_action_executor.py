"""
Action execution for battle screen.

Handles move, attack, rotation, and other combat actions.
"""

from application.battle_service import BattleService
from domain.entities import Unit
from domain.value_objects import Facing, Position
from infrastructure.rendering.hex_grid import calculate_facing_to_hex
from logger.logger import get_logger

logger = get_logger(__name__)


class BattleActionExecutor:
    """Executes battle actions like move, attack, rotate."""

    def __init__(self, battle_service: BattleService):
        """Initialize action executor.

        Args:
            battle_service: Battle service managing combat state
        """
        self.battle = battle_service
        self.combat_message: str | None = None
        self.combat_message_timer = 0

    def execute_move(self, dest: Position, potential_reactors: list[Unit]) -> dict:
        """Execute movement to destination.

        Args:
            dest: Destination position
            potential_reactors: Enemy units that may react

        Returns:
            Summary dict with move results
        """
        current = self.battle.current_unit()
        summary = self.battle.move_current_unit(dest=dest, potential_reactors=potential_reactors)

        if "error" in summary:
            self.show_message(f"Move failed: {summary['error']}")
            logger.warning(f"Move failed: {summary['error']}")
        else:
            ap_spent = summary.get("ap_spent", 0)
            self.show_message(f"Moved (AP: -{ap_spent})")
            logger.info(f"{current.name} moved to {dest} (AP spent: {ap_spent})")

        return summary

    def execute_attack(
        self, target_pos: Position, attacker: Unit, defender: Unit | None
    ) -> dict | None:
        """Execute attack on target position.

        Args:
            target_pos: Target hex position
            attacker: Attacking unit
            defender: Defending unit (if any)

        Returns:
            Attack summary or None if failed
        """
        if not defender:
            self.show_message("No target at that hex")
            return None

        # Execute attack
        summary = self.battle.attack_unit(attacker, defender)

        if "error" in summary:
            self.show_message(f"Attack failed: {summary['error']}")
            logger.warning(f"Attack failed: {summary['error']}")
            return None

        # Build detailed message
        result = summary.get("result")
        if result:
            msg_parts = [f"Result: {result.outcome.value.title()}"]
            msg_parts.append(f"Hit: {result.hit}")
            msg_parts.append(f"EP: -{result.damage_to_ep}")
            msg_parts.append(f"FP: -{result.damage_to_fp}")
            self.show_message(" | ".join(msg_parts))

        ap_spent = summary.get("ap_spent", 0)
        logger.info(f"{attacker.name} attacked {defender.name} (AP spent: {ap_spent})")

        return summary

    def execute_rotation(self, direction: int, unit: Unit) -> dict:
        """Execute unit rotation.

        Args:
            direction: Rotation direction (-1 for CCW, 1 for CW)
            unit: Unit to rotate

        Returns:
            Rotation result summary
        """
        from domain.value_objects import Facing

        direction_name = "left" if direction < 0 else "right"

        # Calculate new facing
        current_facing = unit.facing.direction
        new_facing_dir = (current_facing + direction) % 6
        new_facing = Facing(new_facing_dir)

        # Execute rotation
        result = self.battle.rotate_current_unit(new_facing)

        if "error" in result:
            self.show_message(result["error"])
            logger.warning(f"Rotation failed: {result['error']}")
        else:
            ap_spent = result.get("ap_spent", 0)
            self.show_message(f"Rotated {direction_name} (AP: -{ap_spent})")
            logger.info(
                f"{unit.name} rotated {direction_name} to facing {new_facing_dir} (AP spent: {ap_spent})"
            )

        return result

    def execute_facing_change(self, target_q: int, target_r: int, unit: Unit) -> dict | None:
        """Change unit's facing to point toward target hex.

        Args:
            target_q: Target hex q coordinate
            target_r: Target hex r coordinate
            unit: Unit to rotate

        Returns:
            Rotation result or None if invalid
        """
        # Calculate facing direction
        facing_dir = calculate_facing_to_hex(unit.position.q, unit.position.r, target_q, target_r)
        if facing_dir is None:
            self.show_message("Not an adjacent hex")
            return None

        # Execute facing change
        new_facing = Facing(facing_dir)
        result = self.battle.rotate_current_unit(new_facing)

        if "error" in result:
            self.show_message(result["error"])
            logger.warning(f"Facing change failed: {result['error']}")
        else:
            ap_spent = result.get("ap_spent", 0)
            self.show_message(f"Rotated to face hex (AP: -{ap_spent})")
            logger.info(f"{unit.name} rotated to facing {facing_dir} (AP spent: {ap_spent})")

        return result

    def end_turn(self) -> None:
        """End current unit's turn."""
        current = self.battle.current_unit()
        if current:
            logger.info(f"Ending turn for {current.name}")
            self.battle.end_turn()
            # Show new active unit's name
            next_unit = self.battle.current_unit()
            if next_unit:
                self.show_message(f"{next_unit.name}'s turn")

    def show_message(self, message: str) -> None:
        """Show combat message to player.

        Args:
            message: Message text
        """
        self.combat_message = message
        self.combat_message_timer = 180  # 3 seconds at 60fps
        logger.debug(f"Combat message: {message}")

    def update_message_timer(self) -> None:
        """Update message timer and clear if expired."""
        if self.combat_message_timer > 0:
            self.combat_message_timer -= 1
            if self.combat_message_timer == 0:
                self.combat_message = None

    def inspect_hex(
        self, q: int, r: int, units: list[Unit], screen_width: int, screen_height: int
    ) -> Unit | None:
        """Inspect a hex and return unit if present.

        Args:
            q: Hex q coordinate
            r: Hex r coordinate
            units: List of all units
            screen_width: Screen width for popup positioning
            screen_height: Screen height for popup positioning

        Returns:
            Unit if found at hex, None otherwise
        """
        # Find unit at hex
        for unit in units:
            if unit.position.q == q and unit.position.r == r:
                logger.info(f"Inspecting unit: {unit.name} at ({q}, {r})")
                return unit

        logger.debug(f"No unit at ({q}, {r})")
        return None
