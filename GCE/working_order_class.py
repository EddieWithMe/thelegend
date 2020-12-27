import uuid
import time

class WorkingOrder:
    def __init__(self, wo_params_dict):
        # required_spread, quantity, work_ex, hedge_ex
        self.external_working_order_id = str(uuid.uuid4())
        self.send_to = wo_params_dict["send_to"].lower()
        self.buy_on = wo_params_dict["buy_on"].lower()
        self.required_spread = float(wo_params_dict["required_spread"])
        self.total_quantity = float(wo_params_dict["quantity"])
        if self.total_quantity > 0:
            self.buy_sell = "buy"
        else:
            self.buy_sell = "sell"
        self.continue_loop = False
        self.completed = False
        self.working_order_id = 0
        self.work_just_matched_price = 0
        self.to_remove_count = 0
        self.last_time = 0
        self.counter = 0

    def get_work_price(self, exchanges_container):
        required_spread = self.required_spread
        hedge_ask = exchanges_container.ex_dict[self.send_to].ask_price
        hedge_bid = exchanges_container.ex_dict[self.send_to].bid_price
 