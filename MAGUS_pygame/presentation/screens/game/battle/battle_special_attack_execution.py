"""
Special attack execution registry.

Validates specific targets and executes special attacks:
- Checks if target is in range
- Validates line of sight and positioning
- Executes the attack action

Called AFTER entering attack mode, when clicking on a target.
"""

from typing import Callable, Optional

from domain.entities import Unit
from domain.value_objects import Position
from logger.logger import get_logger

logger = get_logger(__name__)


class SpecialAttackRegistry:
    """Registry for special attacks with validation and execution handlers."""

    def __init__(self, battle_service, action_executor):
        """Initialize special attack registry.

        Args:
            battle_service: BattleService for validation
            action_executor: BattleActionExecutor for execution
        """
        self.battle = battle_service
        self.action_executor = action_executor

        # Build registry: attack_id -> (validate_target_fn, execute_fn)
        # validate_target_fn: checks if THIS specific target is valid
        # execute_fn: performs the attack action
        self._registry = {
            "charge": (
                self.battle.validate_charge_target,
                self.action_executor.execute_charge,
            ),
            "dagger_combo": (
                self.battle.validate_attack_combination_target,
                self.action_executor.execute_attack_combination,
            ),
            "shield_bash": (
                self.battle.validate_shield_bash_target,
                self.action_executor.execute_shield_bash,
            ),
        }

    def register(
        self, attack_id: str, validate_fn: Callable, execute_fn: Callable
    ) -> None:
        """Register a new special attack for execution.

        Args:
            attack_id: Unique identifier for the attack
            validate_fn: Target validation function(unit, target_pos) -> (is_valid, error_msg)
            execute_fn: Attack execution function(target_pos) -> dict
        """
        self._registry[attack_id] = (validate_fn, execute_fn)
        logger.info(f"Registered special attack: {attack_id}")

    def validate_and_execute(
        self, attack_id: str, current_unit: Unit, target_pos: Position
    ) -> bool:
        """Validate specific target and execute special attack.

        Checks target-specific conditions (range, line of sight, positioning)
        and executes the attack if valid.

        Args:
            attack_id: Special attack identifier
            current_unit: Current unit performing attack
            target_pos: Target hex position to attack

        Returns:
            True if target was valid and attack executed, False otherwise
        """
        if attack_id not in self._registry:
            logger.warning(f"Unknown special attack: {attack_id}")
            return False

        validate_fn, execute_fn = self._registry[attack_id]

        # Validate
        is_valid, error_msg = validate_fn(current_unit, target_pos)
        if not is_valid:
            self.action_executor.show_message(error_msg)
            return False

        # Execute
        execute_fn(target_pos)
        return True

    def get_all_ids(self) -> list[str]:
        """Get list of all registered special attack IDs.

        Returns:
            List of attack identifiers
        """
        return list(self._registry.keys())

    def is_registered(self, attack_id: str) -> bool:
        """Check if special attack is registered.

        Args:
            attack_id: Special attack identifier

        Returns:
            True if registered
        """
        return attack_id in self._registry
