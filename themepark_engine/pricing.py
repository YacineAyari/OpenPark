"""
Pricing Management System
Handles product selling prices with margin calculations
"""

from typing import Dict


class PricingManager:
    """Manages selling prices for products"""

    def __init__(self):
        # Product selling prices {product_id: price}
        self.prices: Dict[str, float] = {}

        # Price multipliers for recommendations
        self.MIN_MARGIN = 1.1  # 10% minimum margin
        self.RECOMMENDED_MARGIN = 2.0  # 100% recommended margin
        self.MAX_MARGIN = 5.0  # 500% maximum margin

    def get_price(self, product_id: str, default_cost: float = 0.0) -> float:
        """
        Get selling price for a product.
        If not set, returns recommended price (cost × 2.0)
        """
        if product_id in self.prices:
            return self.prices[product_id]
        # Default to recommended margin
        return default_cost * self.RECOMMENDED_MARGIN

    def set_price(self, product_id: str, price: float):
        """Set selling price for a product"""
        self.prices[product_id] = max(0.0, price)

    def get_margin_percent(self, product_id: str, cost: float) -> float:
        """Calculate profit margin percentage"""
        price = self.get_price(product_id, cost)
        if cost <= 0:
            return 0.0
        margin = ((price - cost) / cost) * 100
        return margin

    def get_profit(self, product_id: str, cost: float) -> float:
        """Calculate profit per unit"""
        price = self.get_price(product_id, cost)
        return price - cost

    def get_min_price(self, cost: float) -> float:
        """Get minimum recommended price (cost + 10%)"""
        return cost * self.MIN_MARGIN

    def get_max_price(self, cost: float) -> float:
        """Get maximum recommended price (cost × 5)"""
        return cost * self.MAX_MARGIN

    def get_recommended_price(self, cost: float) -> float:
        """Get recommended price (cost × 2)"""
        return cost * self.RECOMMENDED_MARGIN

    def initialize_product(self, product_id: str, cost: float):
        """Initialize a product with recommended price if not already set"""
        if product_id not in self.prices:
            self.prices[product_id] = self.get_recommended_price(cost)

    def get_margin_color(self, margin_percent: float) -> tuple:
        """
        Get color indicator for margin:
        - Red: < 20% (poor margin or loss)
        - Orange: 20-50% (low margin)
        - Yellow: 50-100% (acceptable)
        - Green: > 100% (good margin)
        """
        if margin_percent < 20:
            return (220, 80, 80)  # Red
        elif margin_percent < 50:
            return (220, 140, 60)  # Orange
        elif margin_percent < 100:
            return (220, 200, 80)  # Yellow
        else:
            return (100, 220, 100)  # Green

    def get_purchase_probability(self, product_id: str, cost: float) -> float:
        """
        Calculate the probability that a guest will accept the price.
        Based on the price relative to the base cost (with inflation).

        Returns probability from 0.0 (never buy) to 1.0 (always buy)

        Price tiers:
        - ≤ 2× cost: 100% acceptance (reasonable price)
        - 2-3× cost: 70-100% acceptance (acceptable but pricey)
        - 3-4× cost: 30-70% acceptance (expensive)
        - > 4× cost: 0-30% acceptance (overpriced)
        """
        price = self.get_price(product_id, cost)

        if cost <= 0:
            return 1.0  # Free or no cost tracking = always accept

        price_ratio = price / cost

        if price_ratio <= 2.0:
            # Reasonable pricing - always accept
            return 1.0
        elif price_ratio <= 3.0:
            # Acceptable but pricey - linear decline from 100% to 70%
            # ratio 2.0 → 1.0, ratio 3.0 → 0.7
            return 1.0 - (price_ratio - 2.0) * 0.3
        elif price_ratio <= 4.0:
            # Expensive - linear decline from 70% to 30%
            # ratio 3.0 → 0.7, ratio 4.0 → 0.3
            return 0.7 - (price_ratio - 3.0) * 0.4
        else:
            # Overpriced - very low acceptance, capped at 5%
            # ratio 4.0 → 0.3, ratio 5.0 → 0.15, ratio 6.0+ → 0.05
            acceptance = max(0.05, 0.3 - (price_ratio - 4.0) * 0.15)
            return acceptance

    # Serialization for save/load
    def to_dict(self) -> dict:
        """Convert to dictionary for saving"""
        return {
            'prices': self.prices
        }

    def from_dict(self, data: dict):
        """Load from dictionary"""
        self.prices = data.get('prices', {})
