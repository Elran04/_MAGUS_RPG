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

✅ Each dataset (skills, classes, equipment, etc.) has its own DataManager.

✅ Consistent CRUD functionality across JSON and SQLite data sources.

🟨 Evaluate a unified storage system for runtime saves (e.g., SQLite instead of JSON). (Hybrid currently in use)

🟩 Introduce optional lightweight persistence for temporary state (e.g., TinyDB or orjson-based caches).

🟨 Design an intermediate layer for “runtime data” (temporary character states, adventure states, etc.).


3. 🧙 GM Toolkit (PySide6)

Current Features:

✅ Skill Editor

✅ Class Editor

✅ Equipment Editor

✅ Character Creator

Planned / Ongoing Enhancements:

🟨 Enhance UI/UX with better layout scaling, icons, and polished dark mode. (Dark mode and some scaling done)

🟨 Add validation and tooltips for input fields. (Validation present, tooltips partial)

🟥 Item Templates (not started)

🟥 Race Editor (not started) → Now a priority

🟥 Race Descriptions and Special Ability Handling

Save race data to JSON (currently .py modules).

Add racial bonuses and automatic racial skills.

🟨 Expand Skill Point System in Character Generation:

Integrate Ügyesség (Dexterity) and Intelligencia (Intelligence) bonuses.

Handle skill categories (Gyakorlás, Tanulás) for bonus allocation per level.

🟥 Continue implementing inventory generation logic:

Random gold allocation and starting equipment purchasing.

Class-based starting gear setup.

🟥 Add Place of Birth and Character Origin systems tied to class specialization and race.

🟨 Implement Racial and Class Descriptions panels for richer character info.


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

Planned:

🟥 Integrate SQLite-based class/skill data dynamically. (Partial)

🟥 Implement XP system, leveling, and stat growth.

🟥 Add race system with racial skills and stat bonuses.

🟥 Implement origin and birthplace logic, tied to specialization choices.

🟥 Add save/load for characters and multiple active party slots.

🟥 Improve inventory:

T rack gold, gear weight, and capacity.

Equipable vs non-equipable item handling.

🟨 Begin unifying JSON → runtime model → persistent database logic.


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

🟥 Race editor and JSON data

🟨 Skill/class integration from SQLite

🟨 Inventory, gold, and origin logic

🟨 Save/load support

2️⃣ Expanded Combat Framework

🟥 Stamina system and combat conditions

🟥 Ranged and thrown weapon support

🟥 Damage localization and layered armor

3️⃣ GM Toolkit Extensions

🟥 Race and item templates

🟥 Improved validation and layout polish

🟥 Integrated skill point logic

4️⃣ Playable Demo Scenario

🟥 Configurable combat scenario generator

🟥 Early adventure mode prototype

Current Status

✅ GM Toolkit: Functional, modular, and actively expanding

✅ Game Demo: Playable with melee combat

✅ Data Layer: JSON + SQLite hybrid in good shape

🟨 Next focus: Complete character generation system

🟨 Next focus: Extend combat with stamina, conditions, armor, and ranged logic