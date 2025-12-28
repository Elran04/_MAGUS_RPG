# MAGUS RPG - Gamemaster Tools & Game Engine

M.A.G.U.S. szerepjáték rendszerhez készült Kalandmesteri eszköztár és játékmotor.

## 📋 Projekt Struktúra

### `Gamemaster_tools/`
PySide6 alapú desktop alkalmazás kalandmesterek számára:
- **Karakteralkotás**: Teljes körű karaktergenerátor wizard
- **Karakterbetöltés**: Mentett karakterek megtekintése és törlése
- **Képzettség szerkesztő**: Képzettségek kezelése és szerkesztése
- **Felszerelés szerkesztő**: Fegyverek, páncélok, általános felszerelés kezelése
- **Kaszt szerkesztő**: Karakterosztályok szerkesztése és kezelése

### `MAGUS_pygame/`
Pygame alapú hexagonális rácsú körökre osztott harcrendszer:
- Taktikai harc hexagon grid-en
- Kezdeményezés rendszer
- Támadás, mozgás, roham akciók
- Unit info popup-ok
- Szenárió rendszer (JSON alapú pályák és induló pozíciók)
- Jelenleg a szenáriók JSON fájlok szerkesztésével készülnek; külön editor nincs (archivált)
 
Megjegyzés: A Pygame modul jelenleg demo/prototípus a játékmenet mechanikákhoz; a végleges játék valószínűleg Godot-ban készül.

## 🚀 Telepítés és Használat

### Követelmények
- Python 3.13.x
- Poetry (függőségkezelés)

### Projekt Beállítása

```powershell
# 1. Repository klónozása
git clone <repository-url>
cd _MAGUS_RPG

# 2. Poetry virtuális környezet létrehozása és függőségek telepítése
poetry install

# 3. Virtuális környezet aktiválása
poetry shell
```

### Futtatás

**Gamemaster Tools indítása:**
```powershell
poetry run python Gamemaster_tools/main.py
```

**Pygame játék indítása:**
```powershell
poetry run python MAGUS_pygame/main.py
```

 Alapértelmezett szenárió: `MAGUS_pygame/data/scenarios/default.json`.
 Saját szenáriók a `MAGUS_pygame/data/scenarios/` mappában.

## 🛠️ Fejlesztői Eszközök

### Code Quality Tools

**Black (Code Formatter):**
```powershell
# Teljes projekt formázása
poetry run black .

# Csak ellenőrzés (változtatás nélkül)
poetry run black --check .
```

**Ruff (Linter):**
```powershell
# Lint ellenőrzés
poetry run ruff check .

# Automatikus javítások alkalmazása
poetry run ruff check --fix .
```

**MyPy (Type Checker):**
```powershell
# Type checking futtatása
poetry run mypy Gamemaster_tools/
poetry run mypy MAGUS_pygame/
```

### Konfigurációk
Minden tool konfigurációja a `pyproject.toml` fájlban található.

## 📁 Adatkezelés

- **SQLite**: Referencia adatok tárolása (képzettségek, felszerelések, osztályok)
- **JSON**: Karakterek és runtime adatok mentése
- **Scenarios (JSON)**: Harci pályák (`MAGUS_pygame/data/scenarios/`)

## 📝 Log Fájlok

A log fájlok automatikusan generálódnak a `logs/` mappában:
- `logs/magus_YYYYMMDD.log` - Gamemaster Tools logok
- `logs/pygame_YYYYMMDD.log` - Pygame játék logok

## 🎨 UI/UX

- **Dark Mode**: Automatikus dark mode support (egyedi implementáció)
- **PySide6**: Modern Qt alapú felület
- **Responsive**: Átméretezhető és skálázható UI elemek

## 📦 Függőségek

### Fő Függőségek
- `PySide6` ^6.10.0 - GUI framework
- `pygame` ^2.6.1 - Játékmotor

### Dev Függőségek
- `black` ^25.9.0 - Code formatter
- `ruff` ^0.14.3 - Linter
- `mypy` ^1.18.2 - Type checker

## 🔄 Verziókezelés

A projekt Git verziókezelést használ. A főbb változások és tervek a `docs/PROJECT_ROADMAP.md` fájlban találhatók.

## 👤 Szerző

**Elran04**

## 📄 Licenc

[Add meg a licensz típusát ha van]

---

**Megjegyzés**: Ez egy aktív fejlesztés alatt álló projekt.

## 📚 Dokumentáció

- Fejlesztői útmutató: `docs/DEVELOPER_GUIDE.md`
- Aktuális állapot: `docs/PROJECT_STATUS.md`
- Teljes dokumentáció index: `docs/README.md`
