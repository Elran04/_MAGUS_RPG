"""
Unit information popup display.
Shows detailed unit stats when right-clicking on a unit.
"""
import pygame
from typing import Optional, Dict
from config import WIDTH, HEIGHT, UI_BORDER, UI_TEXT, UI_ACTIVE, UI_INACTIVE
from systems.weapon_wielding import get_wielding_info


class UnitInfoPopup:
    """Popup window for displaying detailed unit information."""
    
    def __init__(self):
        self.visible = False
        self.unit = None
        self.popup_rect = None
        self.cached_wield_info = None  # Cache to avoid recalculating every frame
        self.title_font = pygame.font.SysFont(None, 32, bold=True)
        self.header_font = pygame.font.SysFont(None, 28, bold=True)
        self.text_font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 20)
        
    def show(self, unit) -> None:
        """Show popup for the given unit."""
        self.visible = True
        self.unit = unit
        # Cache wielding info when showing popup
        if unit.weapon and unit.weapon.get('wield_mode') == 'Változó':
            self.cached_wield_info = get_wielding_info(unit, unit.weapon)
        else:
            self.cached_wield_info = None
        
    def hide(self) -> None:
        """Hide the popup."""
        self.visible = False
        self.unit = None
        self.cached_wield_info = None
        
    def toggle(self, unit) -> None:
        """Toggle popup visibility for the given unit."""
        if self.visible and self.unit == unit:
            self.hide()
        else:
            self.show(unit)
            
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the popup on screen."""
        if not self.visible or not self.unit:
            return
        
        # Popup dimensions
        popup_width = 400
        popup_height = 550
        popup_x = (WIDTH - popup_width) // 2
        popup_y = (HEIGHT - popup_height) // 2
        
        self.popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        
        # Semi-transparent background overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Popup background
        pygame.draw.rect(screen, (40, 40, 50), self.popup_rect, border_radius=10)
        pygame.draw.rect(screen, UI_BORDER, self.popup_rect, width=3, border_radius=10)
        
        # Draw content
        y_offset = popup_y + 15
        x_left = popup_x + 20
        x_right = popup_x + popup_width - 20
        
        # Title - Unit Name
        title_text = self.title_font.render(self.unit.name, True, (255, 215, 0))
        screen.blit(title_text, (x_left, y_offset))
        y_offset += 40
        
        # Separator line
        pygame.draw.line(screen, UI_BORDER, (x_left, y_offset), (x_right, y_offset), 2)
        y_offset += 15
        
        # Health/Fatigue Points
        y_offset = self._draw_health_section(screen, x_left, y_offset)
        y_offset += 10
        
        # Combat Stats
        y_offset = self._draw_combat_stats(screen, x_left, y_offset)
        y_offset += 10
        
        # Attributes (Tulajdonságok)
        y_offset = self._draw_attributes(screen, x_left, y_offset)
        y_offset += 10
        
        # Equipped Weapon
        y_offset = self._draw_weapon_info(screen, x_left, x_right, y_offset)
        y_offset += 10
        
        # Conditions (placeholder for future)
        y_offset = self._draw_conditions(screen, x_left, y_offset)
        
        # Close instruction
        close_text = self.small_font.render("(Click outside window to close)", True, (150, 150, 150))
        screen.blit(close_text, (popup_x + popup_width - 230, popup_y + popup_height - 25))
        
    def _draw_health_section(self, screen: pygame.Surface, x: int, y: int) -> int:
        """Draw FP/ÉP section. Returns new y offset."""
        # Header
        header = self.header_font.render("Health", True, (100, 200, 255))
        screen.blit(header, (x, y))
        y += 30
        
        # FP (Fatigue Points)
        fp_current = self.unit.current_fp
        fp_max = self.unit.FP
        fp_text = self.text_font.render(f"FP: {fp_current} / {fp_max}", True, UI_TEXT)
        screen.blit(fp_text, (x + 10, y))
        
        # FP bar
        bar_width = 200
        bar_height = 20
        bar_x = x + 150
        bar_y = y + 2
        
        # Background bar
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height), border_radius=5)
        
        # Fill bar (blue for FP)
        if fp_max > 0:
            fill_width = int((fp_current / fp_max) * bar_width)
            pygame.draw.rect(screen, (70, 130, 220), (bar_x, bar_y, fill_width, bar_height), border_radius=5)
        
        pygame.draw.rect(screen, UI_BORDER, (bar_x, bar_y, bar_width, bar_height), width=2, border_radius=5)
        y += 30
        
        # ÉP (Health Points)
        ep_current = self.unit.current_ep
        ep_max = self.unit.EP
        ep_text = self.text_font.render(f"ÉP: {ep_current} / {ep_max}", True, UI_TEXT)
        screen.blit(ep_text, (x + 10, y))
        
        # ÉP bar
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y + 28, bar_width, bar_height), border_radius=5)
        
        # Fill bar (red for ÉP)
        if ep_max > 0:
            fill_width = int((ep_current / ep_max) * bar_width)
            pygame.draw.rect(screen, (220, 70, 70), (bar_x, bar_y + 28, fill_width, bar_height), border_radius=5)
        
        pygame.draw.rect(screen, UI_BORDER, (bar_x, bar_y + 28, bar_width, bar_height), width=2, border_radius=5)
        y += 35
        
        return y
        
    def _draw_combat_stats(self, screen: pygame.Surface, x: int, y: int) -> int:
        """Draw combat statistics with breakdown. Returns new y offset."""
        # Header
        header = self.header_font.render("Combat Stats", True, (255, 100, 100))
        screen.blit(header, (x, y))
        y += 30
        
        # Import wielding info here to avoid circular dependency
        from systems.weapon_wielding import get_wielding_info
        
        # Get wielding bonuses if applicable
        wield_bonuses = {'KE': 0, 'TE': 0, 'VE': 0}
        if self.unit.weapon and self.unit.weapon.get('wield_mode') == 'Változó':
            wield_info = self.cached_wield_info if self.cached_wield_info else get_wielding_info(self.unit)
            wield_bonuses = wield_info['bonuses']
        
        # Get combat stats with breakdown
        combat = self.unit.combat
        weapon = self.unit.weapon
        
        stats = [
            ("KÉ", combat.get("KÉ", 0), weapon.get("KE", 0), wield_bonuses.get('KE', 0)),
            ("TÉ", combat.get("TÉ", 0), weapon.get("TE", 0), wield_bonuses.get('TE', 0)),
            ("VÉ", combat.get("VÉ", 0), weapon.get("VE", 0), wield_bonuses.get('VE', 0)),
            ("CÉ", combat.get("CÉ", 0), weapon.get("CE", 0), 0),
        ]
        
        # Draw each stat with breakdown
        for i, (stat_name, base, weapon_bonus, wield_bonus) in enumerate(stats):
            stat_y = y + (i * 28)
            
            # Calculate total
            total = base + weapon_bonus + wield_bonus
            
            # Draw stat name and total
            stat_text = self.text_font.render(f"{stat_name}: {total}", True, (200, 200, 200))
            screen.blit(stat_text, (x + 10, stat_y))
            
            # Draw breakdown on the right side
            breakdown_x = x + 130
            parts = []
            
            # Base (white)
            if base != 0:
                parts.append((f"{base}", (200, 200, 200)))
            
            # Weapon bonus (green)
            if weapon_bonus != 0:
                parts.append((f"+{weapon_bonus}", (100, 255, 100)))
            
            # Wielding bonus (cyan/light blue)
            if wield_bonus != 0:
                parts.append((f"+{wield_bonus}", (100, 200, 255)))
            
            # Draw breakdown
            offset_x = 0
            for part_text, color in parts:
                part_surface = self.small_font.render(part_text, True, color)
                screen.blit(part_surface, (breakdown_x + offset_x, stat_y + 2))
                offset_x += part_surface.get_width() + 5
        
        y += 120
        return y
        
    def _draw_attributes(self, screen: pygame.Surface, x: int, y: int) -> int:
        """Draw character attributes (Tulajdonságok). Returns new y offset."""
        # Header
        header = self.header_font.render("Attributes", True, (100, 255, 100))
        screen.blit(header, (x, y))
        y += 30
        
        if not self.unit.character_data:
            no_data = self.text_font.render("No data available", True, (150, 150, 150))
            screen.blit(no_data, (x + 10, y))
            return y + 30
        
        # Get attributes
        tulajdonsagok = self.unit.character_data.get('Tulajdonságok', {})
        
        # Common attributes to display
        attr_names = ['Erő', 'Ügyesség', 'Gyorsaság', 'Állóképesség', 'Egészség', 'Szépség', 'Intelligencia', 'Akaraterő', 'Asztrál']
        
        displayed = 0
        for attr_name in attr_names:
            if attr_name in tulajdonsagok:
                attr_data = tulajdonsagok[attr_name]
                if isinstance(attr_data, dict):
                    value = attr_data.get('value', 0)
                else:
                    value = attr_data
                
                # Draw in 3 columns
                col = displayed % 3
                row = displayed // 3
                attr_x = x + 10 + (col * 120)
                attr_y = y + (row * 22)
                
                # Abbreviate long names
                display_name = attr_name[:3] + "." if len(attr_name) > 6 else attr_name
                attr_text = self.small_font.render(f"{display_name}: {value}", True, UI_TEXT)
                screen.blit(attr_text, (attr_x, attr_y))
                
                displayed += 1
        
        if displayed == 0:
            no_attrs = self.text_font.render("No attributes", True, (150, 150, 150))
            screen.blit(no_attrs, (x + 10, y))
            y += 30
        else:
            rows = (displayed + 2) // 3
            y += rows * 22 + 10
        
        return y
        
    def _draw_weapon_info(self, screen: pygame.Surface, x_left: int, x_right: int, y: int) -> int:
        """Draw equipped weapon information. Returns new y offset."""
        # Header
        header = self.header_font.render("Equipped Weapon", True, (255, 200, 100))
        screen.blit(header, (x_left, y))
        y += 30
        
        if not self.unit.weapon:
            no_weapon = self.text_font.render("No weapon equipped", True, (150, 150, 150))
            screen.blit(no_weapon, (x_left + 10, y))
            return y + 30
        
        weapon = self.unit.weapon
        
        # Weapon name
        weapon_name = weapon.get('name', 'Unknown Weapon')
        name_text = self.text_font.render(weapon_name, True, (255, 215, 0))
        screen.blit(name_text, (x_left + 10, y))
        y += 25
        
        # Damage range
        damage_min = weapon.get('damage_min', 1)
        damage_max = weapon.get('damage_max', 6)
        damage_text = self.small_font.render(f"Damage: {damage_min}-{damage_max}", True, UI_TEXT)
        screen.blit(damage_text, (x_left + 20, y))
        y += 22
        
        # Size category
        size_cat = weapon.get('size_category', 1)
        size_text = self.small_font.render(f"Size Category: {size_cat}", True, UI_TEXT)
        screen.blit(size_text, (x_left + 20, y))
        y += 22
        
        # Wield mode
        wield_mode = weapon.get('wield_mode', '1-handed')
        
        if wield_mode == 'Változó':
            # Variable weapon - use cached info
            wield_info = self.cached_wield_info
            if wield_info:
                current_mode = wield_info['mode']
                can_choose = wield_info['can_choose']
                bonuses = wield_info['bonuses']
                
                mode_color = (100, 255, 100) if can_choose else (255, 150, 100)
                mode_text = self.small_font.render(f"Wielding: {current_mode}", True, mode_color)
                screen.blit(mode_text, (x_left + 20, y))
                y += 22
                
                if can_choose:
                    choice_text = self.small_font.render("(Can switch modes)", True, (150, 200, 150))
                    screen.blit(choice_text, (x_left + 30, y))
                    y += 20
                else:
                    forced_text = self.small_font.render("(Forced - need more stats)", True, (200, 150, 100))
                    screen.blit(forced_text, (x_left + 30, y))
                    y += 20
                
                # Show bonuses if wielding 2-handed with choice
                if current_mode == "2-handed" and can_choose and any(bonuses.values()):
                    bonus_parts = []
                    if bonuses['KE'] > 0:
                        bonus_parts.append(f"+{bonuses['KE']} KÉ")
                    if bonuses['TE'] > 0:
                        bonus_parts.append(f"+{bonuses['TE']} TÉ")
                    if bonuses['VE'] > 0:
                        bonus_parts.append(f"+{bonuses['VE']} VÉ")
                    
                    bonus_str = ", ".join(bonus_parts)
                    bonus_text = self.small_font.render(f"Bonuses: {bonus_str}", True, (100, 255, 255))
                    screen.blit(bonus_text, (x_left + 30, y))
                    y += 22
        else:
            # Fixed wield mode
            wield_text = self.small_font.render(f"Wield Mode: {wield_mode}", True, UI_TEXT)
            screen.blit(wield_text, (x_left + 20, y))
            y += 22
        
        return y + 5
        
    def _draw_conditions(self, screen: pygame.Surface, x: int, y: int) -> int:
        """Draw status conditions (placeholder). Returns new y offset."""
        # Header
        header = self.header_font.render("Conditions", True, (200, 100, 255))
        screen.blit(header, (x, y))
        y += 30
        
        # Placeholder for future conditions
        # TODO: Add condition system (stunned, bleeding, poisoned, etc.)
        no_conditions = self.text_font.render("None", True, (150, 150, 150))
        screen.blit(no_conditions, (x + 10, y))
        y += 25
        
        return y
    
    def is_click_outside(self, mx: int, my: int) -> bool:
        """Check if mouse click is outside the popup area."""
        if not self.visible or not self.popup_rect:
            return False
        return not self.popup_rect.collidepoint(mx, my)
