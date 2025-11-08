"""
Loan Management Modal UI
Allows players to take loans and repay them
"""

import pygame
from typing import Optional
from ..loan import LoanManager, LOAN_TYPES


class LoanModal:
    """Modal for managing loans"""

    def __init__(self, font: pygame.font.Font):
        self.font = font
        self.visible = False

        # Modal dimensions
        self.width = 650
        self.height = 550
        self.padding = 20

    def show(self):
        """Show the modal"""
        self.visible = True

    def hide(self):
        """Hide the modal"""
        self.visible = False

    def toggle(self):
        """Toggle modal visibility"""
        self.visible = not self.visible

    def handle_event(self, event: pygame.event.Event, loan_manager: LoanManager,
                     economy, current_day: int) -> bool:
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

                # Handle loan selection buttons
                if not loan_manager.has_active_loan():
                    y_offset = modal_y + 80
                    for idx, (key, loan_type) in enumerate(LOAN_TYPES.items()):
                        button_y = y_offset + idx * 130
                        button_rect = pygame.Rect(modal_x + 220, button_y + 80, 200, 35)

                        if button_rect.collidepoint(mx, my):
                            # Take the loan
                            loan_manager.take_loan(key, current_day)
                            economy.add_income(loan_type.amount)  # Add money to economy
                            return True

                # Handle early repayment button
                else:
                    repay_button_y = modal_y + 380
                    repay_button_rect = pygame.Rect(modal_x + 180, repay_button_y, 280, 40)

                    if repay_button_rect.collidepoint(mx, my):
                        # Check if player can afford it
                        amount = loan_manager.active_loan.get_early_repayment_amount()
                        if economy.cash >= amount:
                            loan_manager.repay_early()
                            economy.add_expense(amount)
                            return True

        return False

    def draw(self, screen: pygame.Surface, loan_manager: LoanManager, economy):
        """Draw the loan management modal"""
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
        title_surf = self.font.render("💰 Gestion des Prêts", True, (255, 255, 255))
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

        # Content
        if loan_manager.has_active_loan():
            self._draw_active_loan(screen, modal_x, modal_y, loan_manager, economy)
        else:
            self._draw_loan_options(screen, modal_x, modal_y)

    def _draw_loan_options(self, screen: pygame.Surface, modal_x: int, modal_y: int):
        """Draw available loan options"""
        y_offset = modal_y + 70

        for idx, (key, loan_type) in enumerate(LOAN_TYPES.items()):
            box_y = y_offset + idx * 130
            box_rect = pygame.Rect(modal_x + 20, box_y, self.width - 40, 120)

            # Background
            pygame.draw.rect(screen, (50, 50, 60), box_rect)
            pygame.draw.rect(screen, (80, 80, 90), box_rect, 2)

            # Loan name
            name_surf = self.font.render(loan_type.name, True, (255, 220, 100))
            screen.blit(name_surf, (modal_x + 35, box_y + 10))

            # Details
            details_y = box_y + 35
            amount_text = f"Montant: ${loan_type.amount:,.0f}"
            duration_text = f"Durée: {loan_type.duration_days} jours"
            interest_text = f"Intérêt: +{loan_type.interest_rate:.0f}%"

            detail_surf1 = self.font.render(amount_text, True, (200, 200, 200))
            detail_surf2 = self.font.render(duration_text, True, (200, 200, 200))
            detail_surf3 = self.font.render(interest_text, True, (200, 200, 200))

            screen.blit(detail_surf1, (modal_x + 35, details_y))
            screen.blit(detail_surf2, (modal_x + 200, details_y))
            screen.blit(detail_surf3, (modal_x + 360, details_y))

            # Repayment info
            daily_payment = loan_type.get_daily_payment()
            total_amount = loan_type.get_total_amount()

            repay_text = f"Remboursement: ${daily_payment:.2f}/jour"
            total_text = f"Total: ${total_amount:,.0f}"

            repay_surf = self.font.render(repay_text, True, (150, 150, 150))
            total_surf = self.font.render(total_text, True, (255, 100, 100))

            screen.blit(repay_surf, (modal_x + 35, details_y + 25))
            screen.blit(total_surf, (modal_x + 360, details_y + 25))

            # Button
            mx, my = pygame.mouse.get_pos()
            button_rect = pygame.Rect(modal_x + 220, box_y + 80, 200, 35)
            is_hover = button_rect.collidepoint(mx, my)
            btn_color = (100, 180, 100) if is_hover else (80, 140, 80)

            pygame.draw.rect(screen, btn_color, button_rect)
            pygame.draw.rect(screen, (150, 150, 150), button_rect, 2)

            btn_text = self.font.render("Emprunter", True, (255, 255, 255))
            btn_rect = btn_text.get_rect(center=button_rect.center)
            screen.blit(btn_text, btn_rect)

        # Footer info
        footer_y = modal_y + self.height - 50
        info_text = "Attention: Un seul prêt actif à la fois"
        info_surf = self.font.render(info_text, True, (200, 150, 150))
        screen.blit(info_surf, (modal_x + 20, footer_y))

    def _draw_active_loan(self, screen: pygame.Surface, modal_x: int, modal_y: int,
                          loan_manager: LoanManager, economy):
        """Draw active loan information and repayment options"""
        loan_info = loan_manager.get_loan_info()
        if not loan_info:
            return

        y = modal_y + 70

        # Active loan header
        header_surf = self.font.render("Prêt actuel:", True, (255, 220, 100))
        screen.blit(header_surf, (modal_x + 20, y))

        # Loan details box
        box_rect = pygame.Rect(modal_x + 20, y + 30, self.width - 40, 250)
        pygame.draw.rect(screen, (50, 50, 60), box_rect)
        pygame.draw.rect(screen, (100, 180, 180), box_rect, 2)

        detail_y = y + 45

        # Loan type and amount
        name_surf = self.font.render(loan_info['name'], True, (255, 255, 255))
        screen.blit(name_surf, (modal_x + 35, detail_y))

        amount_surf = self.font.render(f"Montant initial: ${loan_info['original_amount']:,.0f}",
                                       True, (200, 200, 200))
        screen.blit(amount_surf, (modal_x + 35, detail_y + 30))

        # Progress
        days_text = f"Jours restants: {loan_info['days_remaining']}/{loan_info['total_days']}"
        days_surf = self.font.render(days_text, True, (200, 200, 200))
        screen.blit(days_surf, (modal_x + 35, detail_y + 60))

        paid_text = f"Déjà payé: ${loan_info['amount_paid']:,.2f}"
        paid_surf = self.font.render(paid_text, True, (150, 150, 150))
        screen.blit(paid_surf, (modal_x + 35, detail_y + 90))

        # Separator
        pygame.draw.line(screen, (80, 80, 90),
                        (modal_x + 35, detail_y + 125),
                        (modal_x + self.width - 35, detail_y + 125), 1)

        # Normal repayment
        normal_header = self.font.render("Remboursement normal:", True, (220, 220, 220))
        screen.blit(normal_header, (modal_x + 35, detail_y + 140))

        remaining_text = f"Restant: ${loan_info['remaining_normal']:,.2f} ({loan_info['days_remaining']} × ${loan_info['daily_payment']:.2f})"
        remaining_surf = self.font.render(remaining_text, True, (180, 180, 180))
        screen.blit(remaining_surf, (modal_x + 50, detail_y + 165))

        # Early repayment
        early_header = self.font.render("Remboursement anticipé:", True, (100, 220, 100))
        screen.blit(early_header, (modal_x + 35, detail_y + 195))

        early_amount = loan_info['early_repayment']
        savings = loan_info['early_savings']
        early_text = f"Total: ${early_amount:,.2f} (économie: ${savings:,.2f})"
        early_surf = self.font.render(early_text, True, (100, 200, 100))
        screen.blit(early_surf, (modal_x + 50, detail_y + 220))

        # Repay button
        mx, my = pygame.mouse.get_pos()
        button_y = modal_y + 380
        button_rect = pygame.Rect(modal_x + 180, button_y, 280, 40)

        can_afford = economy.cash >= early_amount
        is_hover = button_rect.collidepoint(mx, my)

        if can_afford:
            btn_color = (100, 180, 100) if is_hover else (80, 140, 80)
            btn_text_color = (255, 255, 255)
            btn_text = f"Rembourser maintenant (-${early_amount:,.2f})"
        else:
            btn_color = (100, 60, 60)
            btn_text_color = (150, 150, 150)
            btn_text = "Fonds insuffisants"

        pygame.draw.rect(screen, btn_color, button_rect)
        pygame.draw.rect(screen, (150, 150, 150), button_rect, 2)

        text_surf = self.font.render(btn_text, True, btn_text_color)
        text_rect = text_surf.get_rect(center=button_rect.center)
        screen.blit(text_surf, text_rect)

        # Footer info
        footer_y = modal_y + self.height - 50
        info_text = f"Paiement quotidien: ${loan_info['daily_payment']:.2f} (automatique à minuit)"
        info_surf = self.font.render(info_text, True, (150, 150, 150))
        screen.blit(info_surf, (modal_x + 20, footer_y))
