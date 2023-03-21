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
        next_price = 1 / self.system.next_price
        price = 1 / self.system.price

        # We can buy BTC and redeem it
        if price < next_price:
            print("Found arb")
            ## TODO: Maximize via the LP function
            ## Then interact with Pool and perform the swap
            spot_price = pool.get_price_out(True, 1)
            print("spot_price", spot_price)

            pool_max_before_next_price = pool.get_max_before_price(next_price)

            if pool_max_before_next_price:
                print("NO arb???")
                return

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
