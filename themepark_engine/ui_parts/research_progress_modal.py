"""
Research Progress Modal - Affichage des upgrades et progrès par catégorie
"""

import pygame
from typing import Optional


class ResearchProgressModal:
    """Modal pour afficher le progrès de recherche par catégorie"""

    CATEGORY_NAMES = {
        "visitors": ("Visiteurs", "1F465.png"),  # Two persons
        "attractions": ("Attractions", "rides/1F3A2.png"),  # Roller coaster
        "shops": ("Shops", "shops/1F381.png"),  # Gift
        "employees": ("Employés", "1F454.png"),  # Necktie
        "decorations": ("Décorations", "1F333.png"),  # Tree
        "infrastructure": ("Infrastructure", "1F3D7.png")  # Construction
    }

    def __init__(self):
        self.visible = False
        self.current_category = "visitors"  # Catégorie actuellement affichée
        self.scroll_offset = 0  # Pour scroll vertical
        self.max_scroll = 0

        # UI Rects
        self.category_tab_rects = {}
        self.close_button_rect = None
        self.scroll_up_rect = None
        self.scroll_down_rect = None

        # Load category icons (20x20 for tabs)
        self.category_icons = {}
        self._load_category_icons()

        # Load status icons for upgrades (20x20)
        self.status_icons = {}
        self._load_status_icons()

    def _load_category_icons(self):
        """Load OpenMoji sprites for categories"""
        from .. import assets
        icon_size = (20, 20)

        for category, (name, sprite_path) in self.CATEGORY_NAMES.items():
            try:
                sprite = assets.load_image(sprite_path)
                scaled = pygame.transform.smoothscale(sprite, icon_size)
                self.category_icons[category] = scaled
            except:
                # Fallback to colored rectangle
                fallback = pygame.Surface(icon_size, pygame.SRCALPHA)
                fallback.fill((100, 100, 100))
                self.category_icons[category] = fallback

    def _load_status_icons(self):
        """Load OpenMoji sprites for status icons"""
        from pathlib import Path
        assets_path = Path(__file__).parent.parent.parent / "assets" / "openmoji"
        icon_size = (20, 20)

        status_sprites = {
            'unlocked': '2705.png',  # ✅ Checkmark
            'ready': '1F504.png',    # 🔄 Reload/rotation
            'locked': '1F512.png'    # 🔒 Lock
        }

        for status, sprite_file in status_sprites.items():
            sprite_path = assets_path / sprite_file
            if sprite_path.exists():
                icon = pygame.image.load(str(sprite_path))
                self.status_icons[status] = pygame.transform.scale(icon, icon_size)
            else:
                print(f"Warning: Status icon not found: {sprite_path}")

    def show(self, category: str = "visitors"):
        """Affiche le modal avec une catégorie sélectionnée"""
        self.visible = True
        self.current_category = category
        self.scroll_offset = 0

    def hide(self):
        """Cache le modal"""
        self.visible = False

    def toggle(self):
        """Toggle la visibilité du modal"""
        self.visible = not self.visible

    def handle_event(self, event: pygame.event.Event, research_bureau) -> bool:
        """
        Gère les événements pour le modal

        Returns:
            True si l'événement a été géré
        """
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos

            # Category tabs
            for category, rect in self.category_tab_rects.items():
                if rect.collidepoint(mouse_x, mouse_y):
                    self.current_category = category
                    self.scroll_offset = 0
                    return True

            # Close buttons (X at top or Fermer at bottom)
            if self.close_button_rect and self.close_button_rect.collidepoint(mouse_x, mouse_y):
                self.hide()
                return True
            if hasattr(self, 'close_bottom_button_rect') and self.close_bottom_button_rect.collidepoint(mouse_x, mouse_y):
                self.hide()
                return True

            # Scroll buttons
            if self.scroll_up_rect and self.scroll_up_rect.collidepoint(mouse_x, mouse_y):
                self.scroll_offset = max(0, self.scroll_offset - 50)
                return True

            if self.scroll_down_rect and self.scroll_down_rect.collidepoint(mouse_x, mouse_y):
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 50)
                return True

        elif event.type == pygame.MOUSEWHEEL:
            if self.visible:
                # Scroll avec la molette
                self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset - event.y * 30))
                return True

        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, research_bureau):
        """Dessine le modal de progrès de recherche"""
        if not self.visible:
            return

        screen_w, screen_h = screen.get_size()

        # Modal dimensions (increased size)
        modal_w = 750
        modal_h = 680
        modal_x = (screen_w - modal_w) // 2
        modal_y = (screen_h - modal_h) // 2

        # Fond semi-transparent
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))

        # Modal background
        modal_bg = pygame.Surface((modal_w, modal_h))
        modal_bg.fill((40, 40, 50))
        pygame.draw.rect(modal_bg, (200, 200, 200), (0, 0, modal_w, modal_h), 2)
        screen.blit(modal_bg, (modal_x, modal_y))

        y_offset = modal_y + 20

        # Title
        title_font = pygame.font.Font(None, 40)
        title = title_font.render("PROGRÈS DE RECHERCHE", True, (255, 255, 255))
        screen.blit(title, (modal_x + (modal_w - title.get_width()) // 2, y_offset))

        # Close button X (top right)
        close_x = modal_x + modal_w - 35
        close_y = modal_y + 10
        self.close_button_rect = pygame.Rect(close_x, close_y, 25, 25)
        pygame.draw.rect(screen, (150, 50, 50), self.close_button_rect)
        pygame.draw.rect(screen, (200, 100, 100), self.close_button_rect, 2)
        close_text = font.render("X", True, (255, 255, 255))
        screen.blit(close_text, (close_x + 7, close_y + 3))

        y_offset += 50

        # Category tabs
        tab_width = 100
        tab_height = 35
        tab_x = modal_x + 20
        self.category_tab_rects = {}

        for i, category in enumerate(research_bureau.CATEGORIES):
            cat_name, _ = self.CATEGORY_NAMES.get(category, (category, ""))
            is_active = (category == self.current_category)

            tab_rect = pygame.Rect(tab_x + i * (tab_width + 5), y_offset, tab_width, tab_height)
            self.category_tab_rects[category] = tab_rect

            # Tab background
            tab_color = (60, 120, 180) if is_active else (60, 60, 70)
            pygame.draw.rect(screen, tab_color, tab_rect)
            pygame.draw.rect(screen, (200, 200, 200), tab_rect, 1)

            # Tab icon (centered)
            if category in self.category_icons:
                icon = self.category_icons[category]
                icon_x = tab_rect.x + (tab_width - 20) // 2
                icon_y = tab_rect.y + 8
                screen.blit(icon, (icon_x, icon_y))

        y_offset += 50

        # Category info
        cat_data = research_bureau.get_category_progress(self.current_category)
        cat_name, _ = self.CATEGORY_NAMES.get(self.current_category,
                                               (self.current_category, ""))

        # Points accumulés avec limite dynamique
        current_points = cat_data.get('points', 0)
        points_cap = cat_data.get('points_cap', 1000)
        daily_pts = cat_data.get('daily_points', 0)

        # Afficher points/cap
        points_text = f"Points accumulés : {current_points:.0f} / {points_cap} pts"
        if daily_pts > 0:
            points_text += f"  (+{daily_pts:.1f}/jour)"

        # Couleur selon si limite atteinte
        if current_points >= points_cap:
            points_color = (255, 150, 50)  # Orange si limite atteinte
            points_text += "  ⚠️ LIMITE ATTEINTE"
        else:
            points_color = (100, 255, 100)  # Vert normal

        points_render = font.render(points_text, True, points_color)
        screen.blit(points_render, (modal_x + 30, y_offset))
        y_offset += 35

        # Separator
        pygame.draw.line(screen, (100, 100, 100),
                        (modal_x + 20, y_offset),
                        (modal_x + modal_w - 20, y_offset), 2)
        y_offset += 15

        # Upgrades list (scrollable area)
        scroll_area_y = y_offset
        scroll_area_h = modal_h - (y_offset - modal_y) - 60  # Space for close button

        # Create a subsurface for scrolling
        clip_rect = pygame.Rect(modal_x + 20, scroll_area_y, modal_w - 40, scroll_area_h)

        upgrades = cat_data.get('upgrades', [])
        content_y = scroll_area_y - self.scroll_offset

        # Calculate max scroll
        total_content_height = len(upgrades) * 90
        self.max_scroll = max(0, total_content_height - scroll_area_h)

        # Draw upgrades
        for upgrade in upgrades:
            # Skip if outside visible area
            if content_y + 85 < scroll_area_y or content_y > scroll_area_y + scroll_area_h:
                content_y += 90
                continue

            # Upgrade box
            upgrade_rect = pygame.Rect(modal_x + 30, content_y, modal_w - 60, 80)

            # Background color based on status
            if upgrade.unlocked:
                bg_color = (50, 100, 50)  # Green for unlocked
                border_color = (100, 200, 100)
                status_key = 'unlocked'
            else:
                # Check if can unlock
                can_unlock = upgrade.can_unlock(
                    research_bureau.unlocked_ids,
                    cat_data.get('points', 0)
                )
                if can_unlock:
                    bg_color = (80, 80, 120)  # Blue for ready
                    border_color = (120, 120, 200)
                    status_key = 'ready'
                else:
                    bg_color = (60, 60, 70)  # Gray for locked
                    border_color = (100, 100, 110)
                    status_key = 'locked'

            pygame.draw.rect(screen, bg_color, upgrade_rect)
            pygame.draw.rect(screen, border_color, upgrade_rect, 2)

            # Status icon
            status_icon = self.status_icons.get(status_key)
            if status_icon:
                screen.blit(status_icon, (upgrade_rect.x + 10, upgrade_rect.y + 10))

            # Name
            name_render = font.render(upgrade.name, True, (255, 255, 255))
            screen.blit(name_render, (upgrade_rect.x + 40, upgrade_rect.y + 10))

            # Cost
            cost_text = f"{upgrade.cost} pts"
            cost_render = font.render(cost_text, True, (255, 255, 100))
            screen.blit(cost_render, (upgrade_rect.x + 40, upgrade_rect.y + 30))

            # Description
            desc_render = font.render(upgrade.description, True, (180, 180, 180))
            screen.blit(desc_render, (upgrade_rect.x + 40, upgrade_rect.y + 50))

            # Progress bar if locked and has enough points
            if not upgrade.unlocked:
                current_points = cat_data.get('points', 0)
                if current_points > 0:
                    progress = min(1.0, current_points / upgrade.cost)
                    bar_width = 150
                    bar_height = 8
                    bar_x = upgrade_rect.right - bar_width - 15
                    bar_y = upgrade_rect.y + 15

                    # Background
                    bar_bg_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
                    pygame.draw.rect(screen, (40, 40, 50), bar_bg_rect)
                    pygame.draw.rect(screen, (100, 100, 110), bar_bg_rect, 1)

                    # Fill
                    fill_width = int(bar_width * progress)
                    if fill_width > 0:
                        fill_rect = pygame.Rect(bar_x, bar_y, fill_width, bar_height)
                        pygame.draw.rect(screen, (100, 180, 255), fill_rect)

                    # Percentage
                    pct_text = f"{progress*100:.0f}%"
                    pct_render = font.render(pct_text, True, (200, 200, 200))
                    screen.blit(pct_render, (bar_x + bar_width + 5, bar_y - 2))

            # Prerequisites (if locked)
            if not upgrade.unlocked and upgrade.prerequisites:
                prereq_text = "Pré-requis : " + ", ".join(upgrade.prerequisites)
                prereq_render = font.render(prereq_text, True, (255, 150, 150))
                # Check if prerequisites met
                all_met = all(pid in research_bureau.unlocked_ids
                             for pid in upgrade.prerequisites)
                if all_met:
                    prereq_render = font.render("Pré-requis : ✅", True, (100, 255, 100))
                screen.blit(prereq_render, (upgrade_rect.x + 40, upgrade_rect.y + 65))

            content_y += 90

        # Scroll indicators
        if self.max_scroll > 0:
            # Up arrow
            if self.scroll_offset > 0:
                self.scroll_up_rect = pygame.Rect(modal_x + modal_w - 40, scroll_area_y + 10, 30, 30)
                pygame.draw.rect(screen, (100, 100, 120), self.scroll_up_rect)
                pygame.draw.rect(screen, (200, 200, 200), self.scroll_up_rect, 1)
                up_text = font.render("▲", True, (255, 255, 255))
                screen.blit(up_text, (self.scroll_up_rect.x + 8, self.scroll_up_rect.y + 5))

            # Down arrow
            if self.scroll_offset < self.max_scroll:
                self.scroll_down_rect = pygame.Rect(modal_x + modal_w - 40,
                                                     scroll_area_y + scroll_area_h - 40, 30, 30)
                pygame.draw.rect(screen, (100, 100, 120), self.scroll_down_rect)
                pygame.draw.rect(screen, (200, 200, 200), self.scroll_down_rect, 1)
                down_text = font.render("▼", True, (255, 255, 255))
                screen.blit(down_text, (self.scroll_down_rect.x + 8, self.scroll_down_rect.y + 5))

        # Close button (bottom)
        close_bottom_y = modal_y + modal_h - 50
        close_bottom_rect = pygame.Rect(modal_x + (modal_w - 200) // 2, close_bottom_y, 200, 35)
        pygame.draw.rect(screen, (100, 100, 120), close_bottom_rect)
        pygame.draw.rect(screen, (150, 150, 170), close_bottom_rect, 2)
        close_btn_text = font.render("Fermer", True, (255, 255, 255))
        screen.blit(close_btn_text,
                   (close_bottom_rect.x + 70, close_bottom_rect.y + 8))
        # Also register this rect for click handling
        if not hasattr(self, 'close_bottom_button_rect'):
            self.close_bottom_button_rect = close_bottom_rect
        else:
            self.close_bottom_button_rect = close_bottom_rect
