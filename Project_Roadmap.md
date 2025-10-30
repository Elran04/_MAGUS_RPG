# 🗺️ MAGUS RPG System — Development Roadmap

## 🎯 Overview
This roadmap outlines the current status and future development steps for the **MAGUS RPG System**, which consists of two main modules:
- **GM Toolkit (PySide6-based)** – used for editing and managing game data.  
- **Game Demo (Pygame-based)** – a prototype environment for gameplay and combat testing.  

---


## 1. 🧩 Core Structure
- ✅ Maintain two separate main modules (`main.py` for GM Toolkit and Game Demo).
- ✅ Both run independently and share logic through common libraries.
- ✅ Modularization: split files exceeding ~400 lines into smaller submodules.

---


## 2. 💾 Data Management
- ✅ Each dataset (skills, classes, equipment, etc.) has its own `DataManager`.
- ✅ Consistent CRUD functionality across JSON and SQLite data sources.
- 🟨 Evaluate a unified storage system for runtime saves (e.g., SQLite instead of JSON). (Hybrid in use)

---


## 3. 🧙 GM Toolkit (PySide6)
**Current Features:**
- ✅ Skill Editor
- ✅ Class Editor
- ✅ Equipment Editor
- ✅ Character Creator

**Planned/Ongoing Improvements:**
- 🟨 Enhance UI/UX with better layout scaling, icons, and polished dark mode. (Dark mode and some scaling done)
- 🟨 Add validation and tooltips for input fields. (Validation present, tooltips partial)
- 🟥 Item Templates (not started)
- 🟥 Race Editor (not started)

---


## 4. ⚔️ Game Demo (Pygame)
**Current Features:**
- ✅ Two test characters loaded from JSON.
- ✅ Working melee combat mechanics.
- ✅ Functional hex grid and basic turn system.
- ✅ Initiative and charge mechanics.

**Next Steps:**
- 🟥 Add camera movement and dynamic map scaling.
- 🟥 Implement map loading from JSON or tile sets.
- 🟥 Add environmental elements (obstacles, height, interactive objects).
- 🟥 Expand combat to support ranged attacks and area effects.

---


## 5. 🧝 Character System
**Current:**
- ✅ Characters load from JSON with stats and equipment.
- ✅ Character creator wizard with class/spec selection from SQLite.

**Planned:**
- 🟨 Integrate skill/class data from SQLite dynamically. (Partial)
- 🟥 Add XP system, leveling, and stat growth.
- 🟥 Implement racial traits and unique abilities.
- 🟥 Support multiple characters, save/load, and switching.

---


## 6. ⚔️ Combat System
**Current:**
- ✅ Basic melee combat functional, tested with two characters.
- ✅ Initiative and turn queue.
- ✅ Armor layering system (armor_type + layer fields).

**Planned Enhancements:**
- 🟥 Enable multi-opponent and area-based targeting. (Not started)
- 🟥 Penetration logic and hit localization. (Not started)
- 🟥 Implement visual combat feedback and logs. (Not started)

---


## 7. 🧠 Game Logic & Progression
- 🟥 Develop scalable difficulty for AI opponents.
- 🟥 Introduce scripted events and encounter triggers.
- 🟥 Add simple AI logic (targeting, attack choice, retreat conditions).

---


## 8. ⚙️ Architecture & Constants
- ✅ Centralize all core settings in `config.py` (not `constants.py`).
- 🟨 Move repeated values (window size, grid size, UI scaling) into the config file. (Partial)
- 🟥 Add a `settings.json` or similar structure for user preferences.

---


## 9. 🔧 Version Control & Collaboration
- ✅ Git + GitHub in active use — continue structured commits.
- 🟨 Add or update `README.md` with usage and setup instructions. (Status unknown)
- 🟥 Start version tagging (e.g., `v0.1-alpha`, `v0.2-alpha`).
- 🟨 Optionally add lightweight contribution notes for scalability.

---


## 10. 🎨 Assets & Visuals
- ✅ Currently using free stock top-down sprites and tilesets.
- ✅ Maintain folder structure: `/assets/sprites/` (no maps/ui folders yet)
- 🟨 Plan gradual replacement with custom or commissioned assets.

---


## 11. 🧭 Major Milestones
1. **Character System Completion**
	- 🟨 Integrate dynamic SQLite data
	- 🟥 Add save/load support

2. **Expanded Combat Framework**
	- 🟥 Introduce ranged and AI-based combat

3. **Character Editor (PySide6)**
	- 🟨 Visual editor tied to class/skill databases (Character Creator exists)

4. **Playable Demo Scenario**
	- 🟥 Small map with scaling difficulty and progression

---


> **Status:**
> - ✅ GM Toolkit: Functional and modular
> - ✅ Game Demo: Playable prototype
> - ✅ Data Layer: JSON + SQLite hybrid (CRUD complete)
> - 🟨 Next focus: Finish character creation
> - 🟨 Next focus: Character integration & expanded combat

