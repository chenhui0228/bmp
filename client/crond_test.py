from datetime import *
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler

def print_time():
    now=datetime.now()
    print now


if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(print_time, 'interval', seconds =2, start_date='2017-11-11 20:00:00')
    scheduler.start()