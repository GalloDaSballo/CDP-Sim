import math
import random
from lib.names import name_list

SPEED_RANGE = 100

class User:
    def __init__(self, system, initial_balance_collateral):
        self.system = system
        self.collateral = initial_balance_collateral
        self.debt = 0
        self.name = random.choice(name_list)
        self.speed = math.floor(random.random() * SPEED_RANGE) + 1
        
        self.id = str(
            random.randint(1, 10**24)
        )  ## Although PRGN odds of clash are unlikely

    def __repr__(self):
        return str(self.__dict__)
    
    def spend(self, caller, is_debt, amount, label):
        if is_debt:
            self.debt -= amount

            ## Logging
            self.system.logger.add_entry([self.system.time, "User" + self.name, "Spent Debt", amount])

        
        else:
            self.collateral -= amount

            ## Logging
            self.system.logger.add_entry([self.system.time, "User" + self.name, "Spent Collateral", amount])
        

    
    def receive(self, caller, is_debt, amount, label):
        if is_debt:
            self.debt += amount

            ## Logging
            self.system.logger.add_entry([self.system.time, "User" + self.name, "Receive Debt", amount])

        
        else:
            self.collateral += amount

            ## Logging
            self.system.logger.add_entry([self.system.time, "User" + self.name, "Receive Collateral", amount])


    def get_debt(self):
        return self.debt

    def get_balance(self):
        return self.collateral

    def take_action(self, turn, troves, pool):
        print("User" , self.name, " Taking Action")
        print("turn ", turn)

        self.system.logger.add_entry([self.system.time, "User" + self.name, "Balance of Collateral", self.collateral])
        self.system.logger.add_entry([self.system.time, "User" + self.name, "Balance of Debt", self.debt])

  