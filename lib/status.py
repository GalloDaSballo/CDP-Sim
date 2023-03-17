def get_icr(coll, debt, price):
  """
    Assume price is denominated in debt
    e.g. coll / price = debt value
  """
  return coll / debt / price * 100