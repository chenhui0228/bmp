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

    def listen( self ):
        while True:
            if not self.message.q.empty():
                msg = self.message.get_queue()
                #print msg
                msg_data = msg.split(":", 1)[1]
                date = eval(msg_data)
                self.to_db(date)
            time.sleep(1)

