#!/usr/bin/env python
#coding:utf-8
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



if __name__ == '__main__':
    cp = ConfigParser.ConfigParser()
    cp.read('client.conf')
    log_level = cp.get('client', 'log_level')
    log_file_dir = cp.get('client', 'log_file_dir')

    if not os.path.exists(log_file_dir):
        os.mkdir(log_file_dir)
    if not os.path.exists('/var/run/bak/'):
        os.mkdir('/var/run/bak/')
    log_file_name=log_file_dir+'client.log'
    mylogger = MyLogging(log_level,log_file_name)
    ms=Message("tcp")
    ms.start_server()
    cp.read('create.conf')
    addrl=cp.get('work','ip')
    addr=(addrl,1025)
    data="{'type':'backup','data':{'id':'%s','name':'%s','user':'zyt'," \
         "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
         "'destination_vol':'%s','duration':'%s','run_sub':'queue','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
         "'second':'%s','start_date':'%s'}}}"%(cp.get('work','id'),cp.get('work','name'),cp.get('work','ip'),cp.get('work','source'),cp.get('work','destination').split(':')[0],cp.get('work','destination').split(':')[1],cp.get('work','duration'),cp.get('work','year'),cp.get('work','month'),cp.get('work','day'),cp.get('work','week'),cp.get('work','day_of_week'),cp.get('work','hour'),cp.get('work','minute'),cp.get('work','second'),cp.get('work','start_date'))
    info={}
    info['data']=data
    info['addr']=addr
    ms.send(info)
    #===============================
    while True:
        if not ms.q.empty():
            msg = ms.get_queue()
            print msg
        time.sleep(1)
        #d_backup(ms,addr)
        #time.sleep(1800)
        #q_backup(ms,addr)
        #time.sleep(1800)
        pass