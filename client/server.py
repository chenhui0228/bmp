import os, sys
from datetime import *
import time
from SocketServer import BaseRequestHandler,ThreadingTCPServer,ThreadingUDPServer
import threading
from message import Message,Performance
from log import MyLogging
import logging.handlers as handlers
import socket # 套接字
import logging
import ConfigParser


class Server:
    def __init__(self):
        self.message = Message
        conf = {
            'driver': 'mysql',
            'user': 'backup',
            'password': '123456',
            'host': '10.202.127.11'
        }

    def to_client(self,op,id):
        pass


    def to_db(self,msg):
        pass


