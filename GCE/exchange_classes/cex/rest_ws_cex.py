
#https://github.com/matveyco/cex.io-api-python

"""
    See https://cex.io/rest-api
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
from GCE.firebase import set_in_firebase, set_child_value, firebase_read_value, firebase_push_value
import sys
import datetime

BASE_URL = 'https://cex.io/api/%s/'
PUBLIC_COMMANDS = {
    'currency_limits',
    'ticker',
    'last_price',
    'last_prices',
    'convert',
    'price_stats',
    'order_book',
    'trade_history'
}

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

class CexioApi:
    def update_ticker_thread(self):
        counter = 0
        while self.continue_threads:
            counter += 1
            if counter % 20000 == 0:
                self.update_queue()
                ws_price_health_check(self.ask_price, self.bid_price)
            try:
                if time.time() - self.ws.last_update_time < 8:
                    self.ask_price = self.ws.best_ask
                    self.bid_price = self.ws.best_bid
                else:
                    print "did update ticker"
                    self.update_ticker()
                    set_child_value(["cexio", "prices", "btc", "bid"], self.bid_price)
                    set_child_value(["cexio", "prices", "btc", "ask"], self.ask_price)
                    time.sleep(2.1)
                if abs(self.old_ask - self.ask_price) > .5 or abs(self.old_bid - self.bid_price) > .5:
                    self.old_ask = self.ask_price
                    self.old_bid = self.bid_price
                    firebase_dict = {
                        "bid": self.bid_price,
                        "ask": self.ask_price,
                        "last_update_time": time.time()
                    }
                    set_child_value(["cexio", "prices", "btc"], firebase_dict)
            except:
                print "timeout or error cexio"
            time.sleep(.001)

    def maintain_websocket_thread(self):
        self.ws = CexioWebsocket(self.api_key, self.api_secret)
        RESTART_INTERVAL = 2000
        while True:
            try:
                self.ws.connect()
                start_time = time.time()
                while (self.ws.ws.sock.connected):
                    time.sleep(1)
                    if time.time() - start_time > RESTART_INTERVAL:
                        break
                self.ws.subscribed_to_orderbook = False
                self.ws.exit()
                time.sleep(2)
            except Exception as ex:
                print "except location 1"
                print ex

    def __init__(self, username, api_key, api_secret):
        self.next_call_time = 0
        self.username = username
        self.api_key = api_key
        self.api_secret = api_secret
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

        t = threading.Thread(target=self.maintain_websocket_thread)
        t.start()

        t = threading.Thread(target=self.update_ticker_thread)
        t.start()

    @property
    def __nonce(self):
        while time.time() < self.next_call_time:
            time.sleep(.03)
        nonce = str(int(time.time() * 1000)+200000)
        self.next_call_time = time.time() +.41
        return nonce

    #can use something v similar for websocket
    def __signature(self, nonce):
        message = nonce + self.username + self.api_key
        signature = hmac.new(bytearray(self.api_secret.encode('utf-8')), message.encode('utf-8'),
                             digestmod=hashlib.sha256).hexdigest().upper()
        return signature

    def discontinue_threads(self):
        self.continue_threads = False


    def __post(self, url, param):
        result = requests.post(url, data=param, headers={'User-agent': 'bot-cex.io-' + self.username}).json()
        return result

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

        """
        :param command: Query command for getting info
        :type commmand: str
        :param param: Extra options for query
        :type options: dict
        :return: JSON response from CEX.IO
        :rtype : dict
        """

        if command not in PUBLIC_COMMANDS:
            nonce = self.__nonce
            param.update({
                'key': self.api_key,
                'signature': self.__signature(nonce),
                'nonce': nonce
            })

        request_url = (BASE_URL % command) + action
        before_time = time.time()
        result = self.__post(request_url, param)
        after_time = time.time()
        time_elapsed = after_time - before_time

        self.queue.append((time.time(), time_elapsed))

        t = threading.Thread(target=self.update_queue)
        t.start()
        t = threading.Thread(target=record_log_in_firebase_func, args=[result, request_url, param, self.api_calls_per_second, time_elapsed, wo_id])
        t.start()
        return result

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

        set_child_value(["bitfinex_cexio", "num_calls_per_sec"], self.api_calls_per_second)
        if avg_latency:
            set_child_value(["bitfinex_cexio", "avg_latency"], avg_latency)

    def update_ticker(self):
        return_val = self.ticker()
        if type(return_val) != dict:
            return_val =json.loads(return_val)
        self.ask_price = return_val["ask"]
        self.bid_price = return_val["bid"]

    def get_ask_price(self):
        return self.ws.best_ask

    def get_bid_price(self):
        return self.ws.best_bid


    def ticker(self, market='BTC/USD'):
        """
        :param market: String literal for the market (ex: BTC/ETH)
        :type market: str
        :return: Current values for given market in JSON
        :rtype : dict
        """
        #wo_id, command, param = None, action = ''

        return self.api_call(command='ticker',param=None,action=market)

    @property
    def balance(self):
        #return self.api_call('','balance')
        return self.api_call(command='balance')

    @property
    def get_myfee(self):
        #return self.api_call('','get_myfee')
        return self.api_call(command='get_myfee')

    @property
    def currency_limits(self):
        #return self.api_call('','currency_limits')
        return self.api_call(command='currency_limits')

    def open_orders(self):
        #return self.api_call('','open_orders', {})
        return self.api_call(command='open_orders')

    def active_order_status(self):
        orders_list = {'orders_list':self.ids_should_be_in_open_orders()}
        #return self.api_call('','active_orders_status', orders_list)
        return self.api_call(command='active_orders_status',param=orders_list)

    def cancel_order(self, order_id, wo_id=''):
        return self.api_call(wo_id=wo_id,command='cancel_order', param={'id': order_id})

    def cancel_all_working_orders(self):
        for working_order_key in self.working_order_dict:
            working_order = self.working_order_dict[working_order_key]
            working_order.continue_loop = False

    def cancel_working_order(self, identifier):
        working_order = self.working_order_dict[identifier]
        order_id_of_working = working_order.working_order_id
        error_count = 0
        while True:
            return_val = self.api_call(wo_id=identifier, command='cancel_order', param={'id': order_id_of_working})
            #return_val = self.api_call(identifier,'cancel_order', {'id': order_id_of_working})
            if "Order not found" in str(return_val):
                return "Order not found"
            if error_count > 3:
                return "cancel not successfully made"
            if return_val == True:
                return return_val
            else:
                error_count +=1
                time.sleep(1.2)

    def cancel_orders(self, market='BTC/USD'):
        #return self.api_call('','cancel_orders', None, market)
        return self.api_call(command='cancel_orders', action=market)

    def buy_limit_order(self, wo_uuid, amount, price, market='BTC/USD'):

        params = {
            'type': 'buy',
            'amount': amount,
            'price': price
        }

        #return self.api_call('','place_order', params, market)
        return self.api_call(wo_id=wo_uuid, command='place_order', param=params, action=market)

    def sell_limit_order(self, wo_uuid, amount, price, market='BTC/USD'):

        params = {
            'type': 'sell',
            'amount': amount,
            'price': price
        }

        #return self.api_call('','place_order', params, market)
        return self.api_call(wo_id=wo_uuid, command='place_order', param=params, action=market)


    def open_positions(self, market='BTC/USD'):
        #return self.api_call('','open_positions', None, market)
        return self.api_call(command='open_positions', action=market)