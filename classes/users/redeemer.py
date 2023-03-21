import math
import random
from classes.users.user import User

"""
    TODO: Incomplete

    (Add Redeem logic to troves as well)
"""

## Buy Cheap and Redeem if worth more
## If we know the price (of the Collateral) will go up next turn
## Buy cheap now
## Redeem and get more coll
## Coll will be worth more than debt
## Coll -> Debt -> Redeem -> Coll
class RedeemArber(User):
    ## TODO: Add data to track self open stuff

    def take_action(self, turn, troves, pool):
        ## They know the next price before it happens
        ## At price set, the pool self-arbs for now TODO: Simulate the universe lmao

        ## Open new position
        self.arb(turn, troves, pool)

    def arb(self, turn, troves, pool):
        if price < next_price:
            next_price = 1 / self.system.next_price
            price = 1 / self.system.price
            ## We can buy BTC and redeem it

            ## Specifically, we know that current price is cheaper than next
            ## Meaning we can buy AMT until price goes from current to next
            ## We effectively arb the pool
            ## And do a pure arb, which will pay off next block?

            ## TODO: logic

            print("Found arb")
            ## TODO: Maximize via the LP function
            ## Then interact with Pool and perform the swap
            pool_spot = get_pool_spot(pool)

            pool_max_before_next_price = get_max_before_price(pool, next_price)

            if pool_max_before_next_price:
                print("NO arb???")
                return

            prev_coll = self.collateral

            # Cap if too much
            to_purchase = min(prev_coll, pool_max_before_next_price)

            ## Then we close for immediate profit
            debt_out = self.swap_for_debt(to_purchase)
            ## TODO: Accounting here

            ## Via redeem 
            redeemed_coll = self.redeem(debt_out)

            ## PURE ARB means we go back to coll
            assert self.debt == 0
            ## Must be profitable else we made a mistake
            assert self.coll == prev_coll + redeemed_coll
