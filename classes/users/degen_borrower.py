import math
import random
from classes.users.borrower import Borrower


SPEED_RANGE = 100
REMAINING_LTV_RANGE = 5_00
MIN_LTV_DEGEN = 80_00
MAX_BPS = 10_000

## Borrows and Holds
class DegenBorrower(Borrower):
    def __init__(self, system, initial_balance_collateral):
        Borrower.__init__(self, system, initial_balance_collateral)

        self.target_ltv = MIN_LTV_DEGEN + random.random() * REMAINING_LTV_RANGE