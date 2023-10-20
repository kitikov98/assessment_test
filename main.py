from threading import Thread
from admin_panel import admin_panel_run
from user_panel import user_panel_run
from admin_panel import lots_bid, start_auc, finish_auc
import schedule

def sheduler():
    schedule.every().minute.do(lots_bid)
    while True:
        schedule.run_pending()

def auc_start():
    schedule.every().minute.do(start_auc)
    while True:
        schedule.run_pending()

def auc_finish():
    schedule.every().minute.do(finish_auc)
    while True:
        schedule.run_pending()

if __name__ == '__main__':
    thr1 = Thread(target=auc_start)
    thr2 = Thread(target=user_panel_run)
    thr3 = Thread(target=admin_panel_run)
    thr4 = Thread(target=sheduler)
    thr5 = Thread(target=auc_finish)
    thr1.start()
    thr2.start()
    thr3.start()
    thr4.start()
    thr5.start()