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

gdax_global = Gdax(TEST_GDAX_KEY, TEST_GDAX_SECRET, TEST_GDAX_PASSPHR