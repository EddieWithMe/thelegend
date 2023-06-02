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
    m