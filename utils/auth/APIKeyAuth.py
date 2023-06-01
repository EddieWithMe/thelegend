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
        """Called whe