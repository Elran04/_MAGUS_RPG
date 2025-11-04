"""
Race Manager - Faj adatok betöltése, kezelése, mentése.
"""

from pathlib import Path

from core.race_model import Race, SpecialAbility
from utils.data.json_io import load_json, save_json
from utils.log.logger import get_logger

logger = get_logger(__name__)


class RaceManager:
    """Faj adatok kezelője."""

    def __init__(self, data_dir: Path):
        """
        Inicializálás.

        Args:
            data_dir: Data könyvtár útvonala (pl. Gamemaster_tools/data)
        """
        self.data_dir = Path(data_dir)
        self.races_dir = self.data_dir / "races"
        # special_abilities.json is in the races directory
        self.special_abilities_file = self.races_dir / "special_abilities.json"

        self._races: dict[str, Race] = {}
        self._special_abilities: dict[str, SpecialAbility] = {}

        logger.info(f"RaceManager inicializálva: {self.data_dir}")

    def load_all(self) -> None:
        """Betölti az összes fajt és speciális képességet."""
        logger.info("Fajok és képességek betöltése...")

        # Speciális képességek betöltése
        try:
            if self.special_abilities_file.exists():
                abilities_data = load_json(str(self.special_abilities_file), default={})
                for ability_id, ability_dict in abilities_data.items():
                    self._special_abilities[ability_id] = SpecialAbility(**ability_dict)
                logger.info(f"✓ {len(self._special_abilities)} speciális képesség betöltve")
            else:
                logger.warning(
                    f"Speciális képességek fájl nem található: {self.special_abilities_file}"
                )
        except OSError as e:
            logger.error(f"Hiba speciális képességek betöltése során: {e}", exc_info=True)

        # Fajok betöltése
        try:
            if not self.races_dir.exists():
                logger.warning(f"Races könyvtár nem található: {self.races_dir}")
                return

            loaded_count = 0
            for json_file in self.races_dir.glob("*.json"):
                # Skip special_abilities.json if it's in the races directory
                if json_file.name == "special_abilities.json":
                    continue

                try:
                    race_data = load_json(str(json_file), default={})
                    race = Race(**race_data)
                    self._races[race.id] = race
                    loaded_count += 1
                except OSError as e:
                    logger.error(f"Hiba {json_file.name} betöltése során: {e}")

            logger.info(f"✓ {loaded_count} faj betöltve")

        except OSError as e:
            logger.error(f"Hiba fajok betöltése során: {e}", exc_info=True)

    def get_race(self, race_id: str) -> Race | None:
        """
        Faj lekérése ID alapján.

        Args:
            race_id: Faj azonosítója

        Returns:
            Race objektum vagy None
        """
        return self._races.get(race_id)

    def get_race_by_name(self, race_name: str) -> Race | None:
        """
        Faj lekérése név alapján.

        Args:
            race_name: Faj neve

        Returns:
            Race objektum vagy None
        """
        for race in self._races.values():
            if race.name == race_name:
                return race
        return None

    def get_all_races(self) -> list[Race]:
        """
        Összes faj listája.

        Returns:
            Race objektumok listája
        """
        return sorted(self._races.values(), key=lambda r: r.name)

    def get_race_names(self) -> list[str]:
        """
        Fajok neveinek listája.

        Returns:
            Fajnevek listája ABC sorrendben
        """
        return sorted([race.name for race in self._races.values()])

    def get_special_ability(self, ability_id: str) -> SpecialAbility | None:
        """
        Speciális képesség lekérése ID alapján.

        Args:
            ability_id: Képesség azonosítója

        Returns:
            SpecialAbility vagy None
        """
        return self._special_abilities.get(ability_id)

    def get_all_special_abilities(self) -> list[SpecialAbility]:
        """
        Összes speciális képesség listája.

        Returns:
            SpecialAbility objektumok listája
        """
        return sorted(self._special_abilities.values(), key=lambda a: a.name)

    def get_race_special_abilities(self, race_id: str) -> list[SpecialAbility]:
        """
        Egy faj összes speciális képessége.

        Args:
            race_id: Faj azonosítója

        Returns:
            SpecialAbility objektumok listája
        """
        race = self.get_race(race_id)
        if not race:
            return []

        abilities = []
        for ability_id in race.special_abilities:
            ability = self._special_abilities.get(ability_id)
            if ability:
                abilities.append(ability)
            else:
                logger.warning(f"Hiányzó speciális képesség: {ability_id} a {race.name} fajnál")

        return abilities

    def save_race(self, race: Race) -> None:
        """
        Faj mentése JSON fájlba.

        Args:
            race: Race objektum
        """
        try:
            from datetime import datetime

            # Metadata frissítése
            race.metadata.updated_at = datetime.now().isoformat()

            # Fájl mentése
            race_file = self.races_dir / f"{race.id}.json"
            save_json(str(race_file), race.model_dump(mode="json"), create_dirs=True)

            # Cache frissítése
            self._races[race.id] = race

            logger.info(f"✓ Faj mentve: {race.name} ({race_file.name})")

        except (OSError, TypeError) as e:
            logger.error(f"Hiba faj mentése során ({race.name}): {e}", exc_info=True)
            raise

    def create_race(self, race_id: str, name: str, **kwargs) -> Race:
        """
        Új faj létrehozása.

        Args:
            race_id: Faj azonosítója
            name: Faj neve
            **kwargs: További opcionális paraméterek

        Returns:
            Új Race objektum
        """
        from core.race_model import AgeData, ClassRestrictions, RaceAttributes, RaceMetadata

        # Alapértelmezett értékek
        defaults = {
            "description_file": f"races/descriptions/{race_id}.md",
            "attributes": RaceAttributes(),
            "age": AgeData(min=13, max=100, age_categories=[]),
            "class_restrictions": ClassRestrictions(allowed_classes=[]),
            "metadata": RaceMetadata(),
        }

        # Merge kwargs
        race_data = {**defaults, **kwargs, "id": race_id, "name": name}

        race = Race(**race_data)
        self.save_race(race)

        logger.info(f"✓ Új faj létrehozva: {name}")
        return race

    def delete_race(self, race_id: str) -> bool:
        """
        Faj törlése.

        Args:
            race_id: Faj azonosítója

        Returns:
            True ha sikeres, False ha nem
        """
        try:
            race = self.get_race(race_id)
            if not race:
                logger.warning(f"Törlés sikertelen: nem létező faj ({race_id})")
                return False

            # JSON fájl törlése
            race_file = self.races_dir / f"{race_id}.json"
            if race_file.exists():
                race_file.unlink()

            # Cache-ből törlés
            self._races.pop(race_id, None)

            logger.info(f"✓ Faj törölve: {race.name}")
            return True

        except OSError as e:
            logger.error(f"Hiba faj törlése során ({race_id}): {e}", exc_info=True)
            return False

    def save_special_ability(self, ability: SpecialAbility) -> None:
        """
        Speciális képesség mentése.

        Args:
            ability: SpecialAbility objektum
        """
        try:
            # Betöltjük az összes képességet
            all_abilities = load_json(str(self.special_abilities_file), default={})

            # Frissítjük az aktuális képességet
            all_abilities[ability.id] = ability.model_dump(mode="json")

            # Visszamentjük
            save_json(str(self.special_abilities_file), all_abilities, create_dirs=True)

            # Cache frissítése
            self._special_abilities[ability.id] = ability

            logger.info(f"✓ Speciális képesség mentve: {ability.name}")

        except (OSError, TypeError) as e:
            logger.error(f"Hiba képesség mentése során ({ability.name}): {e}", exc_info=True)
            raise

    def delete_special_ability(self, ability_id: str) -> bool:
        """Speciális képesség törlése az adatbázisból és a cache-ből."""
        try:
            # Betöltjük az összes képességet
            all_abilities = load_json(str(self.special_abilities_file), default={})

            if ability_id not in all_abilities:
                return False

            # Törlés
            all_abilities.pop(ability_id, None)

            # Visszamentjük
            save_json(str(self.special_abilities_file), all_abilities, create_dirs=True)

            # Cache frissítése
            self._special_abilities.pop(ability_id, None)

            logger.info(f"✓ Speciális képesség törölve: {ability_id}")
            return True

        except (OSError, TypeError) as e:
            logger.error(f"Hiba képesség törlése során ({ability_id}): {e}", exc_info=True)
            return False
