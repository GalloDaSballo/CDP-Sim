import random

MAX_BPS = 10_000
MAX_LTV = 8_500


class Trove:
    def __init__(self, owner, system):
        self.collateral = 0
        self.debt = 0
        self.last_update_ts = system.time
        self.owner = owner
        self.system = system
        self.id = str(
            random.randint(1, 10**24)
        )  ## Although PRGN odds of clash are unlikely

    def __repr__(self):
        return str(self.__dict__)

    def local_collateral_ratio(self):
        return self.debt * MAX_BPS / self.collateral

    def deposit(self, amount):
        ## System Wide
        self.system.total_deposits += amount

        ## Internal
        assert self.is_solvent()
        self.collateral += amount

        ## Caller
        self.owner.spend(self.id, False, amount, "Deposit")

        ## Logging
        self.system.logger.add_entry(
            [self.system.time, "Trove" + self.id, "Deposit", amount]
        )

    def withdraw(self, amount):
        ## System Wide
        self.system.total_deposits -= amount

        ## Internal
        self.collateral -= amount
        assert self.is_solvent()

        ## Caller
        self.owner.receive(self.id, False, amount, "Withdraw")

        ## Logging
        self.system.logger.add_entry(
            [self.system.time, "Trove" + self.id, "Withdraw", amount]
        )

    def borrow(self, amount):
        ## Internal
        self.debt += amount
        assert self.is_solvent()

        ## System Wide
        self.system.total_debt += amount
        assert self.system.is_solvent()

        self.owner.receive(self.id, True, amount, "Borrow")

        ## Logging
        self.system.logger.add_entry(
            [self.system.time, "Trove" + self.id, "Borrow", amount]
        )

    def repay(self, amount):
        ## Internal
        self.debt -= amount
        assert self.is_solvent()

        ## System Wide
        self.system.total_debt -= amount
        assert self.system.is_solvent()

        self.owner.spend(self.id, True, amount, "Repay")

        ## Logging
        self.system.logger.add_entry(
            [self.system.time, "Trove" + self.id, "Repay", amount]
        )

    def liquidate_full(self, caller):

        ## Only if not owner
        if caller == self.owner:
            return False

        assert self.is_underwater()

        # TODO: do we care about this specifics?
        is_recovery_mode = self.system.is_in_emergency_mode()

        total_debt_burn = self.debt
        total_col_send = self.collateral

        # Internal
        self.debt -= total_debt_burn
        self.collateral -= total_col_send

        ## System Wide
        self.system.total_debt -= total_debt_burn
        self.system.total_deposits -= total_col_send

        ## Spend Debt to repay
        caller.spend(self.id, True, total_debt_burn, "Liquidate")
        ## Receive Collateral for liquidation
        caller.receive(self.id, False, total_col_send, "Liquidate")

        ## Logging
        self.system.logger.add_entry(
            [self.system.time, "Trove", "Liquidate", total_debt_burn]
        )

        return 0

    def redeem(self, ebtc_amount, caller):
        # healh check-ups before filling redemptions
        assert ebtc_amount > 0
        assert self.system.get_tcr() >= self.system.MCR
        assert ebtc_amount <= self.system.total_debt
        assert caller.debt >= ebtc_amount

        price = self.system.get_price()

        trove_ebtc_redemption = min(ebtc_amount, self.debt)
        coll_compensation = trove_ebtc_redemption / price

        # Internal
        self.debt -= trove_ebtc_redemption
        self.collateral -= coll_compensation

        # System Wide
        self.system.total_debt -= trove_ebtc_redemption
        self.system.total_deposits -= coll_compensation

        # Redemption Fee
        coll_redemp_fee = self.redemption_fee(coll_compensation)
        self.system.redemp_coll += coll_redemp_fee

        # Caller Updates
        caller.spend(self.id, True, trove_ebtc_redemption, "Redemption")
        caller.receive(
            self.id, False, coll_compensation - coll_redemp_fee, "Redemption"
        )

        ## TODO: Function for price given debt
        ## Given that return linearly
        ## TODO: 2 -> require system calling
        ## TODO: 3 -> Add % Fee
        return coll_compensation - coll_redemp_fee

    def redemption_fee(self, coll_amt):
        # https://github.com/liquity/dev/blob/main/packages/contracts/contracts/TroveManager.sol#L47
        floor_fee = 0.005
        redemp_fee = coll_amt * floor_fee
        assert redemp_fee < coll_amt
        return redemp_fee

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

    def get_icr(self):
        if(self.debt == 0):
            return 100000000000
        
        return (self.collateral * self.system.get_price()) / self.debt * 100

    def current_ltv(self):
        if self.collateral == 0 or self.system.get_price() == 0:
            return 0

        return self.debt / (self.collateral * self.system.get_price())
