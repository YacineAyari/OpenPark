
class Economy:
    def __init__(self):
        self.cash = 10000  # Starting cash

        # Park entrance pricing
        self.park_entrance_fee = 50  # Default entrance fee ($50)
        self.entrance_revenue = 0  # Total revenue from entrance fees
        self.guests_refused = 0  # Guests refused due to insufficient budget

    def add_expense(self, amt):
        """Add an expense (reduces cash)"""
        self.cash -= amt

    def add_income(self, amt):
        """Add income (increases cash)"""
        self.cash += amt

    def collect_entrance_fee(self, amount):
        """Collect entrance fee from a guest"""
        self.cash += amount
        self.entrance_revenue += amount

    def set_entrance_fee(self, amount):
        """Set the park entrance fee"""
        self.park_entrance_fee = max(5, min(300, amount))  # Clamp between $5 and $300

    def tick(self):
        pass
