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


if __name__ == '__main__':
    mylogger = MyLogging()
    ms=Message("tcp")
    ms.start_server()
    ip = ''
    cip = ''
    if not os.path.exists('/var/run/bak/'):
        os.mkdir('/var/run/bak/')
    if 'start' == sys.argv[1]:
        #print cip
        daemon = Daemon('/var/run/bak/watch_process.pid',  ms, ip, cip,
                        stdout='/var/log/bak/watch_stdout.log')
        daemon.start()
    elif  'restart' == sys.argv[1]:

        daemon = Daemon('/var/run/bak/watch_process.pid',  ms, ip, cip,
                        stdout='/var/log/bak/watch_stdout.log')
        daemon.restart()
    elif 'stop' == sys.argv[1]:

        daemon = Daemon('/var/run/bak/watch_process.pid', ms, ip, cip,stdout='/var/log/bak/watch_stdout.log')
        time.sleep(0.2)
        daemon.stop()
        sys.exit(1)
    sys.exit(0)