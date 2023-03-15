import random
MAX_BPS = 10_000
MAX_LTV = 85_00

class Trove:
    def __init__(self, owner, system):
        self.collateral = 0
        self.debt = 0
        self.last_update_ts = system.time
        self.owner = owner
        self.system = system
        self.id = str(random.randint(1, 10**24)) ## Although PRGN odds of clash are unlikely

    def __repr__(self):
        return str(self.__dict__)

    def local_collateral_ratio(self):
        return self.debt * MAX_BPS / self.collateral

    def deposit(self, amount):
        ## Internal
        assert self.is_solvent()
        self.system.total_deposits += amount
        self.collateral += amount

        ## Caller
        self.owner.spend(self.id, False, amount, "Deposit")

        ## Logging
        self.system.logger.add_entry([self.system.time, "Trove" + self.id, "Deposit", amount])

    def withdraw(self, amount):
        ## Internal
        self.collateral -= amount
        assert self.is_solvent()
        
        ## Caller
        self.owner.receive(self.id, False, amount, "Withdraw")

        ## Logging
        self.system.logger.add_entry([self.system.time, "Trove" + self.id, "Withdraw", amount])

    def borrow(self, amount):
        self.debt += amount
        assert self.is_solvent()
        self.system.total_debt += amount
        assert self.system.is_solvent()

        self.owner.receive(self.id, True, amount, "Borrow")

        ## Logging
        self.system.logger.add_entry([self.system.time, "Trove" + self.id, "Borrow", amount])


    def repay(self, amount):
        self.debt -= amount
        assert self.is_solvent()
        self.system.total_debt -= amount
        assert self.system.is_solvent()

        self.owner.spend(self.id, True, amount, "Repay")

        ## Logging
        self.system.logger.add_entry([self.system.time, "Trove" + self.id, "Repay", amount])

    def liquidate(self, amount, caller):
        ## Only if not owner
        if caller == self.owner:
            return False
        
        ## TODO: Incorrect / Missing piece / Math
        ## Spend Debt to repay
        caller.spend(self.id, True, amount, "Liquidate")
        ## Receive Collateral for liquidation
        caller.receive(self.id, False, amount, "Liquidate")

        ## Logging
        self.system.logger.add_entry([self.system.time, "Trove", "Liquidate", amount])

        return 0

    ## SECURITY CHECKS
    def is_trove(self):
        return True

    def max_borrow(self):
        ## TODO: use function that is same as system
        return self.collateral * self.system.get_price() * MAX_LTV / MAX_BPS

    def is_solvent(self):
        if self.debt == 0:
            return True
        ## Strictly less to avoid rounding or w/e
        return self.debt < self.max_borrow()

    def is_underwater(self):
        if self.debt == 0:
            return False
        
        return self.debt > self.collateral * self.system.get_price()

    def get_cr(self):
        return get_icr(self.collateral, self.debt, self.system.get_price())

    
    
    def current_ltv(self):
        if self.collateral == 0 or self.system.get_price() == 0:
            return 0
        
        return self.debt / (self.collateral * self.system.get_price())