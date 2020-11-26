# This file is part of krakenex.
#
# krakenex is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# krakenex is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser
# General Public LICENSE along with krakenex. If not, see
# <http://www.gnu.org/licenses/gpl-3.0.txt>.


import base64
# private query signing
import hashlib
import hmac
import json
# private query nonce
import time
import urllib

import connection

from ..abstract import Exchange
from GCE.currency_classes.abstract import Currencies
from GCE.currency_classes.bitcoin.bitcoin import Bitcoin
from GCE.currency_classes.ethereum.ethereum import Ethereum
from GCE.currency_classes.ethereum_classic.ethereum_classic import EthereumClassic
from GCE.currency_classes.litecoin.litecoin import Litecoin


class Kraken(Exchange):
    """Kraken.com cryptocurrency Exchange API.
    
    Public methods:
    load_key
    query_public
    query_private
    
    """
    
    def __init__(self, key, secret):
        """Create an object with authentication information.
        
        Arguments:
        key    -- key required to make queries to the API (default: '')
        secret -- private key used to sign API messages (default: '')
        
        """
        self.key = key
        self.secret = secret
        self.uri = 'https://api.kraken.com'
        self.apiversion = '0'
        self.buy_poll_time = 0.2
        self.currencies = {
            Currencies.bitcoin: Bitcoin(),
            Currencies.ethereum: Ethereum(),
            Currencies.ethereum_classic: EthereumClassic(),
            Currencies.litecoin: Litecoin()
        }
        
        self.currencies[Currencies.bitcoin].usd_pair = "XXBTZUSD"
        self.currencies[Currencies.ethereum].usd_pair = "ETHUSD"
        self.currencies[Currencies.ethereum_classic].usd_pair = "ETCUSD"
        self.currencies[Currencies.litecoin].usd_pair = "LTCUSD"
    
    def load_key(self, path):
        """Load key and secret from file.
        
        Argument:
        path -- path to file (string, no default)
        
        """
        with open(path, "r") as f:
            self.key = f.readline().strip()
            self.secret = f.readline().strip()
    
    def _query(self, urlpath, req={}, conn=None, headers={}):
        """Low-level query handling.
        
        Arguments:
        urlpath -- API URL path sans host (string, no default)
        req     -- additional API request parameters (default: {})
        conn    -- kraken.Connection object (default: None)
        hea