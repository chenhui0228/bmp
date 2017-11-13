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
        self.message = Message('tcp')
        self.message.start_server()
        conf = {
            'driver': 'mysql',
            'user': 'backup',
            'password': '123456',
            'host': '10.202.127.11'
        }
        self.db= db_api.get_database(conf)

    def to_client(self,op,id):
        task=self.db.get_task(id)
        if op=='suspend' or op == 'delete'or op == 'restart':





    def to_db(self,msg):
        pass

    def listen(self):  # listen msg from client
        while True:
            if self.message.con.acquire():
                if not self.message.q.empty():
                        msg = self.message.get_queue()
                        #print msg
                        msg_data = msg.split(":", 1)[1]
                        #print msg_data
                        #self.log.logger.info("get msg is that %s"%msg_data)
                        date = eval(msg_data)
                        self.to_db(date)
                else:
                        self.message.con.wait()
                time.sleep(1)
                self.message.con.release()


