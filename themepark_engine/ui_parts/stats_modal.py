"""
Financial Statistics Modal UI
Displays financial stats and graphs (30 days / 1 year)
"""

import pygame
from typing import List, Dict
from ..finance_stats import FinanceStatsTracker


class StatsModal:
    """Modal for displaying financial statistics and graphs"""

    def __init__(self, font: pygame.font.Font):
        self.font = font
        self.visible = False

        # Modal dimensions
        self.width = 700
        self.height = 600
        self.padding = 20

        # Graph mode: '30days' or '1year'
        self.graph_mode = '30days'

        # Graph area
        self.graph_width = 660
        self.graph_height = 250
        self.graph_padding = 10

    def show(self):
        """Show the modal"""
        self.visible = True

    def hide(self):
        """Hide the modal"""
        self.visible = False

    def toggle(self):
        """Toggle modal visibility"""
        self.visible = not self.visible

    def handle_event(self, event: pygame.event.Event, stats_tracker: FinanceStatsTracker) -> bool:
        """
        Handle pygame events for the modal.
        Returns True if event was handled, False otherwise.
        """
        if not self.visible:
            return False

        screen_w, screen_h = pygame.display.get_surface().get_size()
        modal_x = (screen_w - self.width) // 2
        modal_y = (screen_h - self.height) // 2

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.hide()
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mx, my = event.pos

                # Click outside modal closes it
                if not (modal_x <= mx <= modal_x + self.width and modal_y <= my <= modal_y + self.height):
                    self.hide()
                    return True

                # Close button (X) in top-right corner
                close_button_size = 30
                close_button_x = modal_x + self.width - close_button_size - 10
                close_button_y = modal_y + 10
                close_button_rect = pygame.Rect(close_button_x, close_button_y, close_button_size, close_button_size)
                if close_button_rect.collidepoint(mx, my):
                    self.hide()
                    return True

                # Graph mode toggle buttons
                toggle_y = modal_y + 70
                btn_30days = pygame.Rect(modal_x + 20, toggle_y, 120, 30)
                btn_1year = pygame.Rect(modal_x + 150, toggle_y, 120, 30)

                if btn_30days.collidepoint(mx, my):
                    self.graph_mode = '30days'
                    return True
                elif btn_1year.collidepoint(mx, my):
                    self.graph_mode = '1year'
                    return True

        return False

    def draw(self, screen: pygame.Surface, stats_tracker: FinanceStatsTracker):
        """Draw the statistics modal"""
        if not self.visible:
            return

        screen_w, screen_h = screen.get_size()
        modal_x = (screen_w - self.width) // 2
        modal_y = (screen_h - self.height) // 2

        # Draw semi-transparent overlay
        overlay = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        screen.blit(overlay, (0, 0))

        # Draw modal background
        modal_rect = pygame.Rect(modal_x, modal_y, self.width, self.height)
        pygame.draw.rect(screen, (40, 40, 50), modal_rect)
        pygame.draw.rect(screen, (100, 100, 120), modal_rect, 3)

        # Title
        title_surf = self.font.render("📊 Statistiques Financières", True, (255, 255, 255))
        screen.blit(title_surf, (modal_x + self.padding, modal_y + self.padding))

        # Close button (X) in top-right corner
        close_button_size = 30
        close_button_x = modal_x + self.width - close_button_size - 10
        close_button_y = modal_y + 10
        close_button_rect = pygame.Rect(close_button_x, close_button_y, close_button_size, close_button_size)

        mx, my = pygame.mouse.get_pos()
        is_hovering = close_button_rect.collidepoint(mx, my)
        button_color = (180, 60, 60) if is_hovering else (120, 40, 40)

        pygame.draw.rect(screen, button_color, close_button_rect)
        pygame.draw.rect(screen, (200, 200, 200), close_button_rect, 2)

        # Draw X
        x_color = (255, 255, 255)
        margin = 8
        pygame.draw.line(screen, x_color,
                        (close_button_x + margin, close_button_y + margin),
                        (close_button_x + close_button_size - margin, close_button_y + close_button_size - margin), 2)
        pygame.draw.line(screen, x_color,
                        (close_button_x + close_button_size - margin, close_button_y + margin),
                        (close_button_x + margin, close_button_y + close_button_size - margin), 2)

        # Graph mode toggle buttons
        toggle_y = modal_y + 70
        btn_30days = pygame.Rect(modal_x + 20, toggle_y, 120, 30)
        btn_1year = pygame.Rect(modal_x + 150, toggle_y, 120, 30)

        # 30 days button
        is_30days_active = self.graph_mode == '30days'
        btn_30days_color = (100, 140, 180) if is_30days_active else (60, 60, 70)
        pygame.draw.rect(screen, btn_30days_color, btn_30days)
        pygame.draw.rect(screen, (150, 150, 150), btn_30days, 2)
        text_30days = self.font.render("30 jours", True, (255, 255, 255))
        text_rect_30days = text_30days.get_rect(center=btn_30days.center)
        screen.blit(text_30days, text_rect_30days)

        # 1 year button
        is_1year_active = self.graph_mode == '1year'
        btn_1year_color = (100, 140, 180) if is_1year_active else (60, 60, 70)
        pygame.draw.rect(screen, btn_1year_color, btn_1year)
        pygame.draw.rect(screen, (150, 150, 150), btn_1year, 2)
        text_1year = self.font.render("1 an", True, (255, 255, 255))
        text_rect_1year = text_1year.get_rect(center=btn_1year.center)
        screen.blit(text_1year, text_rect_1year)

        # Draw graph
        graph_y = modal_y + 115
        self._draw_graph(screen, modal_x + 20, graph_y, stats_tracker)

        # Draw statistics summary
        stats_y = graph_y + self.graph_height + 30
        self._draw_stats_summary(screen, modal_x, stats_y, stats_tracker)

    def _draw_graph(self, screen: pygame.Surface, x: int, y: int, stats_tracker: FinanceStatsTracker):
        """Draw the financial graph"""
        # Graph background
        graph_rect = pygame.Rect(x, y, self.graph_width, self.graph_height)
        pygame.draw.rect(screen, (30, 30, 40), graph_rect)
        pygame.draw.rect(screen, (80, 80, 90), graph_rect, 1)

        # Get data based on mode
        if self.graph_mode == '30days':
            data = stats_tracker.get_daily_graph_data(30)
            x_label = "Jours"
        else:  # 1year
            data = stats_tracker.get_monthly_graph_data()
            x_label = "Mois"

        if not data:
            # No data available
            no_data_text = self.font.render("Pas encore de données", True, (150, 150, 150))
            text_rect = no_data_text.get_rect(center=(x + self.graph_width // 2, y + self.graph_height // 2))
            screen.blit(no_data_text, text_rect)
            return

        # Calculate scales
        max_revenue = max((d['revenue'] for d in data), default=100)
        max_expenses = max((d['expenses'] for d in data), default=100)
        max_value = max(max_revenue, max_expenses, 100)  # Minimum 100 for scale

        # Add 10% padding to top
        max_value *= 1.1

        # Draw grid lines (5 horizontal lines)
        for i in range(6):
            line_y = y + (self.graph_height - 2 * self.graph_padding) * i / 5 + self.graph_padding
            pygame.draw.line(screen, (50, 50, 60),
                           (x + self.graph_padding, line_y),
                           (x + self.graph_width - self.graph_padding, line_y), 1)

            # Y-axis labels
            value = max_value * (1 - i / 5)
            label = self.font.render(f"${value:.0f}", True, (120, 120, 130))
            screen.blit(label, (x + 5, line_y - 8))

        # Calculate bar/point spacing
        plot_area_width = self.graph_width - 2 * self.graph_padding - 60  # Leave space for labels
        plot_area_height = self.graph_height - 2 * self.graph_padding
        data_count = len(data)
        spacing = plot_area_width / max(data_count, 1)

        # Draw data points/bars
        for i, entry in enumerate(data):
            bar_x = x + self.graph_padding + 60 + i * spacing

            # Calculate heights
            revenue_height = (entry['revenue'] / max_value) * plot_area_height
            expenses_height = (entry['expenses'] / max_value) * plot_area_height

            base_y = y + self.graph_height - self.graph_padding

            # Revenue bar (green)
            if revenue_height > 0:
                revenue_rect = pygame.Rect(
                    bar_x,
                    base_y - revenue_height,
                    spacing * 0.4,
                    revenue_height
                )
                pygame.draw.rect(screen, (100, 200, 100), revenue_rect)

            # Expenses bar (red)
            if expenses_height > 0:
                expenses_rect = pygame.Rect(
                    bar_x + spacing * 0.4,
                    base_y - expenses_height,
                    spacing * 0.4,
                    expenses_height
                )
                pygame.draw.rect(screen, (200, 100, 100), expenses_rect)

        # Legend
        legend_y = y + self.graph_height + 5
        # Green square
        pygame.draw.rect(screen, (100, 200, 100), (x + 150, legend_y, 15, 15))
        legend_revenue = self.font.render("Revenus", True, (200, 200, 200))
        screen.blit(legend_revenue, (x + 170, legend_y))

        # Red square
        pygame.draw.rect(screen, (200, 100, 100), (x + 260, legend_y, 15, 15))
        legend_expenses = self.font.render("Dépenses", True, (200, 200, 200))
        screen.blit(legend_expenses, (x + 280, legend_y))

    def _draw_stats_summary(self, screen: pygame.Surface, modal_x: int, y: int,
                           stats_tracker: FinanceStatsTracker):
        """Draw statistics summary below graph"""
        # Get statistics
        today = stats_tracker.get_today_stats()
        last_30 = stats_tracker.get_last_30_days_stats()
        last_365 = stats_tracker.get_last_365_days_stats()

        # Create summary boxes
        box_width = 200
        box_height = 120
        box_spacing = 20
        start_x = modal_x + (self.width - 3 * box_width - 2 * box_spacing) // 2

        # Today
        self._draw_stat_box(screen, start_x, y, box_width, box_height,
                           "Aujourd'hui", today)

        # Last 30 days
        self._draw_stat_box(screen, start_x + box_width + box_spacing, y, box_width, box_height,
                           "Ce Mois (30j)", last_30)

        # Last year
        self._draw_stat_box(screen, start_x + 2 * (box_width + box_spacing), y, box_width, box_height,
                           "Cette Année", last_365, show_avg=True)

    def _draw_stat_box(self, screen: pygame.Surface, x: int, y: int, width: int, height: int,
                      title: str, stats: Dict, show_avg: bool = False):
        """Draw a single statistics box"""
        # Background
        box_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, (50, 50, 60), box_rect)
        pygame.draw.rect(screen, (80, 80, 90), box_rect, 2)

        # Title
        title_surf = self.font.render(title, True, (220, 220, 100))
        title_rect = title_surf.get_rect(centerx=x + width // 2, top=y + 5)
        screen.blit(title_surf, title_rect)

        # Stats
        text_y = y + 30
        line_height = 20

        # Revenue
        revenue_text = f"Revenus  : ${stats['revenue']:,.0f}"
        revenue_surf = self.font.render(revenue_text, True, (100, 200, 100))
        screen.blit(revenue_surf, (x + 10, text_y))

        # Expenses
        expenses_text = f"Dépenses : ${stats['expenses']:,.0f}"
        expenses_surf = self.font.render(expenses_text, True, (200, 100, 100))
        screen.blit(expenses_surf, (x + 10, text_y + line_height))

        # Profit
        profit = stats['profit']
        profit_color = (100, 220, 100) if profit >= 0 else (220, 100, 100)
        profit_sign = "+" if profit >= 0 else ""
        profit_text = f"Profit   : {profit_sign}${profit:,.0f}"
        profit_surf = self.font.render(profit_text, True, profit_color)
        screen.blit(profit_surf, (x + 10, text_y + 2 * line_height))

        # Average per day (for yearly stats)
        if show_avg and 'avg_profit_per_day' in stats:
            avg = stats['avg_profit_per_day']
            avg_color = (150, 150, 150)
            avg_sign = "+" if avg >= 0 else ""
            avg_text = f"Moy/jour : {avg_sign}${avg:.0f}"
            avg_surf = self.font.render(avg_text, True, avg_color)
            screen.blit(avg_surf, (x + 10, text_y + 3 * line_height))
