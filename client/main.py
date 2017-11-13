#!/usr/bin/env python
# coding:utf-8
from SocketServer import BaseRequestHandler,ThreadingTCPServer,ThreadingUDPServer
from message import Message,Performance
import socket
from gluster import gfapi
import sys
import os
import atexit
import errno
from os.path import join, getsize, isfile
from signal import SIGTERM
import urllib2
import httplib, urllib
import BaseHTTPServer
from SocketServer import ThreadingMixIn
import threading
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urlparse
from multiprocessing.pool import ThreadPool as Pool
from threading import Timer
from datetime import *
import time
import Queue
import types
import json
import socket
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import math
import logging.handlers as handlers
from daemon import Daemon
from message import Message
from  log import MyLogging
import ConfigParser

def create_dir(path):
    if not os.path.exists(path):  # 创建挂载的目录
        os.makedirs(path)
    for i in range(6):
        new_path=os.path.join(path,str(i))
        if not os.path.exists(new_path):
            try:
                os.mkdir(new_path)
            except:
                try:
                    cmd="umount %s"%new_path
                    os.system(cmd)
                except:
                    pass

if __name__ == '__main__':
    if not os.path.exists('/etc/SFbackup/client.conf'):
        print "conf is lose"
        sys.exit(1)
    cp = ConfigParser.ConfigParser()
    cp.read('/etc/SFbackup/client.conf')
    log_level = cp.get('client', 'log_level')
    log_file_dir = cp.get('client', 'log_file_dir')
    work_dir=cp.get('client', 'mount_dir')
    create_dir(work_dir)
    if not os.path.exists(log_file_dir):
        os.makedirs(log_file_dir)
    log_file_name=log_file_dir+'client.log'
    mylogger = MyLogging(log_level,log_file_name)   # 初始化log
    ip = ''
    cip = ''
    if not os.path.exists('/var/run/bak/'):
        os.mkdir('/var/run/bak/')
    if 'start' == sys.argv[1]:
        #print cip
        daemon = Daemon('/var/run/bak/watch_process.pid',  mylogger, ip, cip)
        daemon.start()
    elif  'restart' == sys.argv[1]:

        daemon = Daemon('/var/run/bak/watch_process.pid', mylogger, ip, cip)
        daemon.restart()
    elif 'stop' == sys.argv[1]:

        daemon = Daemon('/var/run/bak/watch_process.pid',  mylogger, ip, cip,)
        time.sleep(0.2)
        daemon.stop()
        sys.exit(1)
    sys.exit(0)