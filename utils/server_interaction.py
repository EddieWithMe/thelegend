from __future__ import division

import hashlib
import hmac
import json
import logging
import time

from google.appengine.api import urlfetch

from models import TradeSettings
from security.secrets import OUR_API_KEY, OUR_API_SECRET

VALID_RESPONSE = [200, 201, 202]

PRODUCTION_SETTING = True

if PRODUCTION_SETTING:
    SERVER_URL = "http://35.229.35.101"
else:
    SERVER_URL = "http://127.0.0.1:5000"


def make_headers():
    nonce = str(int(time.time() * 1e6))
    message = nonce + OUR_API_KEY
    signature = hmac.new(OUR_API_SECRET, message, hashlib.sha256).hexdigest()
    headers = {
        'Access-Nonce': nonce,
        'Access-Key': OUR_API_KEY,
        'Access-Signature': signature
    }
    return headers


def place_order(user_id):
    thisSettings = TradeSettings.query(TradeSettings.user_id == user_id).get()
    required_spread = thisSettings.required_spread
    trade_size = thisSettings.trade_size
    send_ex = thisSettings.send_to
    buy_ex = thisSettings.buy_on
    wo_params_dict = {}
    wo_params_dict["required_spread"] = required_spread
    wo_params_dict["quantity"] = trade_size
    wo_params_dict["send_to"] = send_ex
    wo_params_dict["buy_on"] = buy_ex
    logg