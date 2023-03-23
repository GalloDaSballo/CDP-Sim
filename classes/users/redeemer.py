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

        if self.system.total_debt > 0:
            ## Open new position
            self.arb(turn, troves, pool)

    def arb(self, turn, troves, pool):
        # healh check-ups before redeeming
        assert len(troves) > 0

        next_price = self.system.next_price
        price = self.system.price

        ## Specifically, we know that current price is cheaper than next
        ## Meaning we can buy AMT until price goes from current to next
        ## We effectively arb the pool
        ## And do a pure arb, which will pay off next block?

        ## TODO: logic

        # We can buy BTC and redeem it
        if price < next_price:
            ## TODO: Maximize via the LP function
            ## Then interact with Pool and perform the swap
            spot_price = pool.get_price_out(True, 1)

            # Ensure price spot is higher for one unit of collateral, otherwise will
            # not be profitable when consider swap fees and collateral redemp fee
            if spot_price > price:
                return "TODO: No point in arbing"

            print(
                f"[REDEEMER]Found arb!. System price: {spot_price} and Pool Spot price: {spot_price}"
            )

            prev_coll = self.collateral

            max_coll_in = pool.get_max_coll_before_next_price_sqrt(next_price)

            # Cap if too much
            to_purchase = min(prev_coll, max_coll_in)

            # Swap collateral in the pool for debt
            debt_out = pool.swap_for_debt(to_purchase)

            print(f"[REDEEMER]Swapped {to_purchase} in coll for {debt_out} in debt")

            # User Update
            self.collateral -= to_purchase
            self.debt += debt_out

            # Redeem Troves
            redeemed_coll = 0
            for trove in troves:
                debt_to_redeem = min(trove.debt, self.debt)
                if(debt_to_redeem > 0):
                    redeemed_coll += trove.redeem(debt_to_redeem, self)
                else:
                    break

            ## PURE ARB means we go back to coll
            print("self.debt", self.debt)
            # assert self.debt == 0
            # Final Collateral is greater than initial
            print("self.collateral", self.collateral)
            print("prev_coll", prev_coll)
            ## TODO: Sometimes unprofitable
            # assert self.collateral >= prev_coll
            # Final Collateral is equal to initial + total collateral redeemed
            # assert self.collateral == prev_coll + redeemed_coll
