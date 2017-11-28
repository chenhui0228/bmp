#!/usr/bin/env python

import os
import time
import subprocess

import threading
def asd():
    print 'asd'
    timer=threading.Timer(2.0,asd)
    timer.setDaemon(True)
    timer.start()

timer=threading.Timer(2.0,asd)
timer.setDaemon(True)

timer.start()
while True:
    time.sleep(1)








