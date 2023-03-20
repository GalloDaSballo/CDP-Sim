import math
import random
from classes.users.user import User

"""
    TODO: Incomplete

    (Add Redeem logic to troves as well)
"""

## Buys when cheap and sells when higher
class RedeemArber(User):
   ## TODO: Add data to track self open stuff

    def take_action(self, turn, troves, pool):
        ## They know the next price before it happens
        ## At price set, the pool self-arbs for now TODO: Simulate the universe lmao

        ## Open new position
        self.arb(turn, troves, pool)


    
    def arb(self, turn, troves, pool):
        if (price < next_price):
            next_price = 1 / self.system.next_price
            price = 1 / self.system.price
            ## We can buy BTC and redeem it

            print("Found arb")
            ## TODO: Maximize via the LP function
            ## Then interact with Pool and perform the swap
            pool_spot = get_pool_spot(pool)

            pool_max_before_next_price = get_max_before_price(pool, next_price)

            if(pool_max_before_next_price):
                print("NO arb???")
                return
            

            prev_coll = self.collateral

            to_purchase = prev_coll

            if(prev_coll > pool_max_before_next_price):
                ## Cap if too much
                to_purchase = pool_max_before_next_price

            ## Then we close for immediate profit
            debt_out = self.swap_for_debt(to_purchase)
            ## TODO: Accounting here

            ## Via redeem
            redeemed_coll = self.redeem(debt_out)

            ## TODO: Accounting here

            ## PURE ARB means we go back to coll
            assert self.debt == 0
            ## Must be profitable else we made a mistake
            assert self.coll > prev_coll

       
       