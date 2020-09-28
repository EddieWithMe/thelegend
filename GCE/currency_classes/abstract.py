from enum import Enum


class Currency(object):
    """Abstract currency classes have some functions to check the
    blockchain. These are implemented within
    currency_classes/bitcoin/bitcoin.py.
    
    Each exchange class will implement a hashmap called
    "currencies". Within this hashmap they will instantiate one of
    each class pointing to an instance. This will amount to a
    singleton model for each exchange. This "singleton" will contain
    information necessary for that partic