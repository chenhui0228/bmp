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
sys.path.append('../')
from db.sqlalchemy import api as db_api
from db.sqlalchemy import models

def translate_date(sub,start_time,every,weekdat):
    timestamp = int(start_time)
    time_local = datetime.fromtimestamp(timestamp)
    dict={'run_sub':'date','year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'*','second':'*','start_date':'%s'%str(time_local)}
    if sub=='once':
        pass
    elif sub=='hourly':
        dict['second']=time_local.second
        dict['minute']=time_local.minute
        t=time_local.hour%int(every)
        dict['hour']='%d/%d'%(t,int(every))
    elif sub=='datly':
        dict['second']=time_local.second
        dict['minute']=time_local.minute
        dict['hour'] = time_local.hour
        t=time_local.day%int(every)
        dict['day']='%d/%d'%(t,int(every))
    elif sub=='weekly':
        dict['second']=time_local.second
        dict['minute']=time_local.minute
        dict['hour'] = time_local.hour
        dict['day_of_week']=weekdat
    elif sub=='monthly':
        dict['second']=time_local.second
        dict['minute']=time_local.minute
        dict['hour'] = time_local.hour
        dict['day'] = time_local.day
        t=time_local.month%int(every)
        dict['month']='%d/%d'%(t,int(every))
    return dict



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

    def suspend(self,id):
        task = self.db.get_task(id)
        worker = self.db.get_worker('%s' % task.worker_id)
        addr = (worker.ip, int(worker.port))
        data = "{'typr':'suspend','data':{'id':'%s'}}" % id
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def delete(self,id):
        task = self.db.get_task(id)
        worker = self.db.get_worker('%s' % task.worker_id)
        addr = (worker.ip, int(worker.port))
        data = "{'typr':'delete','data':{'id':'%s'}}" % id
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def restart(self,id):
        task = self.db.get_task(id)
        worker = self.db.get_worker('%s' % task.worker_id)
        addr = (worker.ip, int(worker.port))
        data = "{'typr':'restart','data':{'id':'%s'}}" % id
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def update(self,id):
        task = self.db.get_task('%s' % id)
        worker = self.db.get_worker('%s' % task.worker_id)
        policy = self.db.get_policy('%s' % task.policy_id)
        addr = (worker.ip, int(worker.port))
        destination = task.destination
        vol_dir = destination.split('//')[1]
        vol = vol_dir.split('/', 1)[0]
        dir = vol_dir.split('/', 1)[1]
        date_dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        data = "{'type':'update','data':{'id':'%s','name':'%s'," \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % ( id, task.name, worker.ip, task.source, dir, vol, policy.protrction,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def backup(self,id):
        task = self.db.get_task('%s' % id)
        worker = self.db.get_worker('%s' % task.worker_id)
        policy = self.db.get_policy('%s' % task.policy_id)
        addr = (worker.ip, int(worker.port))
        destination = task.destination
        vol_dir = destination.split('//')[1]
        vol = vol_dir.split('/', 1)[0]
        dir = vol_dir.split('/', 1)[1]
        date_dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        data = "{'type':'backup','data':{'id':'%s','name':'%s'," \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % (id, task.name, worker.ip, task.source, dir, vol, policy.protrction,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def recover(self,id):         # need change
        task = self.db.get_task('%s' % id)
        worker = self.db.get_worker('%s' % task.worker_id)
        policy = self.db.get_policy('%s' % task.policy_id)
        addr = (worker.ip, int(worker.port))
        destination = task.destination
        vol_dir = destination.split('//')[1]
        vol = vol_dir.split('/', 1)[0]
        dir = vol_dir.split('/', 1)[1]
        date_dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        data = "{'type':'recover','data':{'name':'test1','backup_time':'201711031508'," \
               "'source_ip':'10.202.125.83','source_address':'/data/dump/','source_vol':'rp','destination_address': '/data/dump/'," \
               "'destination_ip':'10.202.125.83','cron': {'year':'*','month':'*','day':'*', 'week':'*','day_of_week':'*','hour':'*','minute':'0'," \
               "'second':'0','start_date':'2017-11-2 00:00:00'}}} "
        data = "{'type':'recover','data':{'id':'%s','name':'%s'," \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % (id, task.name, worker.ip, task.source, dir, vol, policy.protrction,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)



    def dump(self,id):
        task = self.db.get_task('%s' % id)
        worker = self.db.get_worker('%s' % task.worker_id)
        policy = self.db.get_policy('%s' % task.policy_id)
        addr = (worker.ip, int(worker.port))
        destination = task.destination
        vol_dir = destination.split('//')[1]
        vol = vol_dir.split('/', 1)[0]
        dir = vol_dir.split('/', 1)[1]
        date_dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        data = "{'type':'backup','data':{'id':'%s','name':'%s','script':'%s'" \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % (id, task.name,task.script_path,worker.ip, task.source, dir, vol, policy.protrction,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)











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


