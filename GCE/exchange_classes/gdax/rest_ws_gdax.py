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
                 "neg_timestamp":-time.time(), "api_rate":rate_of_calls,"time_elapsed":time_elapsed, "wo_i