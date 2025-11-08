"""
Loan Management System
Handles player loans with automatic daily repayment
"""

from typing import Optional, Dict
from dataclasses import dataclass


@dataclass
class LoanType:
    """Predefined loan type"""
    name: str
    amount: float
    duration_days: int
    interest_rate: float  # As percentage (e.g., 10 for 10%)

    def get_total_amount(self) -> float:
        """Calculate total amount to repay"""
        return self.amount * (1 + self.interest_rate / 100)

    def get_daily_payment(self) -> float:
        """Calculate daily repayment amount"""
        return self.get_total_amount() / self.duration_days


# Predefined loan types
LOAN_TYPES = {
    'small': LoanType('Petit Prêt', 5000, 30, 10),
    'medium': LoanType('Moyen Prêt', 15000, 60, 15),
    'large': LoanType('Grand Prêt', 50000, 90, 20),
}


class ActiveLoan:
    """Represents an active loan"""

    def __init__(self, loan_type: LoanType, start_day: int):
        self.loan_type = loan_type
        self.start_day = start_day
        self.days_remaining = loan_type.duration_days
        self.amount_paid = 0.0

    def get_daily_payment(self) -> float:
        """Get the daily payment amount"""
        return self.loan_type.get_daily_payment()

    def get_remaining_amount(self) -> float:
        """Get remaining amount to pay (normal schedule)"""
        return self.days_remaining * self.get_daily_payment()

    def get_early_repayment_amount(self) -> float:
        """
        Calculate early repayment amount with reduced interest.
        Interest is proportional to time elapsed.
        """
        total_days = self.loan_type.duration_days
        days_elapsed = total_days - self.days_remaining

        # Calculate proportional interest
        time_ratio = days_elapsed / total_days if total_days > 0 else 0
        proportional_interest = self.loan_type.interest_rate * time_ratio

        # Original amount - already paid + proportional interest
        remaining_principal = self.loan_type.amount * (self.days_remaining / total_days)
        interest_on_remaining = remaining_principal * (proportional_interest / 100)

        return remaining_principal + interest_on_remaining

    def get_early_repayment_savings(self) -> float:
        """Calculate how much player saves by early repayment"""
        normal_remaining = self.get_remaining_amount()
        early_amount = self.get_early_repayment_amount()
        return normal_remaining - early_amount

    def make_daily_payment(self) -> float:
        """
        Process daily payment.
        Returns the payment amount.
        """
        payment = self.get_daily_payment()
        self.amount_paid += payment
        self.days_remaining -= 1
        return payment

    def is_complete(self) -> bool:
        """Check if loan is fully repaid"""
        return self.days_remaining <= 0


class LoanManager:
    """Manages player loans"""

    def __init__(self):
        self.active_loan: Optional[ActiveLoan] = None
        self.total_loans_taken = 0
        self.total_interest_paid = 0.0

    def has_active_loan(self) -> bool:
        """Check if player has an active loan"""
        return self.active_loan is not None

    def can_take_loan(self) -> bool:
        """Check if player can take a new loan (only 1 at a time)"""
        return not self.has_active_loan()

    def take_loan(self, loan_key: str, current_day: int) -> Optional[ActiveLoan]:
        """
        Take a new loan.
        Returns the active loan if successful, None otherwise.
        """
        if not self.can_take_loan():
            return None

        if loan_key not in LOAN_TYPES:
            return None

        loan_type = LOAN_TYPES[loan_key]
        self.active_loan = ActiveLoan(loan_type, current_day)
        self.total_loans_taken += 1

        return self.active_loan

    def process_daily_payment(self) -> tuple[bool, float]:
        """
        Process daily loan payment.
        Returns (success, payment_amount).
        If loan is complete, removes it.
        """
        if not self.has_active_loan():
            return (True, 0.0)

        payment = self.active_loan.make_daily_payment()

        # Track interest paid
        days_total = self.active_loan.loan_type.duration_days
        interest_per_day = (self.active_loan.loan_type.get_total_amount() -
                           self.active_loan.loan_type.amount) / days_total
        self.total_interest_paid += interest_per_day

        # Check if loan is complete
        if self.active_loan.is_complete():
            self.active_loan = None

        return (True, payment)

    def repay_early(self) -> float:
        """
        Repay loan early with reduced interest.
        Returns the amount to pay.
        Removes the active loan.
        """
        if not self.has_active_loan():
            return 0.0

        amount = self.active_loan.get_early_repayment_amount()

        # Track interest (proportional)
        days_total = self.active_loan.loan_type.duration_days
        days_elapsed = days_total - self.active_loan.days_remaining
        total_interest = self.active_loan.loan_type.get_total_amount() - self.active_loan.loan_type.amount
        interest_for_period = total_interest * (days_elapsed / days_total)
        self.total_interest_paid += interest_for_period

        self.active_loan = None

        return amount

    def get_loan_info(self) -> Optional[Dict]:
        """Get information about active loan for display"""
        if not self.has_active_loan():
            return None

        loan = self.active_loan
        return {
            'name': loan.loan_type.name,
            'original_amount': loan.loan_type.amount,
            'days_remaining': loan.days_remaining,
            'total_days': loan.loan_type.duration_days,
            'amount_paid': loan.amount_paid,
            'daily_payment': loan.get_daily_payment(),
            'remaining_normal': loan.get_remaining_amount(),
            'early_repayment': loan.get_early_repayment_amount(),
            'early_savings': loan.get_early_repayment_savings(),
        }

    # Serialization for save/load
    def to_dict(self) -> dict:
        """Convert to dictionary for saving"""
        data = {
            'total_loans_taken': self.total_loans_taken,
            'total_interest_paid': self.total_interest_paid,
            'active_loan': None
        }

        if self.active_loan:
            # Find which loan type this is
            loan_key = None
            for key, loan_type in LOAN_TYPES.items():
                if (loan_type.name == self.active_loan.loan_type.name and
                    loan_type.amount == self.active_loan.loan_type.amount):
                    loan_key = key
                    break

            data['active_loan'] = {
                'loan_key': loan_key,
                'start_day': self.active_loan.start_day,
                'days_remaining': self.active_loan.days_remaining,
                'amount_paid': self.active_loan.amount_paid,
            }

        return data

    def from_dict(self, data: dict):
        """Load from dictionary"""
        self.total_loans_taken = data.get('total_loans_taken', 0)
        self.total_interest_paid = data.get('total_interest_paid', 0.0)

        active_loan_data = data.get('active_loan')
        if active_loan_data:
            loan_key = active_loan_data.get('loan_key')
            if loan_key and loan_key in LOAN_TYPES:
                loan_type = LOAN_TYPES[loan_key]
                self.active_loan = ActiveLoan(loan_type, active_loan_data.get('start_day', 0))
                self.active_loan.days_remaining = active_loan_data.get('days_remaining', loan_type.duration_days)
                self.active_loan.amount_paid = active_loan_data.get('amount_paid', 0.0)
        else:
            self.active_loan = None
