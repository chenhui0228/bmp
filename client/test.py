#!/usr/bin/env python
#coding:utf-8
import os, sys
from datetime import *
import time
from SocketServer import BaseRequestHandler,ThreadingTCPServer,ThreadingUDPServer
import threading
from message import Message,Performance
#from log import MyLogging
#import logging.handlers as handlers
import socket # 套接字
#import logging
import ConfigParser
from server import Server



if __name__ == '__main__':
    se=Server()
    print 'ok'
    #===============================
    se.backup('a6e64ec3-6673-4c27-ad73-ec6934101b0c')
    while True:
        if not se.message.q.empty():
            msg = se.message.get_queue()
            print msg
        time.sleep(1)
        #d_backup(ms,addr)
        #time.sleep(1800)
        #q_backup(ms,addr)
        #time.sleep(1800)
        pass