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

## TODO: Prob, just like liquidator, you'd loop forever until not profitable
## But you can cap to simulate gas limits
class RedeemArber(User):
    ## TODO: Add data to track self open stuff

    def take_action(self, turn, troves, pool):
        ## They know the next price before it happens
        ## At price set, the pool self-arbs for now TODO: Simulate the universe lmao

        ## Open new position
        self.arb(turn, troves, pool)

    def arb(self, turn, troves, pool):
        next_price = 1 / self.system.next_price
        price = 1 / self.system.price

            ## Specifically, we know that current price is cheaper than next
            ## Meaning we can buy AMT until price goes from current to next
            ## We effectively arb the pool
            ## And do a pure arb, which will pay off next block?

            ## TODO: logic

        # We can buy BTC and redeem it
        if price < next_price:
            print("Found arb")
            ## TODO: Maximize via the LP function
            ## Then interact with Pool and perform the swap
            spot_price = pool.get_price_out(True, 1)
            print("spot_price", spot_price)
            
            coll_amount = self.collateral
            pool_max_before_next_price = pool.get_max_coll_before_next_price(next_price)

            if pool_max_before_next_price < self.collateral:
                print("Partial Arb")
                coll_amount = pool_max_before_next_price

            prev_coll = self.collateral

            # Cap if too much
            to_purchase = min(prev_coll, pool_max_before_next_price)

            ## Then we close for immediate profit
            debt_out = self.swap_for_debt(to_purchase)

            # User Update
            self.collateral -= to_purchase
            self.debt += debt_out

            # Redeem Troves
            redeemed_coll = 0
            for trove in troves:
                redeemed_coll += trove.redeem(debt_out, self)

            ## PURE ARB means we go back to coll
            assert self.debt == 0
            # Final Collateral is greater than initial
            assert self.coll > prev_coll
            # Final Collateral is equal to initial + total collateral redeemed
            assert self.coll == prev_coll + redeemed_coll
