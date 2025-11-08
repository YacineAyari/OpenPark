"""
Financial Statistics Tracker
Tracks daily revenue and expenses with historical data
"""

from typing import List, Dict
from collections import deque


class DailyFinance:
    """Represents financial data for a single day"""

    def __init__(self, day: int, revenue: float = 0.0, expenses: float = 0.0):
        self.day = day
        self.revenue = revenue
        self.expenses = expenses

    @property
    def profit(self) -> float:
        """Calculate profit (revenue - expenses)"""
        return self.revenue - self.expenses

    def to_dict(self) -> dict:
        """Convert to dictionary for saving"""
        return {
            'day': self.day,
            'revenue': self.revenue,
            'expenses': self.expenses
        }

    @staticmethod
    def from_dict(data: dict) -> 'DailyFinance':
        """Create from dictionary"""
        return DailyFinance(
            data.get('day', 0),
            data.get('revenue', 0.0),
            data.get('expenses', 0.0)
        )


class MonthlyFinance:
    """Represents aggregated financial data for a month"""

    def __init__(self, month: int, revenue: float = 0.0, expenses: float = 0.0):
        self.month = month
        self.revenue = revenue
        self.expenses = expenses

    @property
    def profit(self) -> float:
        """Calculate profit (revenue - expenses)"""
        return self.revenue - self.expenses

    def to_dict(self) -> dict:
        """Convert to dictionary for saving"""
        return {
            'month': self.month,
            'revenue': self.revenue,
            'expenses': self.expenses
        }

    @staticmethod
    def from_dict(data: dict) -> 'MonthlyFinance':
        """Create from dictionary"""
        return MonthlyFinance(
            data.get('month', 0),
            data.get('revenue', 0.0),
            data.get('expenses', 0.0)
        )


class FinanceStatsTracker:
    """Tracks financial history and provides statistics"""

    def __init__(self):
        # Current day tracking
        self.current_day = 0
        self.today_revenue = 0.0
        self.today_expenses = 0.0

        # Historical data (365 days max)
        self.daily_history: deque[DailyFinance] = deque(maxlen=365)

        # Monthly aggregated data (12 months max)
        self.monthly_history: deque[MonthlyFinance] = deque(maxlen=12)

    def start_new_day(self, day: int):
        """
        Start a new day - save previous day's data and reset counters.
        Called at midnight in-game.
        """
        # Save previous day's data if we had any activity
        if self.current_day > 0:
            daily_data = DailyFinance(self.current_day, self.today_revenue, self.today_expenses)
            self.daily_history.append(daily_data)

            # Update monthly aggregation
            self._update_monthly_stats(self.current_day, self.today_revenue, self.today_expenses)

        # Reset for new day
        self.current_day = day
        self.today_revenue = 0.0
        self.today_expenses = 0.0

    def add_revenue(self, amount: float):
        """Add revenue for today"""
        self.today_revenue += amount

    def add_expense(self, amount: float):
        """Add expense for today"""
        self.today_expenses += amount

    def _update_monthly_stats(self, day: int, revenue: float, expenses: float):
        """Update monthly aggregated statistics"""
        # Calculate which month this day belongs to (30 days per month)
        month = (day - 1) // 30

        # Find or create monthly entry
        if self.monthly_history and self.monthly_history[-1].month == month:
            # Update existing month
            self.monthly_history[-1].revenue += revenue
            self.monthly_history[-1].expenses += expenses
        else:
            # Create new month
            self.monthly_history.append(MonthlyFinance(month, revenue, expenses))

    def get_today_stats(self) -> Dict[str, float]:
        """Get today's financial statistics"""
        return {
            'revenue': self.today_revenue,
            'expenses': self.today_expenses,
            'profit': self.today_revenue - self.today_expenses
        }

    def get_last_30_days_stats(self) -> Dict[str, float]:
        """Get aggregated statistics for last 30 days"""
        if not self.daily_history:
            return {'revenue': 0.0, 'expenses': 0.0, 'profit': 0.0}

        # Get last 30 entries
        last_30 = list(self.daily_history)[-30:]

        total_revenue = sum(d.revenue for d in last_30)
        total_expenses = sum(d.expenses for d in last_30)

        return {
            'revenue': total_revenue,
            'expenses': total_expenses,
            'profit': total_revenue - total_expenses
        }

    def get_last_365_days_stats(self) -> Dict[str, float]:
        """Get aggregated statistics for last 365 days (1 year)"""
        if not self.daily_history:
            return {'revenue': 0.0, 'expenses': 0.0, 'profit': 0.0, 'avg_profit_per_day': 0.0}

        total_revenue = sum(d.revenue for d in self.daily_history)
        total_expenses = sum(d.expenses for d in self.daily_history)
        profit = total_revenue - total_expenses

        days_count = len(self.daily_history)
        avg_profit = profit / days_count if days_count > 0 else 0.0

        return {
            'revenue': total_revenue,
            'expenses': total_expenses,
            'profit': profit,
            'avg_profit_per_day': avg_profit
        }

    def get_daily_graph_data(self, days: int = 30) -> List[Dict]:
        """
        Get daily data for graphing.
        Returns list of {day, revenue, expenses, profit} for last N days.
        """
        if not self.daily_history:
            return []

        last_n = list(self.daily_history)[-days:]

        return [
            {
                'day': d.day,
                'revenue': d.revenue,
                'expenses': d.expenses,
                'profit': d.profit
            }
            for d in last_n
        ]

    def get_monthly_graph_data(self) -> List[Dict]:
        """
        Get monthly aggregated data for graphing.
        Returns list of {month, revenue, expenses, profit} for last 12 months.
        """
        if not self.monthly_history:
            return []

        return [
            {
                'month': m.month,
                'revenue': m.revenue,
                'expenses': m.expenses,
                'profit': m.profit
            }
            for m in self.monthly_history
        ]

    def get_trend(self) -> str:
        """
        Get today's trend compared to yesterday.
        Returns 'up', 'down', or 'neutral'.
        """
        if not self.daily_history:
            return 'neutral'

        today_profit = self.today_revenue - self.today_expenses
        yesterday = self.daily_history[-1] if self.daily_history else None

        if not yesterday:
            return 'neutral'

        if today_profit > yesterday.profit:
            return 'up'
        elif today_profit < yesterday.profit:
            return 'down'
        else:
            return 'neutral'

    # Serialization for save/load
    def to_dict(self) -> dict:
        """Convert to dictionary for saving"""
        return {
            'current_day': self.current_day,
            'today_revenue': self.today_revenue,
            'today_expenses': self.today_expenses,
            'daily_history': [d.to_dict() for d in self.daily_history],
            'monthly_history': [m.to_dict() for m in self.monthly_history]
        }

    def from_dict(self, data: dict):
        """Load from dictionary"""
        self.current_day = data.get('current_day', 0)
        self.today_revenue = data.get('today_revenue', 0.0)
        self.today_expenses = data.get('today_expenses', 0.0)

        # Restore daily history
        daily_data = data.get('daily_history', [])
        self.daily_history = deque(
            [DailyFinance.from_dict(d) for d in daily_data],
            maxlen=365
        )

        # Restore monthly history
        monthly_data = data.get('monthly_history', [])
        self.monthly_history = deque(
            [MonthlyFinance.from_dict(m) for m in monthly_data],
            maxlen=12
        )
