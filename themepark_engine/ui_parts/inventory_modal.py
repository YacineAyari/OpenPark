"""
Inventory Modal UI
Displays stock levels, pending orders, and allows player to place new orders
"""

import pygame
from typing import Optional, List
from ..inventory import InventoryManager, PendingOrder


class InventoryModal:
    """Modal for inventory management and ordering"""

    def __init__(self, font: pygame.font.Font):
        self.font = font
        self.visible = False
        self.active_tab = "stock"  # "stock" or "orders"

        # Order form state
        self.selected_product_id: Optional[str] = None
        self.order_quantity = 100  # Default order quantity
        self.slider_dragging = False  # Is quantity slider being dragged

        # Modal dimensions
        self.width = 700
        self.height = 500
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

    def handle_event(self, event: pygame.event.Event, inventory: InventoryManager,
                     economy, year: int, month: int, day: int, shops: list = None) -> bool:
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
            # Keep ESC and I to close modal
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_i:
                self.hide()
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mx, my = event.pos

                # Click outside modal closes it
                if not (modal_x <= mx <= modal_x + self.width and modal_y <= my <= modal_y + self.height):
                    self.hide()
                    return True

                # Handle tab clicks
                tab_stock_rect = pygame.Rect(modal_x + 20, modal_y + 50, 100, 30)
                tab_orders_rect = pygame.Rect(modal_x + 130, modal_y + 50, 100, 30)

                if tab_stock_rect.collidepoint(mx, my):
                    self.active_tab = "stock"
                    return True
                elif tab_orders_rect.collidepoint(mx, my):
                    self.active_tab = "orders"
                    return True

                # Handle product "Order" button clicks in stock tab
                if self.active_tab == "stock" and shops:
                    product_list_y = modal_y + 100
                    for i, (product_id, product) in enumerate(inventory.products.items()):
                        # Check if player has any shops that use this product
                        has_shop = self._has_shop_for_product(product_id, product, shops)
                        if not has_shop:
                            continue  # Skip if no shops placed

                        button_rect = pygame.Rect(modal_x + 490, product_list_y + i * 50 + 5, 70, 30)
                        if button_rect.collidepoint(mx, my):
                            self.selected_product_id = product_id
                            self.order_quantity = 100
                            return True

                # Handle order form slider and buttons
                if self.selected_product_id:
                    form_width = 400
                    form_height = 250
                    form_x = modal_x + (self.width - form_width) // 2
                    form_y = modal_y + (self.height - form_height) // 2

                    # Quantity slider
                    slider_x = form_x + 120
                    slider_y = form_y + 60
                    slider_width = 200
                    slider_height = 20
                    slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)

                    if slider_rect.collidepoint(mx, my):
                        # Calculate quantity from mouse position on slider
                        ratio = (mx - slider_x) / slider_width
                        ratio = max(0, min(1, ratio))
                        self.order_quantity = int(10 + ratio * 990)  # 10 to 1000
                        self.slider_dragging = True
                        return True

                    # Confirm button
                    confirm_rect = pygame.Rect(form_x + 80, form_y + 210, 120, 30)
                    if confirm_rect.collidepoint(mx, my):
                        total_cost, _, _ = inventory.calculate_order_price(self.selected_product_id, self.order_quantity)
                        if economy.cash >= total_cost:
                            inventory.place_order(self.selected_product_id, self.order_quantity, year, month, day)
                            economy.subtract_expense(total_cost)
                            self.selected_product_id = None
                            self.order_quantity = 100
                        return True

                    # Cancel button
                    cancel_rect = pygame.Rect(form_x + 220, form_y + 210, 120, 30)
                    if cancel_rect.collidepoint(mx, my):
                        self.selected_product_id = None
                        self.slider_dragging = False
                        return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.slider_dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.slider_dragging and self.selected_product_id:
                # Update quantity while dragging slider
                form_width = 400
                form_x = modal_x + (self.width - form_width) // 2
                slider_x = form_x + 120
                slider_width = 200

                mx = event.pos[0]
                ratio = (mx - slider_x) / slider_width
                ratio = max(0, min(1, ratio))
                self.order_quantity = int(10 + ratio * 990)  # 10 to 1000
                return True

        return False

    def _has_shop_for_product(self, product_id: str, product, shops: list) -> bool:
        """Check if player has placed any shop that uses this product"""
        for shop_id in product.used_by_shops:
            for shop in shops:
                if shop.defn.id == shop_id:
                    return True
        return False

    def draw(self, screen: pygame.Surface, inventory: InventoryManager, economy,
             year: int, month: int, day: int, shops: list = None):
        """Draw the inventory modal"""
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
        title_surf = self.font.render("Inventory & Orders", True, (255, 255, 255))
        screen.blit(title_surf, (modal_x + self.padding, modal_y + self.padding))

        # Tabs
        tab_stock_color = (80, 120, 180) if self.active_tab == "stock" else (60, 60, 70)
        tab_orders_color = (80, 120, 180) if self.active_tab == "orders" else (60, 60, 70)

        pygame.draw.rect(screen, tab_stock_color, (modal_x + 20, modal_y + 50, 100, 30))
        pygame.draw.rect(screen, tab_orders_color, (modal_x + 130, modal_y + 50, 100, 30))

        stock_text = self.font.render("[1] Stock", True, (255, 255, 255))
        orders_text = self.font.render("[2] Orders", True, (255, 255, 255))
        screen.blit(stock_text, (modal_x + 30, modal_y + 58))
        screen.blit(orders_text, (modal_x + 140, modal_y + 58))

        # Content area
        if self.active_tab == "stock":
            self._draw_stock_tab(screen, modal_x, modal_y, inventory, shops)
        else:
            self._draw_orders_tab(screen, modal_x, modal_y, inventory, year, month, day)

        # Order form (if product selected)
        if self.selected_product_id:
            self._draw_order_form(screen, modal_x, modal_y, inventory, economy)

        # Instructions
        inst_y = modal_y + self.height - 30
        inst_text = "[I/ESC] Close | Click to interact"
        inst_surf = self.font.render(inst_text, True, (180, 180, 180))
        screen.blit(inst_surf, (modal_x + self.padding, inst_y))

    def _draw_stock_tab(self, screen: pygame.Surface, modal_x: int, modal_y: int,
                        inventory: InventoryManager, shops: list = None):
        """Draw stock overview tab"""
        y = modal_y + 100

        # Header
        header = self.font.render("Product", True, (200, 200, 200))
        screen.blit(header, (modal_x + 30, y - 25))
        header2 = self.font.render("Stock", True, (200, 200, 200))
        screen.blit(header2, (modal_x + 250, y - 25))
        header3 = self.font.render("Cost/Unit", True, (200, 200, 200))
        screen.blit(header3, (modal_x + 350, y - 25))
        header4 = self.font.render("Action", True, (200, 200, 200))
        screen.blit(header4, (modal_x + 480, y - 25))

        # Product list
        for i, (product_id, product) in enumerate(inventory.products.items()):
            stock = inventory.get_stock(product_id)
            cost_per_unit = inventory.get_current_cost(product_id)

            # Check if player has any shops for this product
            has_shop = self._has_shop_for_product(product_id, product, shops) if shops else False

            # Background highlight
            if i % 2 == 0:
                pygame.draw.rect(screen, (50, 50, 60), (modal_x + 20, y, 660, 40))

            # Color tint for products without shops
            text_color = (255, 255, 255) if has_shop else (120, 120, 130)

            # Stock color coding
            if stock == 0:
                stock_color = (255, 80, 80) if has_shop else (120, 40, 40)
                status_icon = "⚠️"
            elif stock < 50:
                stock_color = (255, 200, 80) if has_shop else (120, 100, 40)
                status_icon = "⚠"
            else:
                stock_color = (80, 255, 120) if has_shop else (40, 120, 60)
                status_icon = "✓"

            # Product name
            name_surf = self.font.render(f"{status_icon} {product.name}", True, text_color)
            screen.blit(name_surf, (modal_x + 30, y + 10))

            # Stock amount
            stock_surf = self.font.render(str(stock), True, stock_color)
            screen.blit(stock_surf, (modal_x + 260, y + 10))

            # Cost per unit
            cost_surf = self.font.render(f"${cost_per_unit:.2f}", True, text_color)
            screen.blit(cost_surf, (modal_x + 360, y + 10))

            # Order button (only if shop exists)
            if has_shop:
                button_rect = pygame.Rect(modal_x + 490, y + 5, 70, 30)
                pygame.draw.rect(screen, (80, 150, 80), button_rect)
                pygame.draw.rect(screen, (120, 200, 120), button_rect, 2)
                order_text = self.font.render("Order", True, (255, 255, 255))
                screen.blit(order_text, (modal_x + 500, y + 12))
            else:
                # Show "No shop" message instead
                no_shop_text = self.font.render("No shop", True, (150, 150, 150))
                screen.blit(no_shop_text, (modal_x + 490, y + 12))

            y += 50

        # Inflation info
        inflation_percent = (inventory.inflation_rate - 1.0) * 100
        inflation_text = f"Total Inflation: {inflation_percent:.1f}%"
        inflation_surf = self.font.render(inflation_text, True, (255, 200, 100))
        screen.blit(inflation_surf, (modal_x + 30, modal_y + self.height - 70))

    def _draw_orders_tab(self, screen: pygame.Surface, modal_x: int, modal_y: int,
                         inventory: InventoryManager, year: int, month: int, day: int):
        """Draw pending orders tab with visual delivery progress"""
        y = modal_y + 100

        if not inventory.pending_orders:
            no_orders = self.font.render("No pending orders", True, (150, 150, 150))
            screen.blit(no_orders, (modal_x + 30, y))
            return

        # Header
        header = self.font.render("Product", True, (200, 200, 200))
        screen.blit(header, (modal_x + 30, y - 25))
        header2 = self.font.render("Qty", True, (200, 200, 200))
        screen.blit(header2, (modal_x + 200, y - 25))
        header3 = self.font.render("Cost", True, (200, 200, 200))
        screen.blit(header3, (modal_x + 260, y - 25))
        header4 = self.font.render("Delivery Progress", True, (200, 200, 200))
        screen.blit(header4, (modal_x + 350, y - 25))

        # Order list
        for i, order in enumerate(inventory.pending_orders):
            product = inventory.products.get(order.product_id)
            product_name = product.name if product else order.product_id

            # Background
            if i % 2 == 0:
                pygame.draw.rect(screen, (50, 50, 60), (modal_x + 20, y, 660, 60))

            # Product name
            name_surf = self.font.render(product_name, True, (255, 255, 255))
            screen.blit(name_surf, (modal_x + 30, y + 8))

            # Quantity
            qty_surf = self.font.render(f"{order.quantity}x", True, (200, 200, 200))
            screen.blit(qty_surf, (modal_x + 205, y + 8))

            # Cost
            cost_surf = self.font.render(f"${order.total_cost:.2f}", True, (255, 200, 100))
            screen.blit(cost_surf, (modal_x + 265, y + 8))

            # Progress bar
            progress_ratio = 1.0 - (order.days_remaining / order.delivery_days)
            bar_width = 250
            bar_height = 20
            bar_x = modal_x + 360
            bar_y = y + 10

            # Background bar
            pygame.draw.rect(screen, (60, 60, 70), (bar_x, bar_y, bar_width, bar_height))

            # Progress fill
            fill_width = int(bar_width * progress_ratio)
            if fill_width > 0:
                progress_color = (80, 180, 255) if order.days_remaining > 0 else (80, 255, 120)
                pygame.draw.rect(screen, progress_color, (bar_x, bar_y, fill_width, bar_height))

            # Border
            pygame.draw.rect(screen, (120, 120, 140), (bar_x, bar_y, bar_width, bar_height), 2)

            # Days remaining text
            if order.days_remaining > 0:
                days_text = f"🚚 {order.days_remaining}/{order.delivery_days} days"
                days_color = (255, 255, 255)
            else:
                days_text = "✓ Delivered!"
                days_color = (120, 255, 150)

            days_surf = self.font.render(days_text, True, days_color)
            screen.blit(days_surf, (bar_x + 5, bar_y + 3))

            y += 65

    def _draw_order_form(self, screen: pygame.Surface, modal_x: int, modal_y: int,
                         inventory: InventoryManager, economy):
        """Draw order form overlay"""
        form_width = 400
        form_height = 250
        form_x = modal_x + (self.width - form_width) // 2
        form_y = modal_y + (self.height - form_height) // 2

        # Background
        pygame.draw.rect(screen, (30, 30, 40), (form_x, form_y, form_width, form_height))
        pygame.draw.rect(screen, (100, 150, 200), (form_x, form_y, form_width, form_height), 3)

        product = inventory.products[self.selected_product_id]

        # Title
        title = self.font.render(f"Order {product.name}", True, (255, 255, 255))
        screen.blit(title, (form_x + 20, form_y + 20))

        # Quantity selector with slider
        qty_label = self.font.render("Quantity:", True, (200, 200, 200))
        screen.blit(qty_label, (form_x + 20, form_y + 60))

        qty_value = self.font.render(f"{self.order_quantity} units", True, (255, 255, 100))
        screen.blit(qty_value, (form_x + 120, form_y + 60))

        # Slider bar (10 to 1000 range)
        slider_x = form_x + 120
        slider_y = form_y + 85
        slider_width = 200
        slider_height = 20

        # Slider background
        pygame.draw.rect(screen, (60, 60, 70), (slider_x, slider_y, slider_width, slider_height))

        # Slider fill (current value)
        fill_ratio = (self.order_quantity - 10) / 990  # 10 to 1000
        fill_width = int(slider_width * fill_ratio)
        if fill_width > 0:
            pygame.draw.rect(screen, (80, 150, 255), (slider_x, slider_y, fill_width, slider_height))

        # Slider border
        pygame.draw.rect(screen, (120, 120, 140), (slider_x, slider_y, slider_width, slider_height), 2)

        # Slider handle
        handle_x = slider_x + fill_width
        handle_y = slider_y
        pygame.draw.circle(screen, (150, 200, 255), (handle_x, handle_y + slider_height // 2), 8)
        pygame.draw.circle(screen, (200, 220, 255), (handle_x, handle_y + slider_height // 2), 8, 2)

        # Range labels
        min_label = self.font.render("10", True, (150, 150, 150))
        max_label = self.font.render("1000", True, (150, 150, 150))
        screen.blit(min_label, (slider_x - 20, slider_y + 3))
        screen.blit(max_label, (slider_x + slider_width + 5, slider_y + 3))

        # Price calculation
        total_cost, delivery_days, discount_percent = inventory.calculate_order_price(
            self.selected_product_id, self.order_quantity
        )

        cost_label = self.font.render("Total Cost:", True, (200, 200, 200))
        screen.blit(cost_label, (form_x + 20, form_y + 110))

        cost_value = self.font.render(f"${total_cost:.2f}", True, (255, 200, 100))
        screen.blit(cost_value, (form_x + 120, form_y + 110))

        if discount_percent > 0:
            discount_text = self.font.render(f"(-{discount_percent:.0f}% bulk discount)", True, (120, 255, 150))
            screen.blit(discount_text, (form_x + 120, form_y + 130))

        # Delivery time
        delivery_label = self.font.render("Delivery:", True, (200, 200, 200))
        screen.blit(delivery_label, (form_x + 20, form_y + 155))

        delivery_value = self.font.render(f"{delivery_days} days", True, (150, 200, 255))
        screen.blit(delivery_value, (form_x + 120, form_y + 155))

        # Cash check
        cash_available = economy.cash
        can_afford = cash_available >= total_cost

        cash_text = f"Cash: ${cash_available:.2f}"
        cash_color = (80, 255, 120) if can_afford else (255, 80, 80)
        cash_surf = self.font.render(cash_text, True, cash_color)
        screen.blit(cash_surf, (form_x + 20, form_y + 180))

        # Buttons (clickable)
        confirm_rect = pygame.Rect(form_x + 80, form_y + 210, 120, 30)
        cancel_rect = pygame.Rect(form_x + 220, form_y + 210, 120, 30)

        if can_afford:
            pygame.draw.rect(screen, (80, 180, 80), confirm_rect)
            pygame.draw.rect(screen, (120, 220, 120), confirm_rect, 2)
            confirm_text = "Confirm"
            confirm_color = (255, 255, 255)
        else:
            pygame.draw.rect(screen, (100, 50, 50), confirm_rect)
            pygame.draw.rect(screen, (150, 80, 80), confirm_rect, 2)
            confirm_text = "No funds"
            confirm_color = (200, 200, 200)

        confirm_surf = self.font.render(confirm_text, True, confirm_color)
        text_rect = confirm_surf.get_rect(center=confirm_rect.center)
        screen.blit(confirm_surf, text_rect)

        pygame.draw.rect(screen, (80, 80, 100), cancel_rect)
        pygame.draw.rect(screen, (120, 120, 140), cancel_rect, 2)
        cancel_surf = self.font.render("Cancel", True, (255, 255, 255))
        text_rect = cancel_surf.get_rect(center=cancel_rect.center)
        screen.blit(cancel_surf, text_rect)
