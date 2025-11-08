from .finance_stats import FinanceStatsTracker


class Economy:
    def __init__(self):
        self.cash = 10000  # Starting cash

        # Park entrance pricing
        self.park_entrance_fee = 50  # Default entrance fee ($50)
        self.entrance_revenue = 0  # Total revenue from entrance fees
        self.guests_refused = 0  # Guests refused due to insufficient budget

        # Financial statistics tracker
        self.stats_tracker = FinanceStatsTracker()

        # Track consecutive days with negative cash (for game over)
        self.negative_cash_days = 0

    def add_expense(self, amt):
        """Add an expense (reduces cash)"""
        self.cash -= amt
        self.stats_tracker.add_expense(amt)

    def add_income(self, amt):
        """Add income (increases cash)"""
        self.cash += amt
        self.stats_tracker.add_revenue(amt)

    def collect_entrance_fee(self, amount):
        """Collect entrance fee from a guest"""
        self.cash += amount
        self.entrance_revenue += amount
        self.stats_tracker.add_revenue(amount)

    def set_entrance_fee(self, amount):
        """Set the park entrance fee"""
        self.park_entrance_fee = max(5, min(300, amount))  # Clamp between $5 and $300

    def start_new_day(self, day: int):
        """
        Called at the start of each new day (midnight in-game).
        Updates financial tracking and checks for negative cash.
        """
        self.stats_tracker.start_new_day(day)

        # Track negative cash days for game over condition
        if self.cash < 0:
            self.negative_cash_days += 1
        else:
            self.negative_cash_days = 0  # Reset if back to positive

    def should_game_over(self) -> bool:
        """Check if game over condition is met (90 consecutive days with negative cash)"""
        return self.negative_cash_days >= 90

    def tick(self):
        pass
