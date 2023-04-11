"""
  Sim of CDP System

  ### SYSTEM STATE ###

  Global Collateral Ratio
  Total Deposits
  Total Debt

  ### SYSTEM CONFIG ###

  Max MAX_LTV
  Fee per second (0% on LUSD)
  Origination Fee (Fixed Fee 50 BPS on LUSD)

  ### TROVE STATE ###

  Local Collateral Ratio
  Local Deposits
  Local Debt


  ### USER ACTIONS ###
  Deposit
  Withdraw

  Borrow
  Repay

  Liquidate
"""
import random

from lib.logger import GenericLogger
from lib.helpers import get_cg_price

from classes.pool import Pool
from classes.ebtc import Ebtc
from classes.trove import Trove
from classes.users.borrower import Borrower
from classes.users.degen_borrower import DegenBorrower
from classes.users.stat_arber import StatArber
from classes.users.flash_full_liquidator import FlashFullLiquidator
from classes.users.redeemer import RedeemArber


MAX_BPS = 10_000
SECONDS_SINCE_DEPLOY = 0
SECONDS_PER_TURN = 12  ## One block in POS
INITIAL_FEED = 1000
SPEED_RANGE = 10

## TODO: CHANGE
MAX_LTV = 8500

## Randomness seed for multiple runs
SEED = 123

random.seed(SEED)

### ARCHITECURE ###
"""
    Ultimately we're loosely OOP, because OOP can become a mess follow these rules:

    - User and Trove can Log, add logs to System only if you need to snapshot.
        User and Trove are responsible for logging their state
    
    - System tracks all Users and Troves

    - System Triggers -> Users, which Triggers Troves and sync up with System

    - Users are the Agents, create a class that extends User (e.g. Borrower)
    
    - Write the logic in take_action and you will be able to extend the rest of the ebtc


    TODO:
    - Basic invariant / unit tests to make sure ebtc is fine
    - Extend more Classes to Sim
    - Decide if we want to extend UniV2 / V3 Pool and simulate arbs there as well, 
    TODO: for now recharge the size based on TVL
"""


"""
    LIBRARIES
"""


## AMM V2


def price_given_in(amount_in, reserve_in, reserve_out):
    """
    Returns price given the amount in and the reserves
    """
    out = amount_out_given_in(amount_in, reserve_in, reserve_out)
    return amount_in / out


def amount_out_given_in(amount_in, reserve_in, reserve_out):
    """
    Returns the amount out given the amount in and the reserves
    """
    amount_out = reserve_out * amount_in / (reserve_in + amount_in)
    return amount_out


def amount_in_give_out(amount_out, reserve_in, reserve_out):
    """
    Returns how much you need to send in order to receive amount out given the reserves
    """
    amount_in = reserve_in * amount_out / (reserve_out - amount_out)
    return amount_in


def max_in_before_price_limit(price_limit, reserve_in, reserve_out):
    """
    Returns the maximum amount you can buy before reaching the price limit
    """
    return reserve_out * price_limit - reserve_in


"""
    CONSTANTS
"""

## BASIC ##
START_COLL = (
    1_000_000e18  ## NOTE: No point in randomizing it as all insights are % of this
)

PRICE = 13


## RISK VALUES ##
## Below this you get liquidated
MCR = 110

## If TCR < CCR we enter recovery mode
CCR = 150

## In recovery mode, troves below CLR are liquidated
## NOTE: Set to CCR, tweak it if you want
CLR = CCR

STETH_COLL_BALANCE = 100
RESERVE_COLL_INITIAL_BALANCE = 1000
POOL_FEE = 300
INSANE_RATIO_DROP = 0.0001

"""
    Additiona Tracking, see: recap_extended_avg
    * Additional risk (metric being avg % TVL) -> Liquidatable TVL avg
    * Extra volatility (based on liquidations) -> Average Delta from Price + Standard Deviation of it (Can we do StDev of differences?)
    * AVG bad debt

    // Average = (Value + old_value) / 2
    // Value = bad_debt / all_debt * 100

    // Variance?
    // ST Dev

"""


## Brute force the sim to find the values
NORMAL_COUNT = 0
DEGEN_COUNT = 100
STAT_ARBER = 0 ## TODO: Fix this
REDEEM_ARBER = 1
LIQUIDATOR_COUNT = 1

## Want to see historical prices?
PLOT_PRICE = False

## We need 10% in 3 turns for the flag to be active
DRAWDOWN_MIN_AMOUNT = 1_000
DRAWDOWN_MAX_TURNS = 3

## NOTE: Could change into json like but nice to have
FLAGS = [
    "drawdown"
]

## Negative Streak (track older prices)
## Streak goes down by X% within N turns

def has_flags(history):
    for flag in FLAGS:
        if flag == "drawdown":
            if check_sufficient_drawdown(history):
                return True

def check_sufficient_drawdown(history):
    oldest_high = 0
    current_drawdown = 0
    turns = 0

    if len(history) < 3:
        return False

    prev_val = history[0]

    for val in history:
        turns += 1
        if val == prev_val:
            continue
        
        if val > prev_val:
            current_drawdown = 0
            turns = 0 ## Try again
            continue
        
        if val < prev_val:
            if oldest_high == 0:
                oldest_high = prev_val
            
            current_drawdown = oldest_high - val
    
        if current_drawdown / oldest_high * MAX_BPS > DRAWDOWN_MIN_AMOUNT:
            print("drawdown found")
            print("current_drawdown", current_drawdown)
            print("oldest_high", oldest_high)
            return True
        
        if turns > DRAWDOWN_MAX_TURNS + 1:
            current_drawdown = 0
            oldest_high = 0
    
    return False



def main():
    history = []
    logger = None

    
    history = []

    # init the ebtc
    logger = GenericLogger("sim", ["Time", "Name", "Action", "Amount"])
    # make initial balances of the pool matching the "oracle" price from the ebtc system
    reserve_debt_balance = RESERVE_COLL_INITIAL_BALANCE * get_cg_price()
    pool = Pool(RESERVE_COLL_INITIAL_BALANCE, reserve_debt_balance, 1000, POOL_FEE)

    ebtc = Ebtc(logger, pool)

    ## TODO: ADD COUNT as ways to populate them (so we can run % sims)

    users = []
    degens = []
    stat_arbers = []
    redeem_arbers = []
    liquidators = []

    troves = []

    for x in range(NORMAL_COUNT):
        user = Borrower(ebtc, STETH_COLL_BALANCE)
        users.append(user)
        troves.append(Trove(user, ebtc))

    for x in range(DEGEN_COUNT):
        degen = DegenBorrower(ebtc, STETH_COLL_BALANCE)
        degens.append(degen)
        troves.append(Trove(degen, ebtc))
        

    for x in range(STAT_ARBER):
        arber = StatArber(ebtc, STETH_COLL_BALANCE)
        stat_arbers.append(arber)
        troves.append(Trove(arber, ebtc))

    for x in range(REDEEM_ARBER):
        redeem_arbers.append(RedeemArber(ebtc, STETH_COLL_BALANCE * (NORMAL_COUNT // 2)))

    for x in range(LIQUIDATOR_COUNT):
        liquidators.append(FlashFullLiquidator(ebtc))


    assert ebtc.time == 0


    ## Turn System
    all_users = stat_arbers + redeem_arbers + liquidators + degens + users

    has_done_liq = False

    all_avg_bad_debt_percent = []
    all_avg_ltv = []
    all_liquidatable_percent = []
    all_prices_deltas = []

    all_prices = []

    while not has_done_liq and ebtc.is_solvent():
    
        try:
            ebtc.take_turn(all_users, troves)
            
            ## Flag System
            ## Add price so we can check in next iteration
            history.append(ebtc.get_price())

            all_avg_bad_debt_percent.append(ebtc.get_avg_bad_debt_percent(troves))
            all_avg_ltv.append(ebtc.get_avg_ltv(troves))
            all_liquidatable_percent.append(ebtc.get_avg_liquidatable_percent(troves))
            all_prices_deltas.append(ebtc.get_price_delta())

            all_prices.append(ebtc.get_price())

        except Exception as e: 
            print(e)
            print("Exception let's end")
            break


    ## Log the salient run
    df_system, _, _ = logger.to_csv()

    ## Print out end of sim status
    recap(ebtc, users, troves)
    recap_extended_avg(all_avg_bad_debt_percent, all_avg_ltv, all_liquidatable_percent, all_prices_deltas)

    # plot pricing for having some visual insight of the whole system price hist.
    if PLOT_PRICE:
        logger.plot_price_line_graph(df_system)

    

def recap(system, users, troves):
    print("")
    print("")
    print("")
    print("### END OF SIM RECAP ###")
    print("")
    print("")
    print("Ending TCR")
    print(system.get_tcr())

    print("")
    print("Ending Price")
    print(system.get_price())

    print("")
    print("No of redemptioms")
    print(system.redemp_tracking)

    insolvent_troves = 0

    for trove in troves:
        if not trove.is_solvent():
            insolvent_troves += 1
    
    print("")
    print("")
    print("Insolvent Troves %")
    print(insolvent_troves / len(troves) * 100)
    

def get_avg(list):
    acc = 0

    for val in list:
        acc += val
    
    return acc / len(list)


def recap_extended_avg(
        all_avg_bad_debt_percent, all_avg_ltv, all_liquidatable_percent, all_prices_deltas
):
    
    print("")
    print("")
    print("all_avg_bad_debt_percent", get_avg(all_avg_bad_debt_percent))

    print("")
    print("")
    print("AVG TCR", 100 / get_avg(all_avg_ltv))

    print("")
    print("")
    print("AVG Percent of CDPs that can be liquidated", get_avg(all_liquidatable_percent))

    print("")
    print("")
    print("AVG Delta between Price and Amount out for 1 unit", get_avg(all_prices_deltas))