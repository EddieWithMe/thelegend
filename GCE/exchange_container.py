import datetime
import threading
import time
from exchange_classes.blockcypher import get_num_confirmations_transaction
import requests
import secrets
import settings
from exchange_classes.cex.cex import Cex
from exchange_classes.gdax.gdax import Gdax
from exchange_classes.bittrex.bittrex import Bittrex
from exchange_classes.kraken.kraken import Kraken
from exchange_classes.exmo.exmo import Exmo
from currency_classes.abstract import Currencies
from firebase import set_in_firebase, firebase_push_value, firebase_read_value

from working_order_class import WorkingOrder
ACTIVE_EXCHANGE_LIST = ["cexio", "gdax", "kraken", "bittrex", "exmo"]

# The allowed trading margin error between the amount placed as an order and the amount stage to be transfered to the
# desitnation exchange
ALLOWED_TRADE_TRANSFER_MARGIN_ERROR = 0.001


class Exchanges:
    def __init__(self):
        self.wos_dict = {}
        # for ex_name in ACTIVE_EXCHANGE_LIST:
        #    self.wos_dict[ex_name] = {}
        self.ex_dict = {}
        self.ex_dict["cex"] = Cex(secrets.TEST_CEX_UID, secrets.TEST_CEX_KEY, secrets.TEST_CEX_SECRET)
        self.ex_dict["bittrex"] = Bittrex(