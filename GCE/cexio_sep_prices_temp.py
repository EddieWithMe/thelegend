import httplib
# from exmo import ExmoAPI
import urllib

import ccxt

from exchange_classes.bittrex.bittrex import *
# def __init__(self, key, b64secret, passphrase, api_url="https://api.gdax.com"):
from exchange_classes.cex.cex import Cex
from exchange_classes.gdax.gdax import Gdax
from secrets import TEST_CEX_KEY, TEST_CEX_SECRET, TEST_CEX_UID, \
    TEST_GDAX_KEY, TEST_GDAX_SECRET, TEST_GDAX_PASSPHRASE, TEST_EXMO_KEY, TEST_EXMO_SECRET, TEST_BITTREX_KEY, \
    TEST_BITTREX_SECRET, TEST_KRAKEN_KEY, TEST_KRAKEN_SECRET
from firebase import set_child_value

gdax_global = Gdax(TEST_GDAX_KEY, TEST_GDAX_SECRET, TEST_GDAX_PASSPHRASE)
cex_global = Cex(TEST_CEX_UID, TEST_CEX_KEY, TEST_CEX_SECRET)
my_bittrex = Bittrex(TEST_BITTREX_KEY, TEST_BITTREX_SECRET)
krk_global = ccxt.kraken({
    'apiKey': TEST_KRAKEN_KEY,
    'secret': TEST_KRAKEN_SECRET
})
#exmo_global = ExmoAPI(TEST_EXMO_KEY, TEST_EXMO_SECRET)
def RRR():

    api_key = TEST_EXMO_KEY
    api_secret = TEST_EXMO_SECRET
    nonce = int(round(time.time() * 1000))
    params = {"nonce": nonce}
    params = urllib.urlencode(params)
    H = hmac.new(api_secret, digestmod=hashlib.sha512)
    H.update(params)
    sign = H.hexdigest()
    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Key": api_key,
               "Sign": sign}
    conn = httplib.HTTPSConnection("api.exmo.com")
    conn.request("POST", "/v1/user_info", params, headers)
    response = conn.getresponse()
    return_val = json.load(response)
    conn.close()
    return return_val

def prices():
    try:
        response = requests.get("https://bittrex.com/api/v1.1/public/getmarketsummary?market=usdt-btc")
        json_r = json.loads(response.text)
        result_dict = json_r["result"][0]
        bid = result_dict["Bid"]
        ask = result_dict["Ask"]
        firebase_dict = {
            "bid": bid,
            "ask": ask,
            "last_update_time": time.time()
        }
        set_child_value(["BITTREX", "prices", "btc"], firebase_dict)
        response = requests.get("https://api.exmo.com/v1/ticker/")
        json_r = json.loads(response.text)
        btscusd_dict = json_r["BTC_USD"]
        bid = btscusd_dict["buy_price"]
        ask = btscusd_dict["sell_price"]
        firebase_dict = {
            "bid": bid,
            "ask": ask,
            "last_update_time": time.time()
        }
        set_child_value(["EXMO", "prices", "btc"], firebase_dict)
        response = requests.get("https://api.kraken.com/0/public/Trades?pair=XBTUSD")
        json_r = json.loads(response.text)
      