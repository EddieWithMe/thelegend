import requests


SATOSHIS_PER_BITCOIN = 100000000


def get_most_recent_unnconfirmed_txn(address, original_amount_sent):
    """
    Since some exchanges don't expose the transaction id of the transfer. Here we attempt to get the transaction id
    from the blockchain address. If multiple unconfirmed transactions are present, we try to get the transaction hash
    by finding the most recent transaction with the matching btc amount sent
    :param address The desitnation bitcoin address
    :param original_amount_sent The amount of BTC sent

    """
    r = requests.get("https://api.blockcypher.com/v1/btc/m