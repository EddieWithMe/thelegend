import uuid
import time

class WorkingOrder:
    def __init__(self, wo_params_dict):
        # required_spread, quantity, work_ex, hedge_ex
        self.external_working_order_id = str(uuid.uuid4())
        self.send_to = wo_params_dict["send_to"].lower()
        self.buy_on = wo_params_dict["buy_on"].lower()
        self.required_spread = float(wo_params_dict["required_spread"])
        self.tot