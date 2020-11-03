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
                r = requests.get(BASE_URL + '/' + str(command) + '/', auth=self.auth)
            else:
                r = requests.post(BASE_URL + '/' + command + '/', data=json.dumps(kwargs), auth=self.auth)
            after_time = time.time()
            time_elapsed = after_time - before_time
            self.queue.append((time.time(), time_elapsed))
        else:
            before_time = time.time()
            r = requests.get(BASE_URL + '/' + command + '/')  # no authentication needed
            after_time = time.time()
            time_elapsed = after_time - before_time
            self.queue.append((time.time(), time_elapsed))

        #t = threading.Thread(target=self.update_queue)
        #t.start()
        #t = threading.Thread(target=record_log_in_firebase_func, args=[result, request_url, param, self.api_calls_per_second, time_elapsed, wo_id])
        #t.start()
        print r.json()
        return r.json()

    def balance(self, account_id=''):
        return self.api_call(call='accounts', command='accounts', param=None, action=None)

    def ticker(self, market):
        """
        :param market: String literal for the market (ex: BTC/ETH)
        :type market: str
        :return: Current values for given market in JSON
        :rtype : dict
        """
        #wo_id, command, param = None, action = ''
        print market
        return self.api_call(call='ticker', command='products/{}/ticker'.format(market), param=None, action=None)

    def update_dicts(self, bids_dict, asks_dict, data, ask_or_bid):
        if ask_or_bid == "bids":
            bids_dict[data[0]] = data[1]
        elif ask_or_bid == "asks":
            asks_dict[data[0]] = data[1]

    def update_queue(self):
        TIME_WINDOW_SECS = 600.0
        avg_latency = 0.0
        try:
            while self.queue[0][0] < time.time() - TIME_WINDOW_SECS:
                self.queue.popleft()
        except IndexError:
            print "there are no records in the queue."

        for item in self.queue:
            avg_latency += item[1]
        if len(self.queue):
            avg_latency = avg_latency/len(self.queue)

        dfds = time.time() - self.start_time
        if dfds < TIME_WINDOW_SECS:
            self.api_calls_per_second = float(len(self.queue)) / float(dfds)
        else:
            self.api_calls_per_second = float(len(self.queue)) / float(TIME_WINDOW_SECS)
        '''
        set_child_value(["bitfinex_gdax", "num_calls_per_sec"], self.api_calls_per_second)
        if avg_latency:
            set_child_value(["bitfinex_gdax", "avg_latency"], avg_latency)
        '''

    def update_ticker(self):
        return_val = self.ticker()
        if type(return_val) != dict:
            return_val = json.loads(return_val)
        self.ask_price = return_val["ask"]
        self.bid_price = return_val["bid"]

    def update_ticker_thread(self):
        counter = 0
        while self.continue_threads:
            counter += 1
            if counter % 20000 == 0:
                self.update_queue()
                #ws_price_health_check(self.ask_price, self.bid_price)
            try:
                if time.time() - self.ws.last_update_time < 8:
                    self.ask_price = self.ws.best_ask
                    self.bid_price = self.ws.best_bid
                else:
                    print "did update ticker"
                    self.update_ticker()
                    #set_child_value(["gdax", "prices", "btc", "bid"], self.bid_price)
                    #set_child_value(["gdax", "prices", "btc", "ask"], self.ask_price)
                    time.sleep(2.1)
                if abs(self.old_ask - self.ask_price) > .5 or abs(self.old_bid - self.bid_price) > .5:
                    self.old_ask = self.ask_price
                    self.old_bid = self.bid_price
                    firebase_dict = {
                        "bid": self.bid_price,
                        "ask": self.ask_price,
                        "last_update_time": time.time()
                    }
                    #set_child_value(["gdax", "prices", "btc"], firebase_dict)
            except:
                print "timeout or error gdax"
            time.sleep(.001)

    def maintain_websocket_thread(self):
        self.ws = GDAXWebsocket()
        RESTART_INTERVAL = 2000
        while True:
            try:
                self.ws.connect()
                start_time = time.time()
                while self.ws.ws.sock.connected:
                    time.sleep(1)
                    if time.time() - start_time > RESTART_INTERVAL:
                        break
                self.ws.subscribed_to_orderbook = False
                self.ws.exit()
                time.sleep(2)
            except Exception as ex:
                print "except location 1"
                print ex

    def best_bid_ask(self, bids_dict, asks_dict):
        bid_list = []
        for item in bids_dict:
            bid_list.append((item, bids_dict[item]))
        bid_list.sort(key=itemgetter(0), reverse=True)
        best_bid = bid_list[0][0]
        ask_list = []
        for item in asks_dict:
            ask_list.append((item, asks_dict[item]))
        ask_list.sort(key=itemgetter(0))
        best_ask = ask_list[0][0]
        return best_bid, best_ask

class GDAXWebsocket(object):

    def __init__(self, api_key=TEST_GDAX_API_KEY, api_secret=TEST_GDAX_API_SECRET, api_passphrase=TEST_GDAX_API_PASSPHRASE):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.old_best_bid = -1
        self.old_best_ask = -1
        self.best_bid = -1
        self.best_ask = -1
        self.bids_dict = {}
        self.asks_dict = {}
        self.sent_subscribed_to_room = False
        self.exited = False
        self.stop = False
       