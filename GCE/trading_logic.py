import threading
import datetime
from firebase import firebase_push_value
import random

import time

def record_order_log_in_firebase(wo_log_dict):
    firebase_push_value(["order_logs", "cex_gdax"], wo_log_dict)

def order_log(order_log_text, wo_uuid):
    time_readable = datetime.datetime.now().strftime("%m-%d %H:%M")
    order_log_dict = {"neg_timestamp": -time.time(), "timestamp": time.time(), "time_readable": time_readable,
                   "wo_id": str(wo_uuid), "text":order_log_text}
    t = threading.Thread(target=record_order_log_in_firebase,args=[order_log_dict])
    t.start()
    return

def exchange_buy_and_send_thread(wo_uuid, cexio_global, gdax_global):
   