"""Simple hex map scenario editor for MAGUS Pygame.

Controls:
- Left click: place based on active tool
- Keys:
  - W: Select Warrior placement tool
  - G: Select Goblin placement tool
  - O: Toggle obstacle at clicked hex (when O tool active)
  - B: Cycle background (currently just grass)
  - S: Save to data/scenarios/custom.json
  - L: Load from data/scenarios/custom.json if exists
  - ESC: Exit
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import pygame

# Ensure we can import sibling packages when running as a script
PARENT_DIR = Path(__file__).resolve().parent.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

from config import (
    WIDTH,
    HEIGHT,
    WARRIOR_SPRITE,
    GOBLIN_SPRITE,
    get_scenario_json_path,
    get_character_sprite_path,
    GRASS_BACKGROUND,
)
from rendering.sprite_manager import load_and_mask_sprite
from systems.hex_grid import draw_grid, pixel_to_hex, get_grid_bounds


class Tool:
    WARRIOR = "warrior"
    GOBLIN = "goblin"
    OBSTACLE = "obstacle"


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("MAGUS Scenario Editor")
    clock = pygame.time.Clock()

    # Resources
    warrior_sprite = load_and_mask_sprite(str(WARRIOR_SPRITE))
    goblin_sprite = load_and_mask_sprite(str(GOBLIN_SPRITE))

    background = None
    try:
        img = pygame.image.load(str(GRASS_BACKGROUND)).convert()
        background = pygame.transform.smoothscale(img, (WIDTH, HEIGHT))
    except Exception:
        background = None

    # State
    MIN_Q, MAX_Q, MIN_R, MAX_R = get_grid_bounds()
    grid_bounds = (MIN_Q, MAX_Q, MIN_R, MAX_R)
    warrior_pos = (3, 3)
    goblin_pos = (6, 3)
    obstacles: set[tuple[int, int]] = set()
    active_tool = Tool.WARRIOR

    font = pygame.font.SysFont(None, 20)

    def draw_ui_overlay():
        info_lines = [
            "Scenario Editor",
            f"Tool: {active_tool.upper()} | Left click to place",
            "W: Warrior, G: Goblin, O: Obstacle, S: Save, L: Load, ESC: Exit",
            "Saves to data/scenarios/custom.json",
        ]
        y = 5
        for line in info_lines:
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (10, y))
            y += 18

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
                if event.key == pygame.K_w:
                    active_tool = Tool.WARRIOR
                elif event.key == pygame.K_g:
                    active_tool = Tool.GOBLIN
                elif event.key == pygame.K_o:
                    active_tool = Tool.OBSTACLE
                elif event.key == pygame.K_s:
                    save_path = get_scenario_json_path("custom.json")
                    save_scenario(save_path, warrior_pos, goblin_pos, obstacles)
                elif event.key == pygame.K_l:
                    load_path = get_scenario_json_path("custom.json")
                    if Path(load_path).exists():
                        w, g, obs = load_scenario_state(load_path)
                        if w:
                            warrior_pos = w
                        if g:
                            goblin_pos = g
                        obstacles = obs
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                q, r = pixel_to_hex(mx, my)
                if active_tool == Tool.WARRIOR:
                    warrior_pos = (q, r)
                elif active_tool == Tool.GOBLIN:
                    goblin_pos = (q, r)
                elif active_tool == Tool.OBSTACLE:
                    if (q, r) in obstacles:
                        obstacles.remove((q, r))
                    else:
                        obstacles.add((q, r))

        # Render
        if background is not None:
            screen.blit(background, (0, 0))
        else:
            screen.fill((20, 30, 20))

        sprite_positions = {
            warrior_pos: warrior_sprite,
            goblin_pos: goblin_sprite,
        }
        draw_grid(
            screen,
            MIN_Q,
            MAX_Q,
            MIN_R,
            MAX_R,
            sprite_positions=sprite_positions,
            highlight_hex=pixel_to_hex(*pygame.mouse.get_pos()),
        )

        draw_ui_overlay()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def save_scenario(path: Path | str, warrior_pos, goblin_pos, obstacles: set[tuple[int, int]]):
    data = {
        "name": "custom",
        "background": str(GRASS_BACKGROUND),
        "units": [
            {"character_file": "Teszt.json", "sprite": "warrior.png", "start_q": warrior_pos[0], "start_r": warrior_pos[1], "facing": 0},
            {"character_file": "Teszt_Goblin.json", "sprite": "goblin.png", "start_q": goblin_pos[0], "start_r": goblin_pos[1], "facing": 3}
        ],
        "obstacles": [list(x) for x in sorted(obstacles)],
        "metadata": {"created_with": "scenario_editor", "version": 1}
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved scenario to {path}")


def load_scenario_state(path: Path | str):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # Extract state
    units = data.get("units", [])
    w = None
    g = None
    if len(units) > 0:
        u0 = units[0]
        w = (int(u0.get("start_q", 3)), int(u0.get("start_r", 3)))
    if len(units) > 1:
        u1 = units[1]
        g = (int(u1.get("start_q", 6)), int(u1.get("start_r", 3)))
    obstacles = set(tuple(x) for x in data.get("obstacles", []))
    return w, g, obstacles


if __name__ == "__main__":
    main()
