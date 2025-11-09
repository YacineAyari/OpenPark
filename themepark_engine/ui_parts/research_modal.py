"""
Research Bureau Modal - Gestion du budget et répartition R&D
"""

import pygame
from typing import Tuple, Optional
from pathlib import Path


class ResearchBureauModal:
    """Modal pour gérer le budget mensuel et la répartition par catégorie"""

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

        # Sliders pour l'allocation
        self.dragging_slider = None  # Nom de la catégorie en cours de drag
        self.slider_rects = {}  # category -> Rect

        # Buttons
        self.budget_minus_rect = None
        self.budget_plus_rect = None
        self.progress_button_rect = None
        self.close_button_rect = None

        # Load category icons (24x24)
        self.category_icons = {}
        self._load_category_icons()

    def _load_category_icons(self):
        """Load OpenMoji sprites for categories"""
        from .. import assets
        icon_size = (24, 24)

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

    def show(self):
        """Affiche le modal"""
        self.visible = True

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

            # Budget buttons
            if self.budget_minus_rect and self.budget_minus_rect.collidepoint(mouse_x, mouse_y):
                research_bureau.set_monthly_budget(research_bureau.monthly_budget - 500)
                return True

            if self.budget_plus_rect and self.budget_plus_rect.collidepoint(mouse_x, mouse_y):
                research_bureau.set_monthly_budget(research_bureau.monthly_budget + 500)
                return True

            # Progress button
            if self.progress_button_rect and self.progress_button_rect.collidepoint(mouse_x, mouse_y):
                # Signal pour ouvrir le modal de progrès (géré par engine)
                return 'open_progress'

            # Close button
            if self.close_button_rect and self.close_button_rect.collidepoint(mouse_x, mouse_y):
                self.hide()
                return True

            # Sliders
            for category, rect in self.slider_rects.items():
                if rect.collidepoint(mouse_x, mouse_y):
                    self.dragging_slider = category
                    return True

        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging_slider = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_slider:
                mouse_x, mouse_y = event.pos
                # Calculer la nouvelle allocation
                rect = self.slider_rects[self.dragging_slider]
                slider_width = 300
                # Position relative dans la barre
                relative_x = max(0, min(slider_width, mouse_x - rect.x))
                new_allocation = relative_x / slider_width
                research_bureau.set_category_allocation(self.dragging_slider, new_allocation)
                return True

        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font,
             research_bureau, current_day: int) -> Optional[str]:
        """
        Dessine le modal Bureau de R&D

        Returns:
            'open_progress' si le joueur clique sur "Voir Progrès"
        """
        if not self.visible:
            return None

        screen_w, screen_h = screen.get_size()

        # Modal dimensions (increased size)
        modal_w = 700
        modal_h = 650
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

        y_offset += 35

        # Separator
        pygame.draw.line(screen, (100, 100, 100),
                        (modal_x + 20, y_offset),
                        (modal_x + modal_w - 20, y_offset), 2)
        y_offset += 20

        # Button: Voir Progrès Recherche
        self.progress_button_rect = pygame.Rect(modal_x + 30, y_offset, 260, 35)
        pygame.draw.rect(screen, (60, 120, 180), self.progress_button_rect)
        pygame.draw.rect(screen, (100, 160, 220), self.progress_button_rect, 2)
        progress_btn_text = font.render("Voir Progrès Recherche", True, (255, 255, 255))
        screen.blit(progress_btn_text,
                   (self.progress_button_rect.x + 20, self.progress_button_rect.y + 8))

        # Close button
        self.close_button_rect = pygame.Rect(modal_x + 310, y_offset, 260, 35)
        pygame.draw.rect(screen, (100, 100, 120), self.close_button_rect)
        pygame.draw.rect(screen, (150, 150, 170), self.close_button_rect, 2)
        close_btn_text = font.render("Fermer", True, (255, 255, 255))
        screen.blit(close_btn_text,
                   (self.close_button_rect.x + 95, self.close_button_rect.y + 8))

        return None
