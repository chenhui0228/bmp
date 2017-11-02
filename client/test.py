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

def q_backup(ms,addr):

    data="{'op_code':'queue','type':'backup','data':{'uuid':'12312','name':'test1','user':'zyt'," \
         "'source_ip':'10.202.125.83','source_address':'/zyt/test100M','destination_address': '/qwe/'," \
         "'destination_vol':'rp','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.send(info)

def d_backup(ms):

    data ="{'op_code':'queue','type':'backup','data':{'uuid':'12312','name':'test1','user':'zyt'," \
         "'source_ip':'10.202.125.83','source_address':'/zyt/test100M','destination_address': '/qwe/'," \
         "'destination_vol':'rp','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.send(info)


if __name__ == '__main__':
    #mylogger = MyLogging()
    ms=Message("tcp")
    ms.start_server()
    addr=('10.202.125.83',1025)
    #===============================
    while True:
        d_backup(ms)
        time.sleep(1800)
        q_backup(ms)
        time.sleep(1800)