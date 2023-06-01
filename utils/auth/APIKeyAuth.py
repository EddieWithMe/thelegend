import hashlib
import hmac
import time

from future.builtins import bytes
from future.standard_library import hooks

from libraries.requests.auth import AuthBase

with hooks():  # Python 2/3 compat
    from urllib.parse import urlparse


class APIKeyAuth(AuthBase):
    """Attaches API Key Authentication to the given Request object."""
    def __init__(self, apiKey, apiSecret):
        """Init with Key & Secret."""
        self.apiKey = apiKey
        self.apiSecret = apiSecret

    def __call__(self, r):
        """Called when forming a request - generates api key headers."""
        # modify and return the request
        nonce = generate_nonce()
        r.headers['api-nonce'] = str(nonce)
        r.headers['api-key'] = self.apiKey
        r.headers['api-signature'] = generate_signature(self.apiSecret, r.method, r.url, nonce, r.body or '')
        return r


def generate_nonce():
    return int(round(time.time() * 1000))


# Generates an API signature.
# A signature is HMAC_SHA256(secret, verb + path + nonce + data), hex encoded.
# Verb must be uppercased, url is relative, nonce must be an increasing 64-bit integer
# and the data, if present, 