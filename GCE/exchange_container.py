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
from firebase import set_in_firebase, firebase_push_value, f