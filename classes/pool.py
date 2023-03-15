## POOL For Swap

## NOTE: For UniV3 we can use Solidly Math
## Or alternatively just use infinite leverage at price point + .50% price impact

class Pool():
  def __init__(self, start_x, start_y, start_lp, fee):
    ## NOTE: May or may not want to have a function to hardcode this
    self.reserve_x = start_x
    self.reserve_y = start_y
    self.fee = fee

  def k(self):
    return self.x * self.y
  
  def get_price_out(self, is_x, amount):
    if (is_x):
      return self.get_price(amount, self.reserve_x, self.reserve_y)
    else:
      return self.get_price(amount, self.reserve_y, self.reserve_x)

  def recharge(self, percent):
    self.reserve_x += self.reserve_x * percent / 100
    self.reserve_y += self.reserve_y * percent / 100
  
  def set_price(self, reserve_x, reserve_y):
    """
        TODO: Prob should change to move the reserves?
    """
    self.reserve_x = reserve_x
    self.reserve_y = reserve_y

  ## UniV2 Formula, can extend the class and change this to create new pools
  def get_price(amount_in, reserve_in, reserve_out):
      amountInWithFee = amount_in * 997
      numerator = amountInWithFee * reserve_out
      denominator = reserve_in * 1000 + amountInWithFee
      amountOut = numerator / denominator

      return amountOut