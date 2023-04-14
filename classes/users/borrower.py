import math
import random
from classes.users.user import User


SPEED_RANGE = 100
MAX_LTV = 85_00
MAX_BPS = 10_000

## Borrows and Holds
class Borrower(User):
    def __init__(self, system, initial_balance_collateral):
        User.__init__(self, system, initial_balance_collateral)
        
        self.name += "-borrower"

        self.speed = math.floor(random.random() * SPEED_RANGE) + 1

        self.target_ltv = random.random() * MAX_LTV
    
    def take_action(self, turn, troves, pool):
        ## Deposit entire balance
        trove = self.find_trove(troves)

        ## TODO: If insolvent we should do something, perhaps try to redeem as much as possible
        if not trove.is_solvent():
            print(trove.id)
            print("Trove is insolvent, we run away with the money")
            return ## Just revert

        if(trove == False):
            print("Cannot find trove PROBLEM")
            assert False
        
        self.deposit_all(trove)

        self.borrow_til_target_ltv(trove, self.target_ltv)

        

    def deposit_all(self, trove):
        ## if has collateral spend it
        if(self.collateral > 0):
            trove.deposit(self.collateral)
            
            ## Check we did use collateral
            print("self.collateral", self.collateral)
            assert self.collateral == 0
        
    def borrow_til_target_ltv(self, trove, target_ltv):
        target_borrow = self.get_target_borrow(trove, target_ltv)

        ## If below target, borrow
        if(trove.debt < target_borrow):
            print("We are below target ltv, borrow")
            ## Borrow until we get to ltv
            delta_borrow = target_borrow - trove.debt

            try:
                trove.borrow(delta_borrow)
            except:
                x = 0 ## Do nothing, this can happen if we end up overborrowing after
        
        ## If above target, delever
        if(trove.debt > target_borrow):
            self.handle_repayment(trove, target_borrow)

    def handle_repayment(self, trove, target_borrow):
        delta = trove.debt - target_borrow
        ## Check we can afford to repay
        if delta < self.debt:
            trove.repay(delta)
        else:
            print("Insolvent, cannot repay the whole debt, wait and pray")

    def get_target_borrow(self, trove, target_ltv):
        return trove.max_borrow() * target_ltv / MAX_BPS


    def find_trove(self, troves):
        for trove in troves:
            if trove.owner.id == self.id:
                return trove

        return False


## TODO: Unit Tests