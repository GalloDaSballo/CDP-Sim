import math
import random
from classes.users.user import User

"""
    TODO: Incomplete

    (Add liquidation logic to troves as well)
"""

## Liquidate when profitable ETH -> eBTC -> ETH
## Never takes any debt, their liquidations are entirely a function of premium and liquidity
class PureLiquidator(User):
    ## TODO: Collateral

    def take_action(self, turn, troves, pool):
        pass

        ## Check amount liquidatable
        [liquidatable_troves, total_debt_liquidatable, total_coll_liquidatable] = get_liquidatable(troves)

        collateral_value = self.get_value_of_collateral(self.collateral)

        if (liquidatable > 0):
            if(liquidatable > collateral_value):
                ## Cap value to what we have
                liquidatable = collateral_value

            ## Check if profitable
            profit = get_liquidation_profitability(total_debt_liquidatable, total_coll_liquidatable)

            ## Do the liquidation and arb
    
def get_liquidatable(troves):
    ## TODO: Should this be library?
    ## TODO: Classes
    found = []
    total_debt = 0
    total_coll = 0

    for trove in troves:
        if not trove.is_solvent():
            found.append(trove)
            total_debt += trove.debt
            total_coll += trove.collateral
        
    found.sort(trove.get_cr(), True)     

    return [found, total_coll, total_debt]