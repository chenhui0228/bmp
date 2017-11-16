#!/usr/bin/env python
#coding:utf-8
import time
from server import Server

def q_backup(ms,addr):

    data="{'type':'backup','data':{'id':'12312','name':'test1','user':'zyt'," \
         "'source_ip':'10.202.125.83','source_address':'/zyt/test100M','destination_address': '/qwe/'," \
         "'destination_vol':'rp','duration':'1','run_sub':'cron','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'*/5'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)

def d_backup(ms,addr):

    data ="{'type':'backup','data':{'id':'12312','name':'test1','user':'zyt'," \
         "'source_ip':'10.202.125.83','source_address':'/zyt/test100M','destination_address': '/qwe/'," \
         "'destination_vol':'rp','duration':'1','run_sub':'date','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)

def d_dump(ms,addr):
    data ="{'type':'dump','data':{'id':'12321','script':'ls'," \
         "'source_ip':'10.202.125.83','source_address':'/data/dump/','destination_address': '/qwe/'," \
         "'destination_vol':'rp','run_sub':'date','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)

def q_dump(ms,addr):
    data ="{'type':'dump','data':{'id':'12321','script':'ls'," \
         "'source_ip':'10.202.125.83','source_address':'/data/dump/','destination_address': '/qwe/'," \
         "'destination_vol':'rp','run_sub':'cron','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
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

def showtask(ms,addr):
    data ="{'type':'show'}"
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
         "'destination_vol':'rp','duration':'1','run_sub':'date','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
         "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
    info={}
    info['data']=data
    info['addr']=addr
    ms.issued(info)


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