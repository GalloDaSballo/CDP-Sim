from random import random

from lib.helpers import get_cg_price, price_after_shock

## TODO: Centralize settings and inject them in system

SECONDS_SINCE_DEPLOY = 0
INITIAL_FEED = 13
MAX_LTV = 8_500
MAX_BPS = 10_000
SECONDS_PER_TURN = 12  ## One block in POS


class Ebtc:
    def __init__(self, logger, pool):
        self.MAX_LTV = 15000  ## 150%
        self.FEE_PER_SECOND = 0  ## No fee for borrows
        self.ORIGINATION_FEE = 50  ## 50BPS
        self.CCR = 150

        self.total_deposits = 0
        self.total_debt = 0
        self.next_price = get_cg_price()
        # feed is assumed to be stETH/BTC
        self.price = get_cg_price()
        self.time = SECONDS_SINCE_DEPLOY
        self.turn = 0

        self.pool = pool

        self.logger = logger

    def __repr__(self):
        return str(self.__dict__)

    def get_tcr(self):
        # https://github.com/liquity/dev/blob/main/packages/contracts/contracts/Dependencies/LiquityBase.sol#L74-L80
        return (self.total_deposits * self.price) / self.total_debt * 100

    def max_borrow(self):
        return (self.total_deposits * self.price) * MAX_LTV / MAX_BPS

    def is_in_emergency_mode(self):
        # https://github.com/liquity/dev/blob/main/packages/contracts/contracts/Dependencies/LiquityBase.sol#L83-L87
        return self.get_tcr() < self.CCR

    def is_solvent(self):
        ## NOTE: Strictly less to avoid rounding, etc..
        ## TODO: Prob refactor
        return self.total_debt < self.max_borrow()

    def is_underwater(self):
        return self.total_debt > self.max_borrow()

    def get_price(self):
        return self.price

    def set_price(self, value):
        old_price = self.price
        ## TODO: Consider adding % Change function vs hardcoded setter
        self.price = value

        self.logger.add_entry([self.time, "System", "Price Change", value])

        # Update pool pricing via manipulating reserves
        price_change = (value - old_price) / old_price * 100

        current_reserve_coll = self.pool.reserve_x
        current_reserve_debt = self.pool.reserve_y

        if price_change < 0:
            # update debt reserve
            self.pool.set_price(current_reserve_coll, current_reserve_coll * self.price)
        else:
            # update coll reserve
            self.pool.set_price(current_reserve_debt / self.price, current_reserve_debt)

    def get_next_price(self):
        return price_after_shock(self.price)

    def take_turn(self, users, troves):
        ## Increase counter
        self.next_turn()
        print("Turn", self.turn, ": Second: ", self.time)

        ## Do w/e
        self.sort_users(users)

        ## Update Price from previous turn
        self.price = self.next_price

        ## Find next price for arbitrageurs to front-run
        self.next_price = self.get_next_price()

        ## Let users take action
        self.take_actions(users, troves)

        ## End of turn checks
        if not self.is_solvent():
            print("INSOLVENT")

    def sort_users(self, users):
        def get_key(user):
            ## TODO: Swing size (+- to impact randomness, simulate sorting, front-running etc..)
            ## Technically should sort by type as to allow some variance but not too much
            ## Alternatively could use PRNG where 99 gives 99% to win but still 1% chance to lose
            ## TODO: look into PRNG
            ## Actualy just have a different ADDEND in the speed so that arbers are faster
            return user.speed

        users.sort(key=get_key)

    def take_actions(self, users, troves):
        ## TODO: Add User Decisions making / given the list of all trove have user do something
        for user in users:
            user.take_action(self.turn, troves, self.pool)

    def next_turn(self):
        self.time += SECONDS_PER_TURN
        self.turn += 1
