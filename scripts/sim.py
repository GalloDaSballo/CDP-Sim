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
from classes.users.stat_arber import StatArber
from classes.users.flash_full_liquidator import FlashFullLiquidator


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


def main():

    # init the ebtc
    logger = GenericLogger("sim", ["Time", "Name", "Action", "Amount"])
    # make initial balances of the pool matching the "oracle" price from the ebtc system
    reserve_debt_balance = RESERVE_COLL_INITIAL_BALANCE * get_cg_price()
    pool = Pool(RESERVE_COLL_INITIAL_BALANCE, reserve_debt_balance, 1000, POOL_FEE)

    ebtc = Ebtc(logger, pool)

    # init a user with a balance of `STETH_COLL_BALANCE`
    user_1 = Borrower(ebtc, STETH_COLL_BALANCE)
    user_2 = StatArber(ebtc, STETH_COLL_BALANCE)
    liquidator = FlashFullLiquidator(ebtc)

    # init a trove for this user
    trove_1 = Trove(user_1, ebtc)
    trove_2 = Trove(user_2, ebtc)

    assert ebtc.time == 0

    ## Turn System
    users = [liquidator, user_1, user_2]
    troves = [trove_1, trove_2]

    ebtc.take_turn(users, troves)
    assert ebtc.time == SECONDS_PER_TURN

    ebtc.take_turn(users, troves)

    ## Test for Feed and solvency
    assert trove_1.is_solvent()

    print("LTV before drop", trove_1.current_ltv())
    print("LTV before drop", trove_2.current_ltv())

    ## Minimum amount to be insolvent ## On max leverage
    ebtc.set_price(ebtc.get_price() * (MAX_BPS - MAX_LTV - 1) / MAX_BPS)

    print("LTV after drop", trove_1.current_ltv())

    ## Insane drop in BTC price -> 0.5 stETH/BTC OR insane drop in ETH price ?
    ebtc.set_price(INSANE_RATIO_DROP)

    ## User will not invest
    ebtc.take_turn(users, troves)

    print("Debt", trove_1.debt)
    print("Max Debt", trove_1.max_borrow())

    ## Because one trove let's verify consistency
    print("ebtc.total_debt", ebtc.total_debt)
    print("trove_1.debt", trove_1.debt)
    print("trove_1.collateral", trove_1.collateral)
    print("trove_2.debt", trove_2.debt)
    # assert with `approx` minor decimals mismatch
    assert approx(ebtc.total_debt) == trove_1.debt + trove_2.debt

    print("ebtc.max_borrow()", ebtc.max_borrow())
    print("trove_1.max_borrow()", trove_1.max_borrow())
    print("trove_2.max_borrow()", trove_2.max_borrow())
    assert ebtc.max_borrow() == trove_1.max_borrow() + trove_2.max_borrow()

    # force another drop again to force trove insolvency, since we `take_turn` and modify the system price
    ebtc.set_price(INSANE_RATIO_DROP)

    assert not trove_1.is_solvent()

    logger.to_csv()
