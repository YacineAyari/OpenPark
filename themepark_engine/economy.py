
class Economy:
    def __init__(self): self.cash=10000
    def add_expense(self,amt): self.cash-=amt
    def add_income(self,amt): self.cash+=amt
    def tick(self): pass
