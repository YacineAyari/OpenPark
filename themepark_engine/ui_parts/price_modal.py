"""
Price Management Modal UI
Allows players to set selling prices for products
"""

import pygame
from typing import Optional, List
from ..inventory import InventoryManager
from ..pricing import PricingManager


class PriceModal:
    """Modal for managing product selling prices"""

    def __init__(self, font: pygame.font.Font):
        self.font = font
        self.visible = False

        # Modal dimensions
        self.width = 600
        self.height = 500
        self.padding = 20

        # Price adjustment increment
        self.price_increment = 0.10  # +/- 0.10

    def show(self):
        """Show the modal"""
        self.visible = True

    def hide(self):
        """Hide the modal"""
        self.visible = False

    def toggle(self):
        """Toggle modal visibility"""
        self.visible = not self.visible

    def handle_event(self, event: pygame.event.Event, inventory: InventoryManager,
                     pricing: PricingManager, shops: list = None) -> bool:
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

                # Handle price adjustment buttons
                if shops:
                    product_list_y = modal_y + 80
                    visible_index = 0

                    for product_id, product in inventory.products.items():
                        # Check if player has any shops that use this product
                        has_shop = self._has_shop_for_product(product_id, product, shops)
                        if not has_shop:
                            continue

                        y_pos = product_list_y + visible_index * 70

                        # Get current cost and price
                        cost = inventory.get_current_cost(product_id)
                        current_price = pricing.get_price(product_id, cost)

                        # Button positions: |-| $X.XX |+|
                        price_section_x = modal_x + 260
                        btn_size = 25
                        btn_y = y_pos - 2

                        # - Button (left of price)
                        btn_minus = pygame.Rect(price_section_x, btn_y, btn_size, btn_size)
                        if btn_minus.collidepoint(mx, my):
                            new_price = max(pricing.get_min_price(cost), current_price - self.price_increment)
                            pricing.set_price(product_id, new_price)
                            return True

                        # Calculate price text width for + button position
                        price_text = f"${current_price:.2f}"
                        price_surf = self.font.render(price_text, True, (255, 220, 100))
                        price_width = price_surf.get_width()
                        price_x = price_section_x + btn_size + 10

                        # + Button (right of price)
                        btn_plus = pygame.Rect(price_x + price_width + 10, btn_y, btn_size, btn_size)
                        if btn_plus.collidepoint(mx, my):
                            new_price = min(pricing.get_max_price(cost), current_price + self.price_increment)
                            pricing.set_price(product_id, new_price)
                            return True

                        visible_index += 1

        return False

    def _has_shop_for_product(self, product_id: str, product, shops: list) -> bool:
        """Check if player has placed any shop that uses this product"""
        for shop_id in product.used_by_shops:
            for shop in shops:
                if shop.defn.id == shop_id:
                    return True
        return False

    def draw(self, screen: pygame.Surface, inventory: InventoryManager,
             pricing: PricingManager, shops: list = None):
        """Draw the price management modal"""
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
        title_surf = self.font.render("Gestion des Prix", True, (255, 255, 255))
        screen.blit(title_surf, (modal_x + self.padding, modal_y + self.padding))

        # Close button (X) in top-right corner
        close_button_size = 30
        close_button_x = modal_x + self.width - close_button_size - 10
        close_button_y = modal_y + 10
        close_button_rect = pygame.Rect(close_button_x, close_button_y, close_button_size, close_button_size)

        # Check if mouse is hovering over close button
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

        # Header row
        header_y = modal_y + 60
        header_color = (150, 150, 160)

        product_header = self.font.render("Produit", True, header_color)
        screen.blit(product_header, (modal_x + 20, header_y))

        cost_header = self.font.render("Coût", True, header_color)
        screen.blit(cost_header, (modal_x + 180, header_y))

        price_header = self.font.render("Prix de vente", True, header_color)
        screen.blit(price_header, (modal_x + 300, header_y))

        margin_header = self.font.render("Marge", True, header_color)
        screen.blit(margin_header, (modal_x + 440, header_y))

        # Product list
        if not shops:
            no_shops_text = self.font.render("Aucun magasin placé", True, (150, 150, 150))
            screen.blit(no_shops_text, (modal_x + self.width // 2 - 80, modal_y + 200))
            return

        product_list_y = modal_y + 80
        visible_index = 0

        for product_id, product in inventory.products.items():
            # Check if player has any shops that use this product
            has_shop = self._has_shop_for_product(product_id, product, shops)
            if not has_shop:
                continue

            y_pos = product_list_y + visible_index * 70

            # Get current cost (with inflation)
            cost = inventory.get_current_cost(product_id)

            # Initialize price if not set
            pricing.initialize_product(product_id, cost)
            current_price = pricing.get_price(product_id, cost)

            # Calculate margin
            margin_percent = pricing.get_margin_percent(product_id, cost)
            profit = pricing.get_profit(product_id, cost)

            # Background for this row
            row_rect = pygame.Rect(modal_x + 10, y_pos - 5, self.width - 20, 65)
            pygame.draw.rect(screen, (50, 50, 60), row_rect)
            pygame.draw.rect(screen, (80, 80, 90), row_rect, 1)

            # Product name
            name_surf = self.font.render(product.name, True, (255, 255, 255))
            screen.blit(name_surf, (modal_x + 20, y_pos))

            # Cost (with inflation)
            cost_surf = self.font.render(f"${cost:.2f}", True, (200, 200, 200))
            screen.blit(cost_surf, (modal_x + 180, y_pos))

            # Price adjustment section: |-| $X.XX |+|
            price_section_x = modal_x + 260
            btn_size = 25
            btn_y = y_pos - 2

            # - Button (left)
            btn_minus = pygame.Rect(price_section_x, btn_y, btn_size, btn_size)
            is_minus_hover = btn_minus.collidepoint(mx, my)
            minus_bg = (140, 100, 100) if is_minus_hover else (100, 80, 80)
            pygame.draw.rect(screen, minus_bg, btn_minus)
            pygame.draw.rect(screen, (150, 150, 150), btn_minus, 1)
            minus_label = self.font.render("-", True, (255, 255, 255))
            minus_rect = minus_label.get_rect(center=btn_minus.center)
            screen.blit(minus_label, minus_rect)

            # Current selling price (center)
            price_surf = self.font.render(f"${current_price:.2f}", True, (255, 220, 100))
            price_x = price_section_x + btn_size + 10
            screen.blit(price_surf, (price_x, y_pos))

            # + Button (right)
            price_width = price_surf.get_width()
            btn_plus = pygame.Rect(price_x + price_width + 10, btn_y, btn_size, btn_size)
            is_plus_hover = btn_plus.collidepoint(mx, my)
            plus_bg = (100, 140, 100) if is_plus_hover else (80, 100, 80)
            pygame.draw.rect(screen, plus_bg, btn_plus)
            pygame.draw.rect(screen, (150, 150, 150), btn_plus, 1)
            plus_label = self.font.render("+", True, (255, 255, 255))
            plus_rect = plus_label.get_rect(center=btn_plus.center)
            screen.blit(plus_label, plus_rect)

            # Margin display on single line: 100% (+$0.50)
            margin_color = pricing.get_margin_color(margin_percent)
            margin_text = f"{margin_percent:.0f}% (+${profit:.2f})"
            margin_surf = self.font.render(margin_text, True, margin_color)
            screen.blit(margin_surf, (modal_x + 440, y_pos))

            visible_index += 1

        # Footer info
        footer_y = modal_y + self.height - 40
        info_text = "Utilisez les boutons +/- pour ajuster les prix de vente"
        info_surf = self.font.render(info_text, True, (150, 150, 150))
        screen.blit(info_surf, (modal_x + 20, footer_y))
