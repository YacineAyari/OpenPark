"""
Inventory Modal UI
Displays stock levels, pending orders, and allows player to place new orders
"""

import pygame
from typing import Optional, List
from ..inventory import InventoryManager, PendingOrder
from .. import assets


class InventoryModal:
    """Modal for inventory management and ordering"""

    def __init__(self, font: pygame.font.Font):
        self.font = font
        self.visible = False
        self.active_tab = "stock"  # "stock" or "orders"

        # Order form state
        self.selected_product_id: Optional[str] = None
        self.order_quantity = 100  # Default order quantity
        self.cached_delivery_days = 0  # Cache delivery days to prevent random changes
        self.slider_dragging = False  # Is quantity slider being dragged

        # Modal dimensions
        self.width = 700
        self.height = 500
        self.padding = 20

        # Load package sprite for delivery animation
        self.package_sprite = assets.load_image("1F4E6.png")  # Package from OpenMoji

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

                # Close button (X) in top-right corner
                close_button_size = 30
                close_button_x = modal_x + self.width - close_button_size - 10
                close_button_y = modal_y + 10
                close_button_rect = pygame.Rect(close_button_x, close_button_y, close_button_size, close_button_size)
                if close_button_rect.collidepoint(mx, my):
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
                    visible_index = 0
                    for product_id, product in inventory.products.items():
                        # Check if player has any shops that use this product
                        has_shop = self._has_shop_for_product(product_id, product, shops)
                        if not has_shop:
                            continue  # Skip if no shops placed

                        button_rect = pygame.Rect(modal_x + 490, product_list_y + visible_index * 50 + 5, 70, 30)
                        if button_rect.collidepoint(mx, my):
                            self.selected_product_id = product_id
                            self.order_quantity = 100
                            # Calculate and cache delivery days for this quantity
                            _, self.cached_delivery_days, _ = inventory.calculate_order_price(product_id, 100)
                            return True
                        visible_index += 1

                # Handle order form slider and buttons
                if self.selected_product_id:
                    form_width = 400
                    form_height = 250
                    form_x = modal_x + (self.width - form_width) // 2
                    form_y = modal_y + (self.height - form_height) // 2

                    # Quantity slider (must match coordinates in _draw_order_form!)
                    slider_x = form_x + 120
                    slider_y = form_y + 85  # Fixed: was 60, but draw uses 85
                    slider_width = 200
                    slider_height = 20
                    slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)

                    if slider_rect.collidepoint(mx, my):
                        # Calculate quantity from mouse position on slider
                        ratio = (mx - slider_x) / slider_width
                        ratio = max(0, min(1, ratio))
                        new_quantity = int(10 + ratio * 990)  # 10 to 1000

                        # Only recalculate delivery if quantity changed significantly (different tier)
                        if self._get_quantity_tier(new_quantity) != self._get_quantity_tier(self.order_quantity):
                            _, self.cached_delivery_days, _ = inventory.calculate_order_price(self.selected_product_id, new_quantity)

                        self.order_quantity = new_quantity
                        self.slider_dragging = True
                        return True

                    # Confirm button
                    confirm_rect = pygame.Rect(form_x + 80, form_y + 210, 120, 30)
                    if confirm_rect.collidepoint(mx, my):
                        total_cost, _, _ = inventory.calculate_order_price(self.selected_product_id, self.order_quantity)
                        if economy.cash >= total_cost:
                            # Pass cached delivery days to prevent random recalculation
                            inventory.place_order(self.selected_product_id, self.order_quantity, year, month, day,
                                                  delivery_days=self.cached_delivery_days)
                            economy.add_expense(total_cost)  # Deduct cost from cash
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
                new_quantity = int(10 + ratio * 990)  # 10 to 1000

                # Only recalculate delivery if quantity tier changed
                if self._get_quantity_tier(new_quantity) != self._get_quantity_tier(self.order_quantity):
                    _, self.cached_delivery_days, _ = inventory.calculate_order_price(self.selected_product_id, new_quantity)

                self.order_quantity = new_quantity
                return True

        return False

    def _get_quantity_tier(self, quantity: int) -> int:
        """
        Get pricing tier for a quantity (to detect when to recalculate delivery).
        Returns tier number (0-4).
        """
        if quantity <= 50:
            return 0
        elif quantity <= 100:
            return 1
        elif quantity <= 200:
            return 2
        elif quantity <= 500:
            return 3
        else:
            return 4

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

        # Product list (only show products with shops placed)
        visible_index = 0
        for product_id, product in inventory.products.items():
            # Check if player has any shops for this product
            has_shop = self._has_shop_for_product(product_id, product, shops) if shops else False

            # Skip products without shops (don't display them at all)
            if not has_shop:
                continue

            stock = inventory.get_stock(product_id)
            cost_per_unit = inventory.get_current_cost(product_id)

            # Background highlight (use visible_index for alternating colors)
            if visible_index % 2 == 0:
                pygame.draw.rect(screen, (50, 50, 60), (modal_x + 20, y, 660, 40))

            # Stock color coding
            if stock == 0:
                stock_color = (255, 80, 80)
                status_icon = "⚠️"
            elif stock < 50:
                stock_color = (255, 200, 80)
                status_icon = "⚠"
            else:
                stock_color = (80, 255, 120)
                status_icon = "✓"

            # Product name
            name_surf = self.font.render(f"{status_icon} {product.name}", True, (255, 255, 255))
            screen.blit(name_surf, (modal_x + 30, y + 10))

            # Stock amount
            stock_surf = self.font.render(str(stock), True, stock_color)
            screen.blit(stock_surf, (modal_x + 260, y + 10))

            # Cost per unit
            cost_surf = self.font.render(f"${cost_per_unit:.2f}", True, (200, 200, 200))
            screen.blit(cost_surf, (modal_x + 360, y + 10))

            # Order button
            button_rect = pygame.Rect(modal_x + 490, y + 5, 70, 30)
            pygame.draw.rect(screen, (80, 150, 80), button_rect)
            pygame.draw.rect(screen, (120, 200, 120), button_rect, 2)
            order_text = self.font.render("Order", True, (255, 255, 255))
            screen.blit(order_text, (modal_x + 500, y + 12))

            y += 50
            visible_index += 1

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

            # Delivery progress with moving truck
            progress_ratio = 1.0 - (order.days_remaining / order.delivery_days)
            track_width = 250
            track_height = 30
            track_x = modal_x + 360
            track_y = y + 5

            # Draw track/road (light gray line)
            road_y = track_y + track_height // 2
            pygame.draw.line(screen, (100, 100, 110), (track_x, road_y), (track_x + track_width, road_y), 3)

            # Draw start and end markers
            pygame.draw.circle(screen, (180, 180, 190), (track_x, road_y), 5)  # Start
            pygame.draw.circle(screen, (100, 255, 120), (track_x + track_width, road_y), 5)  # End (green)

            # Draw truck position
            truck_x = track_x + int(track_width * progress_ratio)
            truck_y = road_y - 8

            if order.days_remaining > 0:
                # Scale package sprite to fit in the track
                package_size = 20  # Size for the package sprite
                package_scaled = pygame.transform.scale(self.package_sprite, (package_size, package_size))
                # Center package on position
                package_rect = package_scaled.get_rect(center=(truck_x, truck_y))
                screen.blit(package_scaled, package_rect)
            else:
                # Delivered - show checkmark at end
                check_text = "✓"
                check_surf = self.font.render(check_text, True, (120, 255, 150))
                check_rect = check_surf.get_rect(center=(truck_x, truck_y))
                screen.blit(check_surf, check_rect)

            # Days remaining text below track
            if order.days_remaining > 0:
                days_text = f"{order.days_remaining}/{order.delivery_days} days"
                days_color = (200, 200, 200)
            else:
                days_text = "Delivered!"
                days_color = (120, 255, 150)

            days_surf = self.font.render(days_text, True, days_color)
            screen.blit(days_surf, (track_x + track_width // 2 - 30, track_y + track_height + 5))

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

        # Price calculation (cost only, use cached delivery days)
        total_cost, _, discount_percent = inventory.calculate_order_price(
            self.selected_product_id, self.order_quantity
        )

        cost_label = self.font.render("Total Cost:", True, (200, 200, 200))
        screen.blit(cost_label, (form_x + 20, form_y + 110))

        cost_value = self.font.render(f"${total_cost:.2f}", True, (255, 200, 100))
        screen.blit(cost_value, (form_x + 120, form_y + 110))

        if discount_percent > 0:
            discount_text = self.font.render(f"(-{discount_percent:.0f}% bulk discount)", True, (120, 255, 150))
            screen.blit(discount_text, (form_x + 120, form_y + 130))

        # Delivery time (use cached value to prevent random changes)
        delivery_label = self.font.render("Delivery:", True, (200, 200, 200))
        screen.blit(delivery_label, (form_x + 20, form_y + 155))

        delivery_value = self.font.render(f"{self.cached_delivery_days} days", True, (150, 200, 255))
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
