class Exchange(object):
    def __init__(self, num_confs_btc=6, transfer_time=1800):
        """Constructor
        :param num_confs_btc: :param transfer_time: the number
        of seconds to poll a transaciton before reporting it as a
        failure
        
        :returns: object
        :rtype: Exchange
        
        """
        
        # number of confirmations neede