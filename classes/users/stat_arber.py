import math
import random
from classes.users.borrower import Borrower



## Borrow and Sells when price is higher
"""
    ## Borrow and Sell

    ## If profit is above target close

    ## If underwater enough, close at loss

    ## Always repay after X time

    ## Patience value

    ## Price Open
    ## Profit target
    ## Loss target

    ## Lifetime PNL
    ## Total Loss
    ## Total Gain
"""
class StatArber(Borrower):
    def __init__(self, system, initial_balance_collateral):
        Borrower.__init__(self, system, initial_balance_collateral)

        ## Track open position
        self.position_sold_debt = 0
        self.position_bought_coll = 0

        ## TODO: Random price generation
        self.target_open_price = 0
        self.target_profit_price = 0
        self.target_loss_price = 0

        self.total_loss = 0
        self.total_gain = 0

    
    def take_action(self, turn, troves, pool):

        trove = self.find_trove(troves)

        if not trove.is_solvent():
            print("Trove is insolvent, we run away with the money")
            return ## Just skip

        if(trove == False):
            print("Cannot find trove PROBLEM")
            assert False

        ## Has open position?
        if (self.has_position() > 0):
            self.manage_position(trove)
        else:
            self.open_position(trove)

    def open_position(self, trove):
        price = self.system.get_price()

        ## If above target, open and sell
        if price > self.target_open_price:
            self.deposit_all(trove)

            ## Borrow to tollerance
            self.borrow_til_target_ltv(trove, self.target_ltv)

            initial_coll = self.collateral

            self.position_sold_debt += self.debt

            ## Sell to Pool
            ## True = We sell debt
            self.system.pool.swap(self, True, self.debt)

            ## Then set state
            after_coll = self.collateral
            
            ## Coll we want to sell to get back debt to repay
            self.position_bought_coll = after_coll - initial_coll
        
    def manage_position(self, trove):
        price = self.system.get_price()
        next_price = self.system.get_next_price()

        ## If next_price will hit the stop loss, sell now at loss
        if next_price > self.target_loss_price:
            ## Let's dump at a loss
    
            initial_debt = self.debt
            
            self.system.pool.swap(self, False, self.position_bought_coll)
            
            ## Reset that position tracking
            self.position_bought_coll = 0
            
            ## Compute roi
            ## TODO: test to ensure values are pointed to, else this is way more complex
            after_debt = self.debt
            delta_debt = after_debt - initial_debt

            ## Some of the debt will remain as price moved against
            self.position_sold_debt -= delta_debt

            ## TODO: Compute price as coll
            ## TODO: Standardize pricing via a function
            loss = delta_debt * price
            self.total_loss += loss

        elif price > self.target_profit_price:
            ## if price hits the gain, take profit

            initial_debt = self.debt

            self.sell_all_coll()

            after_debt = self.debt
            delta_debt = after_debt - initial_debt

            cached_initial_debt = self.position_sold_debt

            ## We sold everything by definition
            assert delta_debt > self.position_sold_debt

            self.position_sold_debt = 0

            ## TODO: Price standardization
            gain = (delta_debt - cached_initial_debt) * price
            self.total_gain += gain

    def sell_all_coll(self):
        self.system.pool.swap(self, False, self.position_bought_coll)
        self.position_bought_coll = 0

    def has_position(self):
        return self.position_bought_coll > 0

        
