"""
Centralized validation helpers for GM Tools editors.
Avoid heavy dependencies; perform lightweight schema checks.
"""

from typing import Any


class ValidationError(Exception):
    pass


def _require_keys(data: dict[str, Any], keys: list[str], ctx: str = ""):
    for k in keys:
        if k not in data:
            raise ValidationError(f"Missing required field '{k}' in {ctx or 'data'}")


def validate_skill(skill: dict[str, Any]) -> None:
    """Validate a skill dict before saving.
    Supports two types:
    - skill_type == 1: level-based costs using kp_costs {'1'..'6': int}
    - skill_type == 2: percent-based using kp_per_3_percent: int
    Placeholder skills (main_category == 'Helyfoglaló képzettségek' or placeholder == 1) are validated lightly.
    """
    # Light validation for placeholders
    if skill.get("placeholder", 0) == 1 or skill.get("main_category") == "Helyfoglaló képzettségek":
        _require_keys(
            skill, ["id", "name", "main_category", "sub_category"], ctx="skill (placeholder)"
        )
        return

    _require_keys(
        skill,
        [
            "name",
            "id",
            "main_category",
            "sub_category",
            "acquisition_method",
            "acquisition_difficulty",
            "skill_type",
            "prerequisites",
            "description_file",
        ],
        ctx="skill",
    )

    st = skill.get("skill_type", 1)
    if st == 1:
        # KP costs: dict with string keys '1'..'6' and non-negative ints
        kp = skill.get("kp_costs", {})
        if not isinstance(kp, dict):
            raise ValidationError("kp_costs must be a dict with keys '1'..'6'")
        for i in range(1, 7):
            key = str(i)
            if key not in kp:
                raise ValidationError(f"kp_costs missing level '{key}'")
            val = kp[key]
            if not isinstance(val, int) or val < 0:
                raise ValidationError(f"kp_costs['{key}'] must be non-negative int")
    elif st == 2:
        kp3 = skill.get("kp_per_3_percent")
        if kp3 is None or not isinstance(kp3, int) or kp3 < 0:
            raise ValidationError(
                "kp_per_3_percent must be a non-negative int for percent-based skills"
            )
    else:
        raise ValidationError("skill_type must be 1 (szint) or 2 (%)")

    # Prerequisites: dict with per-level dicts
    prereq = skill.get("prerequisites", {})
    if not isinstance(prereq, dict):
        raise ValidationError("prerequisites must be a dict")
    for i in range(1, 7):
        level = str(i)
        lv = prereq.get(level, {"képesség": [], "képzettség": []})
        if not isinstance(lv, dict):
            raise ValidationError(f"prerequisites['{level}'] must be a dict")
        for key in ("képesség", "képzettség"):
            if key in lv and not isinstance(lv[key], list):
                raise ValidationError(f"prerequisites['{level}']['{key}'] must be a list")

    # description_file: empty or string
    df = skill.get("description_file", "")
    if df is not None and not isinstance(df, str):
        raise ValidationError("description_file must be a string")


def validate_armor(armor: dict[str, Any]) -> None:
    _require_keys(
        armor, ["id", "name", "parts", "mgt", "weight", "price", "description"], ctx="armor"
    )
    # parts: dict of part->int
    parts = armor.get("parts", {})
    if not isinstance(parts, dict):
        raise ValidationError("parts must be a dict")
    for k, v in parts.items():
        if not isinstance(v, int) or v < 0:
            raise ValidationError(f"parts['{k}'] must be non-negative int")
    # protection_overrides: dict of sub->int
    overrides = armor.get("protection_overrides", {})
    if not isinstance(overrides, dict):
        raise ValidationError("protection_overrides must be a dict")
    for k, v in overrides.items():
        if not isinstance(v, int) or v < 0:
            raise ValidationError(f"protection_overrides['{k}'] must be non-negative int")
    # numeric checks
    if not isinstance(armor.get("mgt"), int):
        raise ValidationError("mgt must be int")
    if not isinstance(armor.get("weight"), (int, float)):
        raise ValidationError("weight must be number")
    if not isinstance(armor.get("price"), int):
        raise ValidationError("price must be int in base units")
    # armor_type: optional but if present must be one of expected values
    armor_type = armor.get("armor_type")
    if armor_type is not None and armor_type not in {"plate", "flexible_metal", "leather"}:
        raise ValidationError("armor_type must be one of 'plate', 'flexible_metal', 'leather'")
    # layer: optional but if present must be 1, 2, or 3
    layer = armor.get("layer")
    if layer is not None and (not isinstance(layer, int) or layer not in {1, 2, 3}):
        raise ValidationError("layer must be int 1, 2, or 3")


def validate_general_equipment(item: dict[str, Any]) -> None:
    _require_keys(
        item, ["id", "name", "description", "weight", "price", "category"], ctx="equipment"
    )
    cat = item.get("category")
    if cat in ("eszköz", "élelem", "speciális", "lőszer") and "space" not in item:
        raise ValidationError("space is required for selected category")
    if cat == "tároló" and "capacity" not in item:
        raise ValidationError("capacity is required for 'tároló'")
    if cat == "élelem" and ("freshness" not in item or "durability" not in item):
        raise ValidationError("freshness and durability required for 'élelem'")
    if not isinstance(item.get("weight"), (int, float)):
        raise ValidationError("weight must be number")
    if not isinstance(item.get("price"), int):
        raise ValidationError("price must be int in base units")
