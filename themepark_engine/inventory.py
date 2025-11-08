"""
Inventory Management System
Handles global stock, ordering, delivery, and inflation for theme park shops
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
import random


@dataclass
class ProductDef:
    """Definition of a purchasable product"""
    id: str
    name: str
    base_cost: float  # Base wholesale cost per unit (affected by inflation)
    category: str  # "food", "drink", "souvenir"
    used_by_shops: List[str]  # List of shop IDs that sell this product


@dataclass
class PendingOrder:
    """An order waiting for delivery"""
    product_id: str
    quantity: int
    total_cost: float
    delivery_days: int  # Total days needed for delivery
    days_remaining: int  # Days left until delivery
    order_year: int
    order_month: int
    order_day: int

    def tick_day(self) -> bool:
        """Advance by one day. Returns True if order is delivered."""
        self.days_remaining -= 1
        return self.days_remaining <= 0


class InventoryManager:
    """Manages global inventory, orders, and inflation"""

    def __init__(self, products: Dict[str, ProductDef]):
        self.products = products  # {product_id: ProductDef}
        self.stock: Dict[str, int] = {}  # {product_id: quantity}
        self.pending_orders: List[PendingOrder] = []

        # Inflation tracking
        self.inflation_rate = 1.0  # Cumulative multiplier (starts at 1.0 = 100%)
        self.last_inflation_year = None

        # Initialize stock to 0 for all products
        for product_id in self.products:
            self.stock[product_id] = 0

    def get_stock(self, product_id: str) -> int:
        """Get current stock for a product"""
        return self.stock.get(product_id, 0)

    def has_stock(self, product_id: str) -> bool:
        """Check if product has any stock"""
        return self.get_stock(product_id) > 0

    def consume_stock(self, product_id: str, quantity: int = 1) -> bool:
        """
        Consume stock for a sale.
        Returns True if stock was available, False if out of stock.
        """
        if self.get_stock(product_id) >= quantity:
            self.stock[product_id] -= quantity
            return True
        return False

    def add_stock(self, product_id: str, quantity: int):
        """Add stock (e.g., from a delivered order)"""
        if product_id not in self.stock:
            self.stock[product_id] = 0
        self.stock[product_id] += quantity

    def get_current_cost(self, product_id: str) -> float:
        """Get current cost per unit (with inflation applied)"""
        product = self.products.get(product_id)
        if not product:
            return 0.0
        return product.base_cost * self.inflation_rate

    def calculate_order_price(self, product_id: str, quantity: int) -> tuple[float, int, float]:
        """
        Calculate order price with bulk discount and delivery time.

        Returns: (total_cost, delivery_days, discount_percent)

        Pricing tiers:
        - 1-50: 100% price, 1-3 days
        - 51-100: -10%, 4-7 days
        - 101-200: -15%, 8-14 days
        - 201-500: -20%, 15-21 days
        - 501+: -25%, 22-30 days
        """
        base_cost = self.get_current_cost(product_id)

        if quantity <= 50:
            discount = 0.0
            delivery_days = random.randint(1, 3)
        elif quantity <= 100:
            discount = 0.10
            delivery_days = random.randint(4, 7)
        elif quantity <= 200:
            discount = 0.15
            delivery_days = random.randint(8, 14)
        elif quantity <= 500:
            discount = 0.20
            delivery_days = random.randint(15, 21)
        else:
            discount = 0.25
            delivery_days = random.randint(22, 30)

        discounted_cost = base_cost * (1.0 - discount)
        total_cost = discounted_cost * quantity

        return (total_cost, delivery_days, discount * 100)

    def place_order(self, product_id: str, quantity: int, year: int, month: int, day: int,
                    delivery_days: int = None) -> Optional[PendingOrder]:
        """
        Place an order for a product.

        Args:
            product_id: ID of the product to order
            quantity: Number of units to order
            year, month, day: Order date
            delivery_days: Optional fixed delivery time (if None, will calculate randomly)

        Returns the PendingOrder if successful, None if product doesn't exist.
        """
        if product_id not in self.products:
            return None

        total_cost, calculated_delivery_days, _ = self.calculate_order_price(product_id, quantity)

        # Use provided delivery_days if given, otherwise use calculated (random) one
        final_delivery_days = delivery_days if delivery_days is not None else calculated_delivery_days

        order = PendingOrder(
            product_id=product_id,
            quantity=quantity,
            total_cost=total_cost,
            delivery_days=final_delivery_days,
            days_remaining=final_delivery_days,
            order_year=year,
            order_month=month,
            order_day=day
        )

        self.pending_orders.append(order)
        return order

    def tick_day(self):
        """
        Called once per game day to advance pending orders.
        Returns list of delivered orders (to add stock).
        """
        delivered = []
        remaining = []

        for order in self.pending_orders:
            if order.tick_day():
                # Order delivered!
                self.add_stock(order.product_id, order.quantity)
                delivered.append(order)
            else:
                remaining.append(order)

        self.pending_orders = remaining
        return delivered

    def apply_annual_inflation(self, year: int):
        """
        Apply annual inflation (called once per year in January).
        Increases all base costs by 1-3%.
        """
        if self.last_inflation_year == year:
            return  # Already applied this year

        # Random inflation between 1% and 3%
        annual_increase = random.uniform(0.01, 0.03)
        self.inflation_rate *= (1.0 + annual_increase)
        self.last_inflation_year = year

    def get_product_for_shop(self, shop_id: str) -> Optional[str]:
        """
        Find which product a shop uses.
        Returns product_id or None.
        """
        for product_id, product in self.products.items():
            if shop_id in product.used_by_shops:
                return product_id
        return None

    def is_shop_out_of_stock(self, shop_id: str) -> bool:
        """Check if a shop's product is out of stock"""
        product_id = self.get_product_for_shop(shop_id)
        if not product_id:
            return False
        return not self.has_stock(product_id)

    # Serialization for save/load
    def to_dict(self) -> dict:
        """Convert to dictionary for saving"""
        return {
            'stock': self.stock,
            'inflation_rate': self.inflation_rate,
            'last_inflation_year': self.last_inflation_year,
            'pending_orders': [
                {
                    'product_id': o.product_id,
                    'quantity': o.quantity,
                    'total_cost': o.total_cost,
                    'delivery_days': o.delivery_days,
                    'days_remaining': o.days_remaining,
                    'order_year': o.order_year,
                    'order_month': o.order_month,
                    'order_day': o.order_day
                }
                for o in self.pending_orders
            ]
        }

    def from_dict(self, data: dict):
        """Load from dictionary"""
        self.stock = data.get('stock', {})
        self.inflation_rate = data.get('inflation_rate', 1.0)
        self.last_inflation_year = data.get('last_inflation_year', None)

        # Restore pending orders
        self.pending_orders = []
        for order_data in data.get('pending_orders', []):
            order = PendingOrder(**order_data)
            self.pending_orders.append(order)
