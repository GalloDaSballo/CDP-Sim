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
import math
import random
from rich.pretty import pprint
from pytest import approx

from lib.logger import GenericLogger, GenericEntry
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

PRICE_VOLATILITY = 100  ## 1%


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


def invariant_tests():
    ## TODO: Please fill these in
    """
    If I have X troves, then total debt is sum of each trove debt

    Total borrowed is sum of each trove

    Max_borrow is sum of max borrowed

    LTV is weighted average of each LTV = Sum LTV / $%

    If I take a turn, X seconds pass
    """

## TODO: % of degen vs stable
## TODO: % of liquidators vs stable
## TODO: % of Redeemers

NORMAL_COUNT = 100
DEGEN_COUNT = 1
STAT_ARBER = 1
REDEEM_ARBER = 1
LIQUIDATOR_COUNT = 1




def main():
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
        redeem_arbers.append(RedeemArber(ebtc, STETH_COLL_BALANCE))

    for x in range(LIQUIDATOR_COUNT):
        liquidators.append(FlashFullLiquidator(ebtc))


    assert ebtc.time == 0

    ## Turn System
    all_users = stat_arbers + redeem_arbers + liquidators + degens + users

    ## TODO: Remove
    ## Quick debug for unique id
    # for user in all_users:
    #     print(user.name)
    #     print(user.id)
    # return

    has_done_liq = False

    while not has_done_liq:
        try:
            ebtc.take_turn(all_users, troves)
        except Exception as e: 
            print(e)
            print("Exception let's end")
            break

    df_system, _, _ = logger.to_csv()

    # plot pricing for having some visual insight of the whole system price hist.
    logger.plot_price_line_graph(df_system)
