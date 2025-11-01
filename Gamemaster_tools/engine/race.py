"""
Race data models using Pydantic for validation and type safety.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

# === Attribute Models ===


class AttributeModifiers(BaseModel):
    """Tulajdonság módosítók - MAGYAR nevekkel!"""

    Erő: int = Field(default=0, alias="strength")
    Állóképesség: int = Field(default=0, alias="constitution")
    Gyorsaság: int = Field(default=0, alias="speed")
    Ügyesség: int = Field(default=0, alias="dexterity")
    Karizma: int = Field(default=0, alias="charisma")
    Egészség: int = Field(default=0, alias="health")
    Intelligencia: int = Field(default=0, alias="intelligence")
    Akaraterő: int = Field(default=0, alias="willpower")
    Asztrál: int = Field(default=0, alias="astral")
    Érzékelés: int = Field(default=0, alias="perception")

    model_config = {"populate_by_name": True}  # Accepts both Hungarian and English names


class StatLimit(BaseModel):
    """Tulajdonság limit (min-max)."""

    min: int
    max: int


class StatLimits(BaseModel):
    """Összes tulajdonság limitje - MAGYAR nevekkel."""

    Erő: StatLimit | None = None
    Állóképesség: StatLimit | None = None
    Gyorsaság: StatLimit | None = None
    Ügyesség: StatLimit | None = None
    Karizma: StatLimit | None = None
    Egészség: StatLimit | None = None
    Intelligencia: StatLimit | None = None
    Akaraterő: StatLimit | None = None
    Asztrál: StatLimit | None = None
    Érzékelés: StatLimit | None = None

    model_config = {"populate_by_name": True}


class RaceAttributes(BaseModel):
    """Faj tulajdonság adatok."""

    modifiers: AttributeModifiers = Field(default_factory=AttributeModifiers)
    limits: StatLimits = Field(default_factory=StatLimits)
    hard_limits: StatLimits = Field(default_factory=StatLimits)


# === Age Models ===


class AgeCategory(BaseModel):
    """Életkor kategória."""

    name: str
    min: int
    max: int
    modifiers: AttributeModifiers = Field(default_factory=AttributeModifiers)


class AgeData(BaseModel):
    """Életkor adatok."""

    min: int
    max: int
    age_categories: list[AgeCategory] = Field(default_factory=list)


# === Skill Models ===


class RacialSkill(BaseModel):
    """Faji képzettség."""

    skill_id: str
    level: int | Literal["native"] = 0
    optional: bool = False


# === Origin Models ===


class Origin(BaseModel):
    """Származási hely."""

    id: str
    name: str
    probability: int = Field(ge=0, le=100, description="0-100% közötti valószínűség")


# === Class Restriction Models ===


class ClassRestrictions(BaseModel):
    """Kaszt korlátozások."""

    allowed_classes: list[str] = Field(default_factory=list)
    forbidden_specializations: list[str] = Field(default_factory=list)


# === Metadata ===


class RaceMetadata(BaseModel):
    """Faj metaadatok."""

    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: str = "1.0"
    migrated_from: str | None = None


# === Main Race Model ===


class Race(BaseModel):
    """Faj teljes definíciója."""

    id: str
    name: str
    description_file: str

    attributes: RaceAttributes = Field(default_factory=RaceAttributes)
    age: AgeData

    racial_skills: list[RacialSkill] = Field(default_factory=list)
    forbidden_skills: list[str] = Field(default_factory=list)

    origins: list[Origin] = Field(default_factory=list)
    class_restrictions: ClassRestrictions = Field(default_factory=ClassRestrictions)

    special_abilities: list[str] = Field(default_factory=list)

    metadata: RaceMetadata = Field(default_factory=RaceMetadata)

    def get_description(self, base_path: Path) -> str:
        """
        Betölti a leírást a markdown fájlból.

        Args:
            base_path: Data könyvtár útvonala

        Returns:
            Markdown leírás szövege
        """
        desc_path = base_path / self.description_file
        if desc_path.exists():
            return desc_path.read_text(encoding="utf-8")
        return f"# {self.name}\n\n*Leírás még nem érhető el.*"

    def get_age_category(self, age: int) -> AgeCategory | None:
        """
        Megadja az életkor kategóriát adott korhoz.

        Args:
            age: Karakter életkora

        Returns:
            AgeCategory vagy None
        """
        for category in self.age.age_categories:
            if category.min <= age <= category.max:
                return category
        return None

    def has_special_ability(self, ability_id: str) -> bool:
        """
        Ellenőrzi, hogy van-e adott speciális képesség.

        Args:
            ability_id: Képesség azonosítója

        Returns:
            True ha van, False ha nincs
        """
        return ability_id in self.special_abilities

    def can_learn_skill(self, skill_id: str) -> bool:
        """
        Ellenőrzi, hogy tanulható-e a képzettség.

        Args:
            skill_id: Képzettség azonosítója

        Returns:
            True ha tanulható, False ha tiltott
        """
        return skill_id not in self.forbidden_skills

    def can_be_class(self, class_id: str) -> bool:
        """
        Ellenőrzi, hogy választható-e az osztály.

        Args:
            class_id: Osztály azonosítója

        Returns:
            True ha választható
        """
        return class_id in self.class_restrictions.allowed_classes

    def can_be_specialization(self, spec_id: str) -> bool:
        """
        Ellenőrzi, hogy választható-e a specializáció.

        Args:
            spec_id: Specializáció azonosítója

        Returns:
            True ha választható, False ha tiltott
        """
        return spec_id not in self.class_restrictions.forbidden_specializations


# === Special Ability Models ===


class GameEffect(BaseModel):
    """Játékmechanikai hatás (flexible schema)."""

    model_config = {"extra": "allow"}  # Engedélyezi az extra mezőket


class SpecialAbility(BaseModel):
    """Speciális képesség."""

    id: str
    name: str
    description: str
    category: Literal[
        "vision",
        "senses",
        "environmental",
        "resistance",
        "learning",
        "combat",
        "psionic",
        "transformation",
    ]
    game_effect: dict[str, Any]  # Flexible JSON object
    icon: str | None = None

    def get_short_description(self) -> str:
        """Rövid leírás megjelenítéshez."""
        if len(self.description) > 100:
            return self.description[:97] + "..."
        return self.description
