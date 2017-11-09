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

def q_backup(ms,addr):

    data="{'type':'backup','data':{'id':'12312','name':'test1','user':'zyt'," \
         "'source_ip':'10.202.125.83','source_address':'/zyt/test100M','destination_address': '/qwe/'," \
         "'destination_vol':'rp','duration':'1','run_sub':'queue','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'*/5'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)

def d_backup(ms,addr):

    data ="{'type':'backup','data':{'id':'12312','name':'test1','user':'zyt'," \
         "'source_ip':'10.202.125.83','source_address':'/zyt/test100M','destination_address': '/qwe/'," \
         "'destination_vol':'rp','duration':'1','run_sub':'direct','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)

def d_dump(ms,addr):
    data ="{'type':'dump','data':{'id':'12321','script':'ls'," \
         "'source_ip':'10.202.125.83','source_address':'/data/dump/','destination_address': '/qwe/'," \
         "'destination_vol':'rp','run_sub':'direct','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)

def q_dump(ms,addr):
    data ="{'type':'dump','data':{'id':'12321','script':'ls'," \
         "'source_ip':'10.202.125.83','source_address':'/data/dump/','destination_address': '/qwe/'," \
         "'destination_vol':'rp','run_sub':'queue','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)


def d_recover(ms,addr):
    data ="{'type':'recover','data':{'name':'test1','backup_time':'201711031508'," \
         "'source_ip':'10.202.125.83','source_address':'/data/dump/','source_vol':'rp','destination_address': '/data/dump/'," \
         "'destination_ip':'10.202.125.83','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)

def suspend(ms,addr):
    data ="{'type':'suspend','data':{'id':'12312'} }"
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)

def delete(ms,addr):
    data ="{'type':'delete','data':{'id':'12312'} }"
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)


def restart(ms,addr):
    data ="{'type':'restart','data':{'id':'12312'} }"
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)


def revise (ms,addr):
    data ="{'type':'backup','data':{'id':'12312','name':'test1','user':'zyt'," \
         "'source_ip':'10.202.125.83','source_address':'/zyt/test100M','destination_address': '/qwe/'," \
         "'destination_vol':'rp','duration':'1','run_sub':'direct','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)


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
    addr=('10.202.125.83',1025)
    q_backup(ms, addr)
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