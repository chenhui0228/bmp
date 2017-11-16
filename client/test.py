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