"""Scenario Repository - Lists scenarios and resolves background assets."""

import json

from config import BACKGROUND_SPRITES_DIR, SCENARIOS_DIR, get_scenario_json_path
from logger.logger import get_logger

logger = get_logger(__name__)


class ScenarioRepository:
    """Repository for scenario metadata and assets."""

    def list_scenarios(self) -> list[str]:
        """Return available scenario names (stem without extension)."""
        try:
            files = [f.stem for f in SCENARIOS_DIR.iterdir() if f.suffix.lower() == ".json"]
            return sorted(files) if files else ["default"]
        except Exception as e:
            logger.warning(f"Failed to list scenarios: {e}")
            return ["default"]

    def load_scenario(self, scenario_name: str) -> dict | None:
        """Load scenario data from JSON file.

        Args:
            scenario_name: Scenario name (without .json extension)

        Returns:
            Scenario data dict or None if failed
        """
        try:
            path = get_scenario_json_path(f"{scenario_name}.json")
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded scenario: {scenario_name}")
            return data
        except FileNotFoundError:
            logger.error(f"Scenario file not found: {scenario_name}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in scenario {scenario_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load scenario {scenario_name}: {e}")
            return None

    def save_scenario(self, scenario_name: str, data: dict) -> bool:
        """Save scenario data to JSON file.

        Args:
            scenario_name: Scenario name (without .json extension)
            data: Scenario data dict

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            path = get_scenario_json_path(f"{scenario_name}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved scenario: {scenario_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to save scenario {scenario_name}: {e}")
            return False

    def resolve_background(self, scenario_name: str) -> str | None:
        """Pick a background filename for a given scenario name.

        Tries png, jpg, jpeg. Falls back to grass_bg.jpg if present.
        """
        candidates = [f"{scenario_name}.png", f"{scenario_name}.jpg", f"{scenario_name}.jpeg"]
        for cand in candidates:
            path = BACKGROUND_SPRITES_DIR / cand
            if path.exists():
                return cand

        fallback = "grass_bg.jpg"
        if (BACKGROUND_SPRITES_DIR / fallback).exists():
            logger.debug(
                f"No specific background for '{scenario_name}', using fallback: {fallback}"
            )
            return fallback
        return None
