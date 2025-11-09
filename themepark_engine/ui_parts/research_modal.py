"""
Research Bureau Modal - Gestion du budget et répartition R&D avec onglets
"""

import pygame
from typing import Tuple, Optional
from pathlib import Path
from ..debug import DebugConfig


class ResearchBureauModal:
    """Modal pour gérer le budget mensuel, la répartition par catégorie, et voir les progrès"""

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
        self.budget_input_active = False
        self.budget_input_text = ""
        self.current_tab = "budget"  # "budget" or "progress"
        self.current_progress_category = "visitors"  # For progress tab

        # Sliders pour l'allocation
        self.dragging_slider = None  # Nom de la catégorie en cours de drag
        self.slider_rects = {}  # category -> Rect

        # Buttons
        self.budget_minus_rect = None
        self.budget_plus_rect = None
        self.close_button_rect = None
        self.tab_rects = {}  # Tab buttons
        self.category_tab_rects = {}  # Category tabs for progress view

        # Progress tab state
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_up_rect = None
        self.scroll_down_rect = None
        self.upgrade_rects = {}  # upgrade_id -> Rect (for click detection)

        # Load category icons (24x24 for budget, 20x20 for progress)
        self.category_icons = {}
        self.category_icons_small = {}
        self._load_category_icons()

    def _load_category_icons(self):
        """Load OpenMoji sprites for categories"""
        from .. import assets
        icon_size_24 = (24, 24)
        icon_size_20 = (20, 20)

        for category, (name, sprite_path) in self.CATEGORY_NAMES.items():
            try:
                sprite = assets.load_image(sprite_path)
                scaled_24 = pygame.transform.smoothscale(sprite, icon_size_24)
                scaled_20 = pygame.transform.smoothscale(sprite, icon_size_20)
                self.category_icons[category] = scaled_24
                self.category_icons_small[category] = scaled_20
            except:
                # Fallback to colored rectangle
                fallback_24 = pygame.Surface(icon_size_24, pygame.SRCALPHA)
                fallback_24.fill((100, 100, 100))
                fallback_20 = pygame.Surface(icon_size_20, pygame.SRCALPHA)
                fallback_20.fill((100, 100, 100))
                self.category_icons[category] = fallback_24
                self.category_icons_small[category] = fallback_20

    def show(self, tab="budget"):
        """Affiche le modal avec un onglet spécifique"""
        self.visible = True
        self.current_tab = tab
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

            # Tab buttons
            for tab_name, rect in self.tab_rects.items():
                if rect.collidepoint(mouse_x, mouse_y):
                    self.current_tab = tab_name
                    self.scroll_offset = 0
                    return True

            # Close button (X in top right)
            if self.close_button_rect and self.close_button_rect.collidepoint(mouse_x, mouse_y):
                self.hide()
                return True

            # Budget tab controls
            if self.current_tab == "budget":
                # Budget buttons
                if self.budget_minus_rect and self.budget_minus_rect.collidepoint(mouse_x, mouse_y):
                    research_bureau.set_monthly_budget(research_bureau.monthly_budget - 500)
                    return True

                if self.budget_plus_rect and self.budget_plus_rect.collidepoint(mouse_x, mouse_y):
                    research_bureau.set_monthly_budget(research_bureau.monthly_budget + 500)
                    return True

                # Sliders
                for category, rect in self.slider_rects.items():
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.dragging_slider = category
                        return True

            # Progress tab controls
            elif self.current_tab == "progress":
                # Category tabs
                for category, rect in self.category_tab_rects.items():
                    if rect.collidepoint(mouse_x, mouse_y):
                        self.current_progress_category = category
                        self.scroll_offset = 0
                        return True

                # Upgrade clicks (for manual unlock)
                for upgrade_id, rect in self.upgrade_rects.items():
                    if rect.collidepoint(mouse_x, mouse_y):
                        # Find the upgrade object
                        upgrade = research_bureau.get_upgrade_by_id(upgrade_id)
                        if upgrade and not upgrade.unlocked:
                            cat_data = research_bureau.get_category_progress(self.current_progress_category)
                            # Check if can unlock
                            if upgrade.can_unlock(research_bureau.unlocked_ids, cat_data.get('points', 0)):
                                # Try to unlock
                                success, message = research_bureau.unlock_upgrade_manual(upgrade)
                                if success:
                                    DebugConfig.log('research', message)
                                return True

                # Scroll buttons
                if self.scroll_up_rect and self.scroll_up_rect.collidepoint(mouse_x, mouse_y):
                    self.scroll_offset = max(0, self.scroll_offset - 50)
                    return True

                if self.scroll_down_rect and self.scroll_down_rect.collidepoint(mouse_x, mouse_y):
                    self.scroll_offset = min(self.max_scroll, self.scroll_offset + 50)
                    return True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_slider = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_slider and self.current_tab == "budget":
                mouse_x, mouse_y = event.pos
                # Calculer la nouvelle allocation
                rect = self.slider_rects[self.dragging_slider]
                slider_width = 300
                # Position relative dans la barre
                relative_x = max(0, min(slider_width, mouse_x - rect.x))
                new_allocation = relative_x / slider_width

                # Vérifier si le nouveau total dépasse 100%
                current_allocation = research_bureau.categories[self.dragging_slider].allocation
                total_allocation = research_bureau.get_total_allocation()
                new_total = total_allocation - current_allocation + new_allocation

                # Empêcher d'augmenter si déjà au-dessus de 100%
                if new_total > 1.0 and new_allocation > current_allocation:
                    # Calculer l'allocation maximale permise
                    max_allowed = 1.0 - (total_allocation - current_allocation)
                    new_allocation = max(current_allocation, max_allowed)

                research_bureau.set_category_allocation(self.dragging_slider, new_allocation)
                return True

        elif event.type == pygame.MOUSEWHEEL:
            if self.visible and self.current_tab == "progress":
                # Scroll avec la molette
                self.scroll_offset = max(0, min(self.max_scroll, self.scroll_offset - event.y * 30))
                return True

        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font,
             research_bureau, current_day: int):
        """Dessine le modal Bureau de R&D avec onglets"""
        if not self.visible:
            return

        screen_w, screen_h = screen.get_size()

        # Modal dimensions
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
        title = title_font.render("BUREAU DE R&D", True, (255, 255, 255))
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

        # Tab buttons
        tab_width = 200
        tab_height = 35
        tab_x = modal_x + (modal_w - tab_width * 2 - 10) // 2

        self.tab_rects = {}
        tabs = [("budget", "Budget"), ("progress", "Progrès")]

        for i, (tab_id, tab_name) in enumerate(tabs):
            is_active = (self.current_tab == tab_id)
            tab_rect = pygame.Rect(tab_x + i * (tab_width + 10), y_offset, tab_width, tab_height)
            self.tab_rects[tab_id] = tab_rect

            # Tab background
            tab_color = (60, 120, 180) if is_active else (60, 60, 70)
            pygame.draw.rect(screen, tab_color, tab_rect)
            pygame.draw.rect(screen, (200, 200, 200), tab_rect, 1)

            # Tab text
            tab_text = font.render(tab_name, True, (255, 255, 255))
            text_rect = tab_text.get_rect(center=tab_rect.center)
            screen.blit(tab_text, text_rect)

        y_offset += 50

        # Separator
        pygame.draw.line(screen, (100, 100, 100),
                        (modal_x + 20, y_offset),
                        (modal_x + modal_w - 20, y_offset), 2)
        y_offset += 15

        # Draw content based on active tab
        if self.current_tab == "budget":
            self._draw_budget_tab(screen, font, research_bureau, current_day, modal_x, modal_y, modal_w, modal_h, y_offset)
        else:  # progress
            self._draw_progress_tab(screen, font, research_bureau, modal_x, modal_y, modal_w, modal_h, y_offset)

    def _draw_budget_tab(self, screen, font, research_bureau, current_day, modal_x, modal_y, modal_w, modal_h, y_offset):
        """Draw budget allocation tab content"""
        # Budget mensuel
        budget_label = font.render("Budget mensuel :", True, (200, 200, 200))
        screen.blit(budget_label, (modal_x + 30, y_offset))
        y_offset += 30

        # Budget controls: (-) $X,XXX (+)
        button_size = 30
        spacing = 10

        # Minus button
        self.budget_minus_rect = pygame.Rect(modal_x + 30, y_offset, button_size, button_size)
        pygame.draw.rect(screen, (100, 100, 120), self.budget_minus_rect)
        pygame.draw.rect(screen, (200, 200, 200), self.budget_minus_rect, 1)
        minus_text = font.render("-", True, (255, 255, 255))
        screen.blit(minus_text, (self.budget_minus_rect.x + 8, self.budget_minus_rect.y + 5))

        # Budget display
        budget_text_x = self.budget_minus_rect.right + spacing
        budget_str = f"${research_bureau.monthly_budget:,}"
        budget_display = font.render(budget_str, True, (100, 255, 100))
        screen.blit(budget_display, (budget_text_x, y_offset + 5))

        # Plus button
        self.budget_plus_rect = pygame.Rect(
            budget_text_x + budget_display.get_width() + spacing,
            y_offset,
            button_size,
            button_size
        )
        pygame.draw.rect(screen, (100, 100, 120), self.budget_plus_rect)
        pygame.draw.rect(screen, (200, 200, 200), self.budget_plus_rect, 1)
        plus_text = font.render("+", True, (255, 255, 255))
        screen.blit(plus_text, (self.budget_plus_rect.x + 8, self.budget_plus_rect.y + 5))

        y_offset += 40

        # Info: Dépenses ce mois
        days_until = research_bureau.get_days_until_next_deduction(current_day)
        info_text = f"Prochain prélèvement : dans {days_until} jours"
        info_render = font.render(info_text, True, (180, 180, 180))
        screen.blit(info_render, (modal_x + 30, y_offset))
        y_offset += 40

        # Separator
        pygame.draw.line(screen, (100, 100, 100),
                        (modal_x + 20, y_offset),
                        (modal_x + modal_w - 20, y_offset), 2)
        y_offset += 20

        # Répartition du budget
        allocation_title = font.render("Répartition du budget :", True, (200, 200, 200))
        screen.blit(allocation_title, (modal_x + 30, y_offset))
        y_offset += 35

        # Sliders pour chaque catégorie
        self.slider_rects = {}
        slider_width = 300
        slider_height = 10

        for category in research_bureau.categories.keys():
            cat_data = research_bureau.categories[category]
            cat_name, _ = self.CATEGORY_NAMES.get(category, (category, ""))

            # Category icon
            if category in self.category_icons:
                screen.blit(self.category_icons[category], (modal_x + 30, y_offset - 2))

            # Category label
            label_render = font.render(cat_name, True, (200, 200, 200))
            screen.blit(label_render, (modal_x + 60, y_offset))

            # Percentage and dollar amount
            percentage = cat_data.allocation * 100
            dollar_amount = research_bureau.monthly_budget * cat_data.allocation
            daily_amount = dollar_amount / 30.0

            percentage_text = f"{percentage:.0f}%"
            percentage_render = font.render(percentage_text, True, (255, 255, 100))
            screen.blit(percentage_render, (modal_x + 200, y_offset))

            dollar_text = f"${dollar_amount:.0f}"
            dollar_render = font.render(dollar_text, True, (100, 255, 100))
            screen.blit(dollar_render, (modal_x + 260, y_offset))

            daily_text = f"(${daily_amount:.1f}/jour)"
            daily_render = font.render(daily_text, True, (150, 150, 150))
            screen.blit(daily_render, (modal_x + 360, y_offset))

            # Points accumulés et limite
            cat_progress = research_bureau.get_category_progress(category)
            current_pts = cat_progress.get('points', 0)
            points_cap = cat_progress.get('points_cap', 1000)
            pts_text = f"{current_pts:.0f}/{points_cap}"
            pts_color = (255, 150, 50) if current_pts >= points_cap else (150, 200, 255)
            pts_render = font.render(pts_text, True, pts_color)
            screen.blit(pts_render, (modal_x + 500, y_offset))

            y_offset += 25

            # Slider
            slider_x = modal_x + 30
            slider_y = y_offset
            slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
            self.slider_rects[category] = slider_rect

            # Background
            pygame.draw.rect(screen, (60, 60, 70), slider_rect)
            pygame.draw.rect(screen, (100, 100, 110), slider_rect, 1)

            # Fill (based on allocation)
            fill_width = int(slider_width * cat_data.allocation)
            if fill_width > 0:
                fill_rect = pygame.Rect(slider_x, slider_y, fill_width, slider_height)
                pygame.draw.rect(screen, (100, 180, 255), fill_rect)

            # Handle
            handle_x = slider_x + fill_width
            handle_rect = pygame.Rect(handle_x - 5, slider_y - 5, 10, slider_height + 10)
            pygame.draw.rect(screen, (200, 200, 200), handle_rect)
            pygame.draw.rect(screen, (255, 255, 255), handle_rect, 1)

            y_offset += 30

        # Total allocation check
        total_allocation = research_bureau.get_total_allocation()
        total_text = f"Total : {total_allocation*100:.0f}%"
        total_color = (100, 255, 100) if total_allocation <= 1.0 else (255, 100, 100)
        total_render = font.render(total_text, True, total_color)
        screen.blit(total_render, (modal_x + 30, y_offset))

        if total_allocation > 1.0:
            warning = font.render("⚠️ Total dépasse 100% !", True, (255, 100, 100))
            screen.blit(warning, (modal_x + 150, y_offset))

    def _draw_progress_tab(self, screen, font, research_bureau, modal_x, modal_y, modal_w, modal_h, y_offset):
        """Draw research progress tab content"""
        # Category tabs
        tab_width = 100
        tab_height = 35
        tab_x = modal_x + 20
        self.category_tab_rects = {}

        for i, category in enumerate(research_bureau.CATEGORIES):
            cat_name, _ = self.CATEGORY_NAMES.get(category, (category, ""))
            is_active = (category == self.current_progress_category)

            tab_rect = pygame.Rect(tab_x + i * (tab_width + 5), y_offset, tab_width, tab_height)
            self.category_tab_rects[category] = tab_rect

            # Tab background
            tab_color = (60, 120, 180) if is_active else (60, 60, 70)
            pygame.draw.rect(screen, tab_color, tab_rect)
            pygame.draw.rect(screen, (200, 200, 200), tab_rect, 1)

            # Tab icon (centered)
            if category in self.category_icons_small:
                icon = self.category_icons_small[category]
                icon_x = tab_rect.x + (tab_width - 20) // 2
                icon_y = tab_rect.y + 8
                screen.blit(icon, (icon_x, icon_y))

        y_offset += 50

        # Category info
        cat_data = research_bureau.get_category_progress(self.current_progress_category)
        cat_name, _ = self.CATEGORY_NAMES.get(self.current_progress_category,
                                               (self.current_progress_category, ""))

        # Points accumulés
        points_text = f"Points accumulés : {cat_data.get('points', 0):.0f} pts"
        daily_pts = cat_data.get('daily_points', 0)
        if daily_pts > 0:
            points_text += f"  (+{daily_pts:.1f}/jour)"

        points_render = font.render(points_text, True, (100, 255, 100))
        screen.blit(points_render, (modal_x + 30, y_offset))
        y_offset += 35

        # Separator
        pygame.draw.line(screen, (100, 100, 100),
                        (modal_x + 20, y_offset),
                        (modal_x + modal_w - 20, y_offset), 2)
        y_offset += 15

        # Upgrades list (scrollable area)
        scroll_area_y = y_offset
        scroll_area_h = modal_h - (y_offset - modal_y) - 20  # Space from bottom

        upgrades = cat_data.get('upgrades', [])
        content_y = scroll_area_y - self.scroll_offset

        # Calculate max scroll
        total_content_height = len(upgrades) * 90
        self.max_scroll = max(0, total_content_height - scroll_area_h)

        # Find the first locked upgrade that can be unlocked (the one currently in progress)
        current_research = None
        for upgrade in upgrades:
            if not upgrade.unlocked and upgrade.can_unlock(research_bureau.unlocked_ids, 0):
                current_research = upgrade
                break

        # Clear upgrade rects for this frame
        self.upgrade_rects = {}

        # Draw upgrades
        for upgrade in upgrades:
            # Skip if outside visible area
            if content_y + 85 < scroll_area_y or content_y > scroll_area_y + scroll_area_h:
                content_y += 90
                continue

            # Upgrade box
            upgrade_rect = pygame.Rect(modal_x + 30, content_y, modal_w - 60, 80)

            # Background color based on status
            can_unlock = False
            if upgrade.unlocked:
                bg_color = (50, 100, 50)  # Green for unlocked
                border_color = (100, 200, 100)
                status_emoji = "✅"
            else:
                # Check if can unlock
                can_unlock = upgrade.can_unlock(
                    research_bureau.unlocked_ids,
                    cat_data.get('points', 0)
                )
                if can_unlock:
                    bg_color = (80, 80, 120)  # Blue for ready
                    border_color = (120, 120, 200)
                    status_emoji = "🔄"
                    # Register clickable rect for unlocking
                    self.upgrade_rects[upgrade.id] = upgrade_rect
                else:
                    bg_color = (60, 60, 70)  # Gray for locked
                    border_color = (100, 100, 110)
                    status_emoji = "🔒"

            pygame.draw.rect(screen, bg_color, upgrade_rect)
            pygame.draw.rect(screen, border_color, upgrade_rect, 2)

            # Status emoji
            emoji_render = font.render(status_emoji, True, (255, 255, 255))
            screen.blit(emoji_render, (upgrade_rect.x + 10, upgrade_rect.y + 10))

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

            # Progress bar ONLY for the current research in progress
            if not upgrade.unlocked and upgrade == current_research:
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

            # Unlock button (if can unlock)
            if can_unlock:
                btn_width = 120
                btn_height = 30
                btn_x = upgrade_rect.right - btn_width - 10
                btn_y = upgrade_rect.y + 45
                btn_rect = pygame.Rect(btn_x, btn_y, btn_width, btn_height)

                # Button background with hover effect
                pygame.draw.rect(screen, (100, 200, 100), btn_rect)
                pygame.draw.rect(screen, (150, 255, 150), btn_rect, 2)

                # Button text
                btn_text = font.render("DÉBLOQUER", True, (255, 255, 255))
                text_rect = btn_text.get_rect(center=btn_rect.center)
                screen.blit(btn_text, text_rect)

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
