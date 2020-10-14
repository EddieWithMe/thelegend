
"""
   See https://bittrex.com/Home/Api
"""

import time
import hmac
import hashlib

from ..abstract import Exchange

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

try:
    from Crypto.Cipher import AES
except ImportError:
    encrypted = False
else:
    import getpass
    import ast
    import json

    encrypted = True

from GCE.currency_classes.abstract import Currencies
from GCE.currency_classes.bitcoin.bitcoin import Bitcoin
from GCE.currency_classes.ethereum.ethereum import Ethereum
from GCE.currency_classes.ethereum_classic.ethereum_classic import EthereumClassic
from GCE.currency_classes.litecoin.litecoin import Litecoin

import requests

BUY_ORDERBOOK = 'buy'
SELL_ORDERBOOK = 'sell'
BOTH_ORDERBOOK = 'both'

TRADE_FEE = 0.0025

TICKINTERVAL_ONEMIN = 'oneMin'
TICKINTERVAL_FIVEMIN = 'fiveMin'
TICKINTERVAL_HOUR = 'hour'
TICKINTERVAL_THIRTYMIN = 'thirtyMin'
TICKINTERVAL_DAY = 'Day'

ORDERTYPE_LIMIT = 'LIMIT'
ORDERTYPE_MARKET = 'MARKET'

TIMEINEFFECT_GOOD_TIL_CANCELLED = 'GOOD_TIL_CANCELLED'
TIMEINEFFECT_IMMEDIATE_OR_CANCEL = 'IMMEDIATE_OR_CANCEL'
TIMEINEFFECT_FILL_OR_KILL = 'FILL_OR_KILL'

CONDITIONTYPE_NONE = 'NONE'
CONDITIONTYPE_GREATER_THAN = 'GREATER_THAN'
CONDITIONTYPE_LESS_THAN = 'LESS_THAN'
CONDITIONTYPE_STOP_LOSS_FIXED = 'STOP_LOSS_FIXED'
CONDITIONTYPE_STOP_LOSS_PERCENTAGE = 'STOP_LOSS_PERCENTAGE'

API_V1_1 = 'v1.1'
API_V2_0 = 'v2.0'

BASE_URL_V1_1 = 'https://bittrex.com/api/v1.1{path}?'
BASE_URL_V2_0 = 'https://bittrex.com/api/v2.0{path}?'

PROTECTION_PUB = 'pub'  # public methods