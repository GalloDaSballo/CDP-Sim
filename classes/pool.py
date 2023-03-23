from math import sqrt

## POOL For Swap

## NOTE: For UniV3 we can use Solidly Math
## Or alternatively just use infinite leverage at price point + .50% price impact

class Pool():
  def __init__(self, start_x, start_y, start_lp, fee):
    ## NOTE: May or may not want to have a function to hardcode this
    self.reserve_x = start_x ## Coll
    self.reserve_y = start_y ## Debt
    self.fee = fee

  def k(self):
    return self.x * self.y
  
  def get_price_out(self, is_x, amount):
    if (is_x):
      return self.get_price(amount, self.reserve_x, self.reserve_y)
    else:
      return self.get_price(amount, self.reserve_y, self.reserve_x)
    
  ## GET X to put in given Y out?
  ## Get price given X

  def recharge(self, percent):
    self.reserve_x += self.reserve_x * percent / 100
    self.reserve_y += self.reserve_y * percent / 100
  
  def set_price(self, reserve_x, reserve_y):
    ## TODO: Prob should change to move the reserves?
    self.reserve_x = reserve_x
    self.reserve_y = reserve_y

  
  def increase_price_of_debt(self, percent):
    assert percent < 100

    ## Debt is y
    ## To increase it's price, just increase the reserve_x by the percent
    self.reserve_x = self.reserve_x * percent / 100

  def increase_price_of_coll(self, percent):
    assert percent < 100
    
    ## Coll is x
    ## To increase it's price, just increase the reserve_y by the percent
    self.reserve_y = self.reserve_y * percent / 100

  ## UniV2 Formula, can extend the class and change this to create new pools
  def get_price(self, amount_in, reserve_in, reserve_out):
      amountInWithFee = amount_in * 997
      numerator = amountInWithFee * reserve_out
      denominator = reserve_in * 1000 + amountInWithFee
      amountOut = numerator / denominator

      return amountOut

  def amount_for_debt(self, amount_out_coll_required):
    return self.amount_in_give_out(amount_out_coll_required, self.reserve_x, self.reserve_y)
  
  def amount_in_give_out(self, amount_out, reserve_in, reserve_out):
    amount_in = reserve_in * amount_out / (reserve_out - amount_out)
    return amount_in

  def swap(self, caller, is_from_debt, amount_in):
    ## Spend
    caller.spend(self, is_from_debt, amount_in, "Swap Spend")

    ## Swap
    receive_amount = 0
    if is_from_debt:
      ## If is_from_debt we are buying coll
      receive_amount = self.swap_for_coll(amount_in)
    else:
      ## Else we are spending coll fro debt
      receive_amount = self.swap_for_debt(amount_in)
    
    ## Send back to caller
    caller.receive(self, not is_from_debt, receive_amount, "Swap Receive")

  
  def swap_for_coll(self, debt_in):
    amount_out = self.get_price(debt_in, self.reserve_y, self.reserve_x)

    self.reserve_y += debt_in
    self.reserve_x -= amount_out

    return amount_out


  def swap_for_debt(self, coll_in):
    amount_out = self.get_price(coll_in, self.reserve_x, self.reserve_y)

    self.reserve_x += coll_in
    self.reserve_y -= amount_out

    return amount_out
  
  def get_max_coll_before_next_price(self, next_price):
    return self.max_in_before_price_limit(next_price, self.reserve_x, self.reserve_y)
  
  def max_in_before_price_limit(self, price_limit, reserve_in, reserve_out):
    return reserve_out * price_limit - reserve_in

  def get_max_coll_before_next_price_sqrt(self, next_price):
    # proof: https://media.discordapp.net/attachments/1050808646801567764/1050817069953855508/Petro_Math.jpeg?width=844&height=1126
    return abs(
        sqrt(next_price * self.reserve_x * self.reserve_y) / next_price
        - self.reserve_x
    )

## TODO: Unit Tests