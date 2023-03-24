import requests

from random import normalvariate, seed, randint


def get_cg_price():
    # url = "https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses=0xae7ab96520de3a18e5e111b5eaab095312d7fe84&vs_currencies=btc"

    # res = requests.get(url)
    # res.raise_for_status()

    # # return res.json()["0xae7ab96520de3a18e5e111b5eaab095312d7fe84"]["btc"]
    return 13


def price_after_shock(prev_price):
    # https://github.com/liquity/dev/blob/main/packages/contracts/macroModel/macro_model.py#L100-L102
    period = 24 * 365
    rdn = randint(0, period)
    sd_ether = 0.02
    seed(2019375 + 10000 * rdn)
    shock_ether = normalvariate(0, sd_ether)
    return prev_price * (1 + shock_ether)
