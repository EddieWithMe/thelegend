#https://github.com/matveyco/cex.io-api-python
#PUBLIC ENDPOINTS
#We throttle public endpoints by IP: 3 requests per second, up to 6 requests per second in bursts.

#PRIVATE ENDPOINTS
#We throttle private endpoints by user ID: 5 requests per second, up to 10 requests per second in bursts.

"""
    See https://docs.gdax.com/#ids
"""
import websocket
from operator import itemgetter
import hmac
import hashlib
import time
import requests
import threading
import json
from collections import deque
#from firebase import set_in_firebase, set_child_value, firebase_read_value, firebase_push_value
from security.secrets import TEST_GDAX_API_KEY, TEST_GDAX_API_SECRET, TEST_GDAX_API_PASSPHRASE
import base64
from requests.auth import AuthBase
import sys
import datetime
import logging
logging.basicConfig()

BASE_URL = u'https://api.gdax.com'
PUBLIC_CALLS = {u'products', u'product_order_book', u'ticker', u'product_trades', u'product_historic_rates', u'product_24hr_stats', u'currencies', u'time'}
PRIVATE_CALLS = {u'account':u'GET', u'accounts':u'GET', u'account_history':u'GET', u'account_holds':u'GET', u'history_pagination':u'GET', u'holds_pagination':u'GET', u'buy':u'POST', u'sell':u'POST', u'cancel_order':u'POST', u'cancel_all':u'POST'}

'''
def record_log_in_firebase_func(result, request_url, param, rate_of_calls, time_elapsed, wo_id):
    push_dict = {"result":str(result),"request_url":str(request_url),"param":str(param), "timestamp":time.time(),
                 "neg_timestamp":-time.time(), "api_rate":rate_of_calls,"time_elapsed":time_elapsed, "wo_id":wo_id}
    firebase_push_value(["cexio_bitfinex", "api_call_log"], push_dict)

def ws_price_health_check(ask_price, bid_price):
    response_var = requests.get("https://cex.io/api/ticker/BTC/USD")
    response_json = json.loads(response_var.text)
    test_variable = abs(float(response_json["ask"]) - ask_price) * 100 / ask_price
    test_variable_2 = abs(float(response_json["bid"]) - bid_price) * 100 / bid_price
    if test_variable > 1 and test_variable_2 > 1:
        # health warning
        print "may be problematic"
    else:
        print "prices healthy"
'''

class GDAXAPI(object):

    def __init__(self, api_key=TEST_GDAX_API_KEY, api_secret=TEST_GDAX_API_SECRET, api_passphrase=TEST_GDAX_API_PASSPHRASE):
        self.next_call_time = 0
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.ask_price = 0
        self.bid_price = 0
        self.old_ask = 0
        self.old_bid = 0
        self.max_working_orders = 5
        self.working_order_dict = {}
        self.continue_threads = True
        self.api_calls_this_time_period = 0.0
        self.time_period_length_in_seconds = 180
        self.time_period_start = 0
        self.api_calls_per_second = 0.0
        self.queue = deque()
        self.start_time = time.time()
        self.test_mode_active = False
        self.auth = GdaxAuth(api_key, api_secret, api_passphrase) #todo: add this scheme to cexio
        self.ws = None
        t = threading.Thread(target=self.maintain_websocket_thread)
        t.start()

        t = threading.Thread(target=self.update_ticker_thread)
        t.start()

    def discontinue_threads(self):
        self.continue_threads = False

    def api_call(self, **kwargs):
        if "wo_id" in kwargs:
            wo_id = kwargs["wo_id"]
        else:
            wo_id = ''
        command = kwargs["command"]
        if "param" in kwargs:
            param = kwargs["param"]
        else:
            param = {}
        if "action" in kwargs:
            action = kwargs["action"]
        else:
            action = ''
        if "call" in kwargs:
            call = kwargs["call"]
        else:
            call = ''
        """
        :param command: Query command for getting info
        :type commmand: str
        :param param: Extra options for query
        :type options: dict
        :return: JSON response from CEX.IO
        :rtype : dict
        """
        print command
        print call
        if call not in PUBLIC_CALLS:
            call_type = PRIVATE_CALLS[call]
            before_time = time.time()
            if call_type == 'GET':
