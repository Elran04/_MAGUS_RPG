# 🗺️ MAGUS RPG System — Development Roadmap

## 🎯 Overview
This roadmap outlines the current status and future development steps for the **MAGUS RPG System**, which consists of two main modules:
- **GM Toolkit (PySide6-based)** – used for editing and managing game data.  
- **Game Demo (Pygame-based)** – a prototype environment for gameplay and combat testing.  

---


1. 🧩 Core Structure

✅ Maintain two separate main modules (main.py for GM Toolkit and Game Demo).

✅ Both run independently and share logic through common libraries.

✅ Modularization: split files exceeding ~400 lines into smaller submodules.

🟨 Gradually introduce common utility packages (e.g., core, managers, models) for cleaner dependency structure.


2. 💾 Data Management

✅ Each dataset (skills, classes, equipment, races) has its own DataManager.

✅ Consistent CRUD functionality across JSON and SQLite data sources.

✅ Hybrid storage: SQLite for classes/skills/combat_stats, JSON for races/equipment/characters.

✅ RaceManager: Loads all races from JSON → Pydantic models (race_model.py with Race, RaceAttributes, RacialSkill, AgeCategory).

✅ ClassDBManager: Query wrapper for class_data.db (classes, combat_stats, class_skills, specialisations, starting_equipment tables).

✅ SkillManager: Loads skills from skills_data.db with prerequisites, KP costs, level descriptions.

🟨 Evaluate a unified storage system for runtime saves (e.g., full SQLite migration). (Current hybrid works, no migration planned)

🟩 Introduce optional lightweight persistence for temporary state (e.g., TinyDB or orjson-based caches). (Not started)

� Design an intermediate layer for "runtime data" (temporary character states, adventure states, etc.). (Not started)


3. 🧙 GM Toolkit (PySide6)

Current Features:

✅ Skill Editor (fully implemented with CRUD, prerequisites, KP costs, descriptions)

✅ Class Editor (full class/spec management, combat stats, level requirements, skills)

✅ Equipment Editor (weapons, armor, general equipment with materials/quality)

✅ Character Creator (wizard with class/spec selection, skills, placeholder resolution)

✅ Race Editor (11 races in JSON, full editor with attributes, skills, age categories, special abilities)

Planned / Ongoing Enhancements:

🟨 Enhance UI/UX with better layout scaling, icons, and polished dark mode. (Dark mode ✅, scaling partial)

🟨 Add validation and tooltips for input fields. (Validation ✅, tooltips partial)

🟥 Item Templates (not started)

✅ Race Editor and JSON Storage (11 races: elf, ember, felelf, goblin, khal, torpe, udvari_ork, wier, amund, dzsenn + special_abilities.json)

✅ Race Descriptions and Special Ability Handling (RaceManager loads JSON → Pydantic models, integrated in character creation)

✅ Racial bonuses and automatic racial skills (RaceAttributes with modifiers, limits, hard_limits; RacialSkill model with skill_id + level)

🟨 Expand Skill Point System in Character Generation:

✅ Integrate Ügyesség (Dexterity) and Intelligencia (Intelligence) bonuses (AttributesDisplayWidget shows derived FP/ÉP/KP).

🟥 Handle skill categories (Gyakorlás, Tanulás) for bonus allocation per level (not implemented).

🟥 Continue implementing inventory generation logic:

🟥 Random gold allocation and starting equipment purchasing (starting_equipment DB table exists, UI placeholder only).

🟥 Class-based starting gear setup (schema ready, not wired to character creation).

🟥 Add Place of Birth and Character Origin systems tied to class specialization and race (Origin model in race_model.py, not in UI).

🟨 Implement Racial and Class Descriptions panels for richer character info (class descriptions partial, race descriptions loaded via race.get_description()).


4. ⚔️ Game Demo (Pygame)

Current Features:

✅ Two test characters loaded from JSON.

✅ Working melee combat mechanics.

✅ Functional hex grid and basic turn system.

✅ Initiative and charge mechanics.

Next Steps:

🟥 Camera movement and dynamic map scaling.

🟥 Map loading from JSON or tile sets.

🟥 Environmental elements (obstacles, height, interactive objects).

🟥 Expand combat to support ranged attacks and area effects.

🟥 Implement stamina system:

Running, swimming, armor weight, weapon use, and carrying load affect stamina.

Stamina affects combat performance (e.g., reduced hit chance, slower recovery).

Collapse or penalties at low stamina.

🟥 Implement combat conditions: fatigue, injured, bleeding, dazed, blinded, hamstrung, etc.

🟥 Implement layered armor system and localized damage (body part-based).

🟥 Refine damage and resistance logic:

Damage type modifiers and thresholds (FP → ÉP conversion).

Pain endurance and hit point correlations.

🟥 Add combat scenario setup tool and random combat generator.

🟥 Begin skill integration into combat (skill modifiers, equipped item bonuses).


5. 🧝 Character System

Current:

✅ Characters load from JSON with stats and equipment.

✅ Character Creator wizard with class/spec selection from SQLite.

✅ Race system integrated: RaceManager loads 11 races from JSON → Pydantic models.

✅ Racial bonuses, attribute modifiers, age categories, racial skills, forbidden skills.

✅ Skills step with placeholder resolution, KP tracking, prerequisite checking.

Planned:

� Integrate SQLite-based class/skill data dynamically. (ClassDBManager + SkillDatabaseHelper in use, not full ORM)

🟥 Implement XP system, leveling, and stat growth (CombatStats dataclass exists, XP calculations present in character_model.py, not wired to UI).

✅ Add race system with racial skills and stat bonuses (RaceAttributes, RacialSkill, AgeCategory models complete).

🟥 Implement origin and birthplace logic, tied to specialization choices (Origin model exists in race_model.py, not in character creation UI).

🟥 Add save/load for characters and multiple active party slots (save_character exists, no party/load UI).

� Improve inventory:

🟥 Track gold, gear weight, and capacity (starting_equipment table schema ready, not wired).

🟥 Equipable vs non-equipable item handling (item_model.py exists, not integrated).

🟨 Begin unifying JSON → runtime model → persistent database logic (race_model.py + RaceManager ✅, class/skill/item models not integrated).


6. ⚔️ Combat System

Current:

✅ Basic melee combat functional, tested with two characters.

✅ Initiative and turn queue.

✅ Armor layering system (armor_type + layer fields, its implemented in the armor.json)

Planned Enhancements:

🟥 Multi-opponent combat and area-based targeting.

🟥 Penetration logic, hit localization, and detailed wound conditions.

🟥 Skill and ability integration (e.g., parry, dodge, aimed strike).

🟥 Stamina system integration.

🟥 Combat conditions and ongoing effects.

🟥 Visual combat feedback and logs (damage text, icons, overlays).


7. 🧠 Game Logic & Progression

🟥 Introduce simple AI logic (targeting, attack choice, retreat).

🟥 Scalable difficulty and encounter generation.

🟥 Scripted events and environmental triggers.

🟥 Begin framework for adventure mode:

Non-combat map movement, exploration events, and encounters.

Inventory use, fatigue, and travel modifiers.

🟥 Adventure state persistence (party, fatigue, active quests).


8. ⚙️ Architecture & Constants

✅ Core settings centralized in config.py.

🟨 Move repeated constants (window size, grid size, UI scale) into config file. (Partial)

🟩 Add settings.json for user preferences and runtime configurations.

🟨 Introduce constants/game_balance.py for tunable gameplay parameters (XP rates, stamina drain, etc.).

9. 🔧 Version Control & Collaboration

✅ Git + GitHub in active use.

🟨 Update README.md with usage/setup instructions. (Partial)

🟨 Begin semantic version tagging (v0.1-alpha, v0.2-alpha…).

🟨 Add simple “Development Guidelines” section for consistency and future scaling.


10. 🎨 Assets & Visuals

✅ Using free placeholder top-down sprites and tilesets.

✅ Maintain folder structure: /assets/sprites/ (UI, maps to be added).

🟥 Expand asset management with /assets/tiles/, /assets/ui/, and /assets/maps/.

🟥 Plan gradual replacement with consistent, custom-made assets.


11. 🧭 Major Milestones
1️⃣ Character System Completion

✅ Race editor and JSON data (11 races + special abilities)

✅ Race integration in character creation (RaceManager + Pydantic models)

🟨 Skill/class integration from SQLite (ClassDBManager + SkillDatabaseHelper in use, not full model integration)

� Inventory, gold, and origin logic (DB schema ready, UI placeholder only)

� Save/load support (save_character exists, no load/party UI)

2️⃣ Expanded Combat Framework

🟥 Stamina system and combat conditions

🟥 Ranged and thrown weapon support

🟥 Damage localization and layered armor (armor schema with layer field exists)

3️⃣ GM Toolkit Extensions

✅ Race editor complete

🟥 Item templates (not started)

� Improved validation and layout polish (validation ✅, tooltips/polish partial)

✅ Integrated skill point logic (AttributesDisplayWidget calculates derived KP)

4️⃣ Playable Demo Scenario

🟥 Configurable combat scenario generator

🟥 Early adventure mode prototype

Current Status

✅ GM Toolkit: Functional, modular, and actively expanding (Skill/Class/Equipment/Race editors complete)

✅ Character Creator: Wizard with class/spec/race/skills selection, placeholder resolution, attributes display

✅ Game Demo: Playable with melee combat

✅ Data Layer: JSON + SQLite hybrid in good shape (RaceManager, ClassDBManager, SkillManager all functional)

✅ Race System: Complete with Pydantic models, RaceManager, 11 races in JSON

🟨 Next focus: Implement skill selection during character creation.

🟨 Next focus: Equipment step implementation (starting_equipment DB schema ready, UI is placeholder)

🟨 Next focus: Extend combat with stamina, conditions, armor, and ranged logic