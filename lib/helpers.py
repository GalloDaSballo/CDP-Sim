import requests


def get_cg_price():
    url = "https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses=0xae7ab96520de3a18e5e111b5eaab095312d7fe84&vs_currencies=btc"

    res = requests.get(url)
    res.raise_for_status()

    return res.json()["0xae7ab96520de3a18e5e111b5eaab095312d7fe84"]["btc"]
