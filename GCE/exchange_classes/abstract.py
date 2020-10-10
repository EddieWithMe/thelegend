class Exchange(object):
    def __init__(self, num_confs_btc=6, transfer_time=1800):
        """Constructor
        :param num_confs_btc: :param transfer_time: the number
        of seconds to poll a transaciton before reporting it as a
        failure
        
        :returns: object
        :rtype: Exchange
        
        """
        
        # number of confirmations needed to confirm btc deposit
        self.num_confs_btc = num_confs_btc
        self.transfer_time = transfer_time
    
    def buy(self, currency, amount):
        """Generic method to place buy market order.
        
        :param currency: a reference to the Currencies enum
        :param amount: amount of currency to be bought
        
        """
        raise NotImplementedError
   
    def sell(self, currency, amount):
        """Generic method to place a sell market order
        
        :param currency: a reference to the Currencies enum
        :param amount: amount of currency to be sold
        
        """
        raise NotImplementedError
    
   