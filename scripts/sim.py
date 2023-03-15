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
from lib.logger import GenericLogger, GenericEntry

from classes.pool import Pool
from classes.ebtc import Ebtc
from classes.users.borrower import Borrower
from classes.users.stat_arber import StatArber


MAX_BPS = 10_000
SECONDS_SINCE_DEPLOY = 0
SECONDS_PER_TURN = 12 ## One block in POS
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
    
    - Write the logic in take_action and you will be able to extend the rest of the system


    TODO:
    - Basic invariant / unit tests to make sure system is fine
    - Extend more Classes to Sim
    - Decide if we want to add UniV2 / V3 Pool and simulate arbs there as well
"""


"""
    LIBRARIES
"""

## CR

def get_icr(coll, debt, price):
  """
    Assume price is denominated in debt
    e.g. coll / price = debt value
  """
  return coll / debt / price * 100


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
START_COLL = 1_000_000e18 ## NOTE: No point in randomizing it as all insights are % of this

PRICE = 13

PRICE_VOLATILITY = 100 ## 1%


## RISK VALUES ##
## Below this you get liquidated
MCR = 110 

## If TCR < CCR we enter recovery mode
CCR = 150

## In recovery mode, troves below CLR are liquidated
## NOTE: Set to CCR, tweak it if you want
CLR = CCR





"""
    CLASSES
"""
    
  
    


class Trove:
    def __init__(self, owner, system):
        self.collateral = 0
        self.debt = 0
        self.last_update_ts = system.time
        self.owner = owner
        self.system = system
        self.id = str(random.randint(1, 10**24)) ## Although PRGN odds of clash are unlikely

    def __repr__(self):
        return str(self.__dict__)

    def local_collateral_ratio(self):
        return self.debt * MAX_BPS / self.collateral

    def deposit(self, amount):
        ## Internal
        assert self.is_solvent()
        self.system.total_deposits += amount
        self.collateral += amount

        ## Caller
        self.owner.spend(self.id, False, amount, "Deposit")

        ## Logging
        self.system.logger.add_entry([self.system.time, "Trove" + self.id, "Deposit", amount])

    def withdraw(self, amount):
        ## Internal
        self.collateral -= amount
        assert self.is_solvent()
        
        ## Caller
        self.owner.receive(self.id, False, amount, "Withdraw")

        ## Logging
        self.system.logger.add_entry([self.system.time, "Trove" + self.id, "Withdraw", amount])

    def borrow(self, amount):
        self.debt += amount
        assert self.is_solvent()
        self.system.total_debt += amount
        assert self.system.is_solvent()

        self.owner.receive(self.id, True, amount, "Borrow")

        ## Logging
        self.system.logger.add_entry([self.system.time, "Trove" + self.id, "Borrow", amount])


    def repay(self, amount):
        self.debt -= amount
        assert self.is_solvent()
        self.system.total_debt -= amount
        assert self.system.is_solvent()

        self.owner.spend(self.id, True, amount, "Repay")

        ## Logging
        self.system.logger.add_entry([self.system.time, "Trove" + self.id, "Repay", amount])

    def liquidate(self, amount, caller):
        ## Only if not owner
        if caller == self.owner:
            return False
        
        ## TODO: Incorrect / Missing piece / Math
        ## Spend Debt to repay
        caller.spend(self.id, True, amount, "Liquidate")
        ## Receive Collateral for liquidation
        caller.receive(self.id, False, amount, "Liquidate")

        ## Logging
        self.system.logger.add_entry([self.system.time, "Trove", "Liquidate", amount])

        return 0

    ## SECURITY CHECKS
    def is_trove(self):
        return True

    def max_borrow(self):
        ## TODO: use function that is same as system
        return self.collateral * self.system.get_price() * MAX_LTV / MAX_BPS

    def is_solvent(self):
        if self.debt == 0:
            return True
        ## Strictly less to avoid rounding or w/e
        return self.debt < self.max_borrow()

    def is_underwater(self):
        if self.debt == 0:
            return False
        
        return self.debt > self.collateral * self.system.get_price()

    def get_cr(self):
        return get_icr(self.collateral, self.debt, self.system.get_price())

    
    
    def current_ltv(self):
        if self.collateral == 0 or self.system.get_price() == 0:
            return 0
        
        return self.debt / (self.collateral * self.system.get_price())




      








           




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

    # init the system
    logger = GenericLogger("sim", ["Time", "Name", "Action", "Amount"])
    pool = Pool(1000, 1000, 1000, 300)

    system = Ebtc(logger, pool)

    # init a user with a balance of 100
    user_1 = Borrower(system, 100)
    user_2 = StatArber(system, 100)

    # init a trove for this user
    trove_1 = Trove(user_1, system)
    trove_2 = Trove(user_2, system)

    assert system.time == 0
    

    ## Turn System
    users = [user_1, user_2]
    troves = [trove_1, trove_2]

    system.take_turn(users, troves)
    assert system.time == SECONDS_PER_TURN

    system.take_turn(users, troves)

    pprint(logger)

    ## Test for Feed and solvency
    assert trove_1.is_solvent()

    print("LTVL before drop", trove_1.current_ltv())
    print("LTVL before drop", trove_2.current_ltv())

    ## Minimum amount to be insolvent ## On max leverage
    system.set_price(system.get_price() * (MAX_BPS - MAX_LTV - 1) / MAX_BPS)


    print("LTVL after drop", trove_1.current_ltv())

    ## Insane drop
    system.set_price(0.0001)

    ## User will not invest
    system.take_turn(users, troves)

    print("Debt", trove_1.debt)
    print("Max Debt", trove_1.max_borrow())
    

    ## Because one trove let's verify consistency
    assert system.total_debt == trove_1.debt + trove_2.debt
    print("system.max_borrow()", system.max_borrow())
    print("trove_1.max_borrow()", trove_1.max_borrow())
    print("trove_2.max_borrow()", trove_2.max_borrow())
    assert system.max_borrow() == trove_1.max_borrow() + trove_2.max_borrow()

    assert not trove_1.is_solvent()

    pprint(logger)