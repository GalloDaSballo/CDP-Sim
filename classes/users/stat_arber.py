import math
import random
from classes.users.borrower import Borrower



## Borrow and Sells when price is higher
class StatArber(Borrower):
    def __init__(self, system, initial_balance_collateral):
        Borrower.__init__(self, system, initial_balance_collateral)

        ## TODO
        self.position = 0
        self.target_open_price = 0
        self.target_profit_percent = 0
        self.target_loss_percent = 0



    ## Borrow and Sell

    ## If profit is above target close

    ## If underwater enough, close at loss

    ## Always repay after X time

    ## Patience value

    ## Price Open
    ## Profit target
    ## Loss target

    ## Lifetime PNL
    ## Total Loss
    ## Total Gain

    
    def take_action(self, turn, troves, pool):

        trove = self.find_trove(troves)

        if not trove.is_solvent():
            print("Trove is insolvent, we run away with the money")
            return ## Just skip

        if(trove == False):
            print("Cannot find trove PROBLEM")
            assert False

        ## Has open position?
        if (self.position > 0):
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

            ## Sell to Pool

            ## Then set state
        
    def manage_position(self, trove):
        print("TODO")

        ## If next_price will hit the stop loss, sell now at loss

        ## if price hits the gain, take profit
        
