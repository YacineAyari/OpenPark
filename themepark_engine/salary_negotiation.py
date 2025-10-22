"""
Salary Negotiation System for OpenPark.
Employees negotiate salary increases once per year, with consequences for refusal.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import random


class NegotiationStage(Enum):
    """Stages of negotiation process"""
    NONE = 0
    FIRST_PROPOSAL = 1      # Initial proposal
    SECOND_PROPOSAL = 2     # After first refusal (-35% efficiency)
    THIRD_PROPOSAL = 3      # After second refusal (-75% efficiency)
    STRIKE = 4              # On strike (0% efficiency)
    FINAL_ULTIMATUM = 5     # Last chance before resignation


@dataclass
class NegotiationState:
    """State of an ongoing salary negotiation"""
    employee_type: str                    # 'engineer', 'maintenance', 'security', 'mascot'
    affected_employee_ids: List[int]      # IDs of employees affected by this negotiation
    current_stage: NegotiationStage       # Current stage of negotiation
    current_salary: int                   # Current daily salary
    demanded_salary: int                  # Salary demanded by employees
    player_counter_offer: int             # Player's counter-offer (0 = none yet)
    next_negotiation_day: int             # Game day for next negotiation step
    strike_start_day: int                 # Day strike started (0 = not on strike)
    efficiency_penalty: float             # Current efficiency penalty (0.0 to 1.0)
    negotiation_start_year: int           # Year when negotiation started


class SalaryNegotiationManager:
    """Manages salary negotiations for all employee types"""

    def __init__(self):
        self.active_negotiations: Dict[str, NegotiationState] = {}
        self.negotiation_history: List[Dict] = []

        # Calendar: which month each employee type negotiates
        # TESTING MODE: All types negotiate on day 1 (month 1) for easy testing
        # TODO: Restore to original values for production
        # Original: engineer=3, maintenance=6, security=9, mascot=12
        self.negotiation_months = {
            'engineer': 1,      # TESTING: Month 1 (was Month 3)
            'maintenance': 1,   # TESTING: Month 1 (was Month 6)
            'security': 1,      # TESTING: Month 1 (was Month 9)
            'mascot': 1         # TESTING: Month 1 (was Month 12)
        }

        # Last negotiation year for each type
        self.last_negotiation_year = {
            'engineer': 0,
            'maintenance': 0,
            'security': 0,
            'mascot': 0
        }

    def should_trigger_negotiation(self, employee_type: str, current_day: int,
                                   current_year: int, park_profit: float) -> bool:
        """Determine if a negotiation should be triggered for this employee type

        Time system: 1 year = 12 days, 1 month = 1 day
        """

        # Get current month (1 day = 1 month, 12 days = 1 year)
        current_month = (current_day % 12) + 1

        # Check if it's the right month for this type
        if current_month != self.negotiation_months.get(employee_type, 0):
            return False

        # Check if already negotiated this year
        if self.last_negotiation_year.get(employee_type, 0) >= current_year:
            return False

        # Check if there's already an active negotiation
        if employee_type in self.active_negotiations:
            return False

        # Calculate probability based on park profit
        if park_profit > 10000:
            chance = 0.9  # Very profitable = high chance of demands
        elif park_profit > 5000:
            chance = 0.6  # Moderately profitable
        elif park_profit > 0:
            chance = 0.3  # Low profit = low demands
        else:
            chance = 0.1  # Losing money = very rare demands

        # TESTING MODE: Force 100% chance for easy testing
        # TODO: Remove this for production
        chance = 1.0

        return random.random() < chance

    def start_negotiation(self, employee_type: str, affected_employees: List[int],
                         current_salary: int, current_year: int, current_day: int) -> NegotiationState:
        """Start a new salary negotiation for an employee type

        Time system: Next stage in 1 day (= 1 month in-game)
        """

        # Calculate demanded salary (15% to 30% increase)
        base_increase = 0.15
        variable_increase = random.uniform(0.0, 0.15)
        demanded_salary = int(current_salary * (1 + base_increase + variable_increase))

        # Create negotiation state
        negotiation = NegotiationState(
            employee_type=employee_type,
            affected_employee_ids=affected_employees.copy(),
            current_stage=NegotiationStage.FIRST_PROPOSAL,
            current_salary=current_salary,
            demanded_salary=demanded_salary,
            player_counter_offer=0,
            next_negotiation_day=current_day + 1,  # Next stage in 1 day (= 1 month)
            strike_start_day=0,
            efficiency_penalty=0.0,
            negotiation_start_year=current_year
        )

        self.active_negotiations[employee_type] = negotiation
        self.last_negotiation_year[employee_type] = current_year

        return negotiation

    def process_negotiation_response(self, employee_type: str, player_offer: int,
                                    current_day: int) -> tuple[bool, str]:
        """
        Process player's response to a negotiation.

        Returns: (accepted, message)
        """
        if employee_type not in self.active_negotiations:
            return False, "No active negotiation"

        negotiation = self.active_negotiations[employee_type]
        negotiation.player_counter_offer = player_offer

        # Calculate acceptance threshold (80% of demanded salary)
        acceptance_threshold = negotiation.demanded_salary * 0.8

        if player_offer >= acceptance_threshold:
            # Accepted! Update salary and end negotiation
            self._end_negotiation(employee_type, accepted=True, new_salary=player_offer)
            return True, f"Negotiation accepted! New salary: ${player_offer}/day"
        else:
            # Rejected! Move to next stage
            return self._advance_to_next_stage(negotiation, current_day)

    def _advance_to_next_stage(self, negotiation: NegotiationState,
                               current_day: int) -> tuple[bool, str]:
        """Advance negotiation to next stage after rejection

        Time system: 1 day = 1 month, except final ultimatum (same day decision)
        """

        if negotiation.current_stage == NegotiationStage.FIRST_PROPOSAL:
            negotiation.current_stage = NegotiationStage.SECOND_PROPOSAL
            negotiation.efficiency_penalty = 0.35
            negotiation.next_negotiation_day = current_day + 1  # 1 day = 1 month
            return False, "Offer rejected. Employees working at -35% efficiency. Next negotiation in 1 day."

        elif negotiation.current_stage == NegotiationStage.SECOND_PROPOSAL:
            negotiation.current_stage = NegotiationStage.THIRD_PROPOSAL
            negotiation.efficiency_penalty = 0.75
            negotiation.next_negotiation_day = current_day + 1  # 1 day = 1 month
            return False, "Offer rejected. Employees working at -75% efficiency. Next negotiation in 1 day."

        elif negotiation.current_stage == NegotiationStage.THIRD_PROPOSAL:
            negotiation.current_stage = NegotiationStage.STRIKE
            negotiation.efficiency_penalty = 1.0
            negotiation.strike_start_day = current_day
            negotiation.next_negotiation_day = current_day + 1  # Strike lasts 1 day = 1 month
            return False, "Offer rejected. Employees ON STRIKE for 1 day! (0% efficiency)"

        elif negotiation.current_stage == NegotiationStage.STRIKE:
            # Strike ended, final ultimatum
            negotiation.current_stage = NegotiationStage.FINAL_ULTIMATUM
            negotiation.next_negotiation_day = current_day  # Immediate decision required
            return False, "Final ultimatum! Accept NOW or all employees resign."

        elif negotiation.current_stage == NegotiationStage.FINAL_ULTIMATUM:
            # Resignation!
            self._end_negotiation(negotiation.employee_type, accepted=False, new_salary=0)
            return False, f"ALL {negotiation.employee_type}s have RESIGNED! You must hire new employees."

        return False, "Unknown stage"

    def _end_negotiation(self, employee_type: str, accepted: bool, new_salary: int):
        """End a negotiation (either accepted or failed)"""
        if employee_type in self.active_negotiations:
            negotiation = self.active_negotiations[employee_type]

            # Record in history
            self.negotiation_history.append({
                'type': employee_type,
                'year': negotiation.negotiation_start_year,
                'accepted': accepted,
                'demanded': negotiation.demanded_salary,
                'final_offer': negotiation.player_counter_offer,
                'new_salary': new_salary
            })

            # Remove from active
            del self.active_negotiations[employee_type]

    def get_efficiency_penalty(self, employee_type: str, employee_id: int) -> float:
        """Get current efficiency penalty for an employee (0.0 = no penalty, 1.0 = full penalty)"""
        if employee_type not in self.active_negotiations:
            return 0.0

        negotiation = self.active_negotiations[employee_type]

        # Only applies to employees who were there at negotiation start
        if employee_id not in negotiation.affected_employee_ids:
            return 0.0

        return negotiation.efficiency_penalty

    def is_on_strike(self, employee_type: str) -> bool:
        """Check if employees of this type are on strike"""
        if employee_type not in self.active_negotiations:
            return False

        return self.active_negotiations[employee_type].current_stage == NegotiationStage.STRIKE

    def get_active_negotiation(self, employee_type: str) -> Optional[NegotiationState]:
        """Get the active negotiation for an employee type, if any"""
        return self.active_negotiations.get(employee_type)

    def to_dict(self) -> dict:
        """Serialize for saving"""
        return {
            'active_negotiations': {
                emp_type: {
                    'employee_type': n.employee_type,
                    'affected_employee_ids': n.affected_employee_ids,
                    'current_stage': n.current_stage.value,
                    'current_salary': n.current_salary,
                    'demanded_salary': n.demanded_salary,
                    'player_counter_offer': n.player_counter_offer,
                    'next_negotiation_day': n.next_negotiation_day,
                    'strike_start_day': n.strike_start_day,
                    'efficiency_penalty': n.efficiency_penalty,
                    'negotiation_start_year': n.negotiation_start_year
                }
                for emp_type, n in self.active_negotiations.items()
            },
            'last_negotiation_year': self.last_negotiation_year,
            'negotiation_history': self.negotiation_history
        }

    @staticmethod
    def from_dict(data: dict) -> 'SalaryNegotiationManager':
        """Deserialize from save"""
        manager = SalaryNegotiationManager()
        manager.last_negotiation_year = data.get('last_negotiation_year', {})
        manager.negotiation_history = data.get('negotiation_history', [])

        # Restore active negotiations
        for emp_type, n_data in data.get('active_negotiations', {}).items():
            manager.active_negotiations[emp_type] = NegotiationState(
                employee_type=n_data['employee_type'],
                affected_employee_ids=n_data['affected_employee_ids'],
                current_stage=NegotiationStage(n_data['current_stage']),
                current_salary=n_data['current_salary'],
                demanded_salary=n_data['demanded_salary'],
                player_counter_offer=n_data['player_counter_offer'],
                next_negotiation_day=n_data['next_negotiation_day'],
                strike_start_day=n_data['strike_start_day'],
                efficiency_penalty=n_data['efficiency_penalty'],
                negotiation_start_year=n_data['negotiation_start_year']
            )

        return manager
