import math
import random
from classes.users.user import User

"""
    TODO: Incomplete

    (Add liquidation logic to troves as well)

    FlashLiquidator will:
    - Compute if worth liquidating -> custom by subclass
    - Flashloan the amount -> Always the same
    - Liquidate that amount / call the liquidation function -> custom by subclass
    - Track roi?? -> Always the same
"""

MAX_BPS = 10_000

## Liquidate when profitable ETH -> eBTC -> ETH
## Never takes any debt, their liquidations are entirely a function of premium and liquidity
class FlashFullLiquidator(User):

    def __init__(self, system, profitable_treshold):
        User.__init__(self, system, 0)
        
        self.name += "-fl-liquidator"

        ## 9 basis points or we wouldn't even do th swap
        self.profitable_treshold = profitable_treshold
        
        self.max_liquidations_per_block = 12 ## TODO: Simulate gas efficiency, as some contracts are cheaper than others

        self.liquidated_ids = []

    def take_action(self, turn, troves, pool):
        ## Check amount liquidatable
        [liquidatable_troves] = get_liquidatable(troves)
        print("")
        print("")
        print("")
        print("")

        ## Get next liquidatable trove

        ## Compute amount you can liquidate profitably via FL
        has_troves = len(liquidatable_troves) > 0

        if not has_troves:
            print("No Troves liquidatable, skip")
        last_profitable = True
        liquidations_left = self.max_liquidations_per_block

        while has_troves and last_profitable and liquidations_left > 0:
            print("has_troves", has_troves)
            print("liquidations_left", liquidations_left)
            liquidations_left -= 1

            next_trove = None

            try:
                next_trove = liquidatable_troves.pop(0)
            except:
                has_troves = False

            if next_trove == None:
                break

            ## If we apply the price impact, we can already compare ROI
            amt_of_coll_required = pool.amount_for_debt(next_trove.debt) ## From x to y, from coll to
            debt_after_purchase = pool.get_amount_out(True, amt_of_coll_required)
            coll_in = amt_of_coll_required
            coll_out = next_trove.collateral
            roi_liq = get_roi_full_liquidation(coll_in, coll_out)
            print("system price", self.system.get_price())
            print("get_roi_full_liquidation coll_as_debt", roi_liq)
            if roi_liq > (MAX_BPS + self.profitable_treshold) / MAX_BPS:
                ## We perform the liquidation
                self.do_liquidation(next_trove, amt_of_coll_required, pool)

                ### TODO: Add Profit math
                self.liquidated_ids.append(next_trove.id)
            else:
                
                ## We do not
                last_profitable = False
        
    def do_liquidation(self, trove, collateral_paid, pool):
        ## Fake flashloan
        self.receive("fake flashloan", False, collateral_paid, "Flashloan Received")

        ## Pay to Pool
        pool.swap_for_debt(collateral_paid)

        ## Liquidate the trove
        if self.debt > 0:
            trove.liquidate_full(self)

    
def get_liquidatable(troves):
    found = []

    for trove in troves:        
        if not trove.is_solvent():
            found.append(trove)

        
    found.sort(key=lambda obj: obj.get_icr(), reverse=True)     

    return [found]

def get_roi_full_liquidation(coll_in, coll_out):
    return coll_out / coll_in