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
        self.ex_dict["bittrex"] = Bittrex(secrets.TEST_BITTREX_KEY, secrets.TEST_BITTREX_SECRET)
        self.ex_dict["kraken"] = Kraken(secrets.TEST_KRAKEN_KEY, secrets.TEST_KRAKEN_SECRET)
        self.ex_dict["exmo"] = Exmo(secrets.TEST_EXMO_KEY, secrets.TEST_EXMO_SECRET)

        if settings.GDAX_PRODUCTION:
            self.ex_dict["gdax"] = Gdax(secrets.TEST_GDAX_KEY, secrets.TEST_GDAX_SECRET, secrets.TEST_GDAX_PASSPHRASE)
            #self.ex_dict["gdax"] = Gdax(secrets.LIVE_GDAX_KEY, secrets.LIVE_GDAX_SECRET, secrets.LIVE_GDAX_PASSPHRASE)
        else:
            self.ex_dict["gdax"] = Gdax(secrets.TEST_GDAX_KEY, secrets.TEST_GDAX_SECRET, secrets.TEST_GDAX_PASSPHRASE,url="https://api-public.sandbox.gdax.com")

    ###possibly change to architecture where we have the working orders as objects of the exchange container,
    ###not sure how much it actually matters which things the working orders are a part of

    def create_wo(self, wo_params_dict):
        """
        create a working order and run it in a separate thread
        all necessary arguments are within the working order object itself
        :param wo_params_dict: 
        :return: 
        """
        if len(self.wos_dict) > 0:
            print "len(self.wos_dict) > 0"
            return
        # required_spread, quantity, buy_ex, send_ex
        if wo_params_dict["buy_on"] == wo_params_dict["send_to"]:
            return
        wo_obj = WorkingOrder(wo_params_dict)
        wo_obj.continue_loop = True
        self.wos_dict[wo_obj.external_working_order_id] = wo_obj
        time_readable = datetime.datetime.now().strftime("%m-%d %H:%M")
        wo_dict = {"neg_timestamp": -time.time(), "timestamp": time.time(), "time_readable": time_readable,
                   "wo_id": str(wo_obj.external_working_order_id), "required_spread": str(wo_obj.required_spread),
                   "quantity": str(wo_obj.total_quantity)}
        response = firebase_push_value(["working_orders"], wo_dict)
        t = threading.Thread(target=self.working_thread_general, args=[wo_obj])
        t.start()
        # self.create_wo_log(wo_obj)

    def working_thread_general(self, wo_obj):
        wo_obj.counter = 0
        while True:
            wo_obj.counter += 1
            if not wo_obj.continue_loop:
                self.working_order_log("cancelled continue loop bp 1", wo_obj)
                break

            current_spread = self.get_spread(wo_obj)
            print "current_spread: %s" % current_spread
            print "required_spread: %s" % wo_obj.required_spread
            self.working_order_log("actual_spread: " + str(current_spread), wo_obj)

            if self.check_price_criteria_met(current_spread, wo_obj.required_spread):
                # TODO: hardcoding all currencies to btc for now
                self.initiate_arbitrage(self.ex_dict[wo_obj.buy_on], self.ex_dict[wo_obj.send_to], wo_obj.total_quantity, Currencies.bitcoin)

                break
            else:
                time.sleep(5)

    def initiate_arbitrage(self, buy_on_exchange,  send_to_exchange, amount, currency):
                print "Initiating btc buy order for %s" % amount
                buy_status = buy_on_exchange.buy(currency, amount)
                print buy_status
                print "Waiting for order to complete"
                buy_on_exchange.wait_for_order(buy_status["id"])
                print buy_sta