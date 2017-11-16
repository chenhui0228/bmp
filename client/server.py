import os, sys
from datetime import *
import time
from SocketServer import BaseRequestHandler,ThreadingTCPServer,ThreadingUDPServer
import threading
from message import Message,Performance
#from log import MyLogging
#import logging.handlers as handlers
import socket
#import logging
import ConfigParser
sys.path.append('../')
from db.sqlalchemy import api as db_api
from db.sqlalchemy import models


super_context = {
    'is_superrole': True
}


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
    elif sub=='daily':
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
            'host': '10.202.127.11',
            'database': 'test'

        }
        self.db= db_api.get_database(conf)
        cp = ConfigParser.ConfigParser()
        cp.read('/etc/SFbackup/client.conf')
        self.port = cp.get('server', 'port')

    def suspend(self,id):
        task = self.db.get_task(super_context,id)
        worker = self.db.get_worker(super_context,'%s' % task.worker_id)
        addr = (worker.ip, int(worker.port))
        data = "{'typr':'suspend','data':{'id':'%s'}}" % id
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def delete(self,id):
        task = self.db.get_task(super_context,id)
        worker = self.db.get_worker(super_context, task.worker_id)
        addr = (worker.ip, int(worker.port))
        data = "{'typr':'delete','data':{'id':'%s'}}" % id
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def restart(self,id):
        task = self.db.get_task(super_context,id)
        worker = self.db.get_worker(super_context,task.worker_id)
        addr = (worker.ip, int(worker.port))
        data = "{'typr':'restart','data':{'id':'%s'}}" % id
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def update_task(self,id):
        task = self.db.get_task(super_context,id)
        worker = self.db.get_worker(super_context, task.worker_id)
        policy = self.db.get_policy( super_context,task.policy_id)
        addr = (worker.ip, int(worker.port))
        destination = task.destination
        vol_dir = destination.split('//')[1]
        vol = vol_dir.split('/', 1)[0]
        dir = vol_dir.split('/', 1)[1]
        dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
        source = task.source.split('/', 1)[1]
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        data = "{'type':'update','data':{'id':'%s','name':'%s'," \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % ( id, task.name, worker.ip,source, dir, vol, policy.protection,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)


    def update_worker(self,id):
        tasks=self.db.get_tasks(super_context)[0]
        for task in tasks:
            if task.worker_id == id:
                self.update_task(task.id)

    def update_policy(self,id):
        tasks=self.db.get_tasks(super_context)[0]
        for task in tasks:
            if task.policy_id == id:
                self.update_task(task.id)







    def backup(self,id,type=False):
        task = self.db.get_task(super_context,id)
        worker = self.db.get_worker(super_context, task.worker_id)
        policy = self.db.get_policy(super_context, task.policy_id)
        addr = (worker.ip, int(self.port))
        destination = task.destination
        vol_dir = destination.split('//')[1]
        vol = vol_dir.split('/', 1)[0]
        dir = vol_dir.split('/', 1)[1]
        dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
        source = task.source.split('/', 1)[1]
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        if type:
            run_sub='immediately'
        data = "{'type':'backup','data':{'id':'%s','name':'%s'," \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % (id, task.name, worker.ip, source, dir, vol, policy.protection,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def recover(self,id,type=False):         # need change
        task = self.db.get_task(super_context, id)
        worker = self.db.get_worker(super_context,task.worker_id)
        policy = self.db.get_policy(super_context, task.policy_id)
        addr = (worker.ip, int(self.port))
        destination = task.destination
        vol_dir = destination.split('//')[1]
        vol = vol_dir.split('/', 1)[0]
        dir = vol_dir.split('/', 1)[1]
        dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
        source = task.source.split('/', 1)[1]
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        if type:
            run_sub='immediately'
        data = "{'type':'recover','data':{'id':'%s','name':'%s'," \
               "'source_vol':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_ip':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % (id, task.name, vol,  dir ,source, worker.ip,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)



    def dump(self,id,type=False):
        task = self.db.get_task(super_context, id)
        worker = self.db.get_worker(super_context, task.worker_id)
        policy = self.db.get_policy(super_context,task.policy_id)
        addr = (worker.ip, int(self.port))
        destination = task.destination
        vol_dir = destination.split('//')[1]
        vol = vol_dir.split('/', 1)[0]
        dir = vol_dir.split('/', 1)[1]
        dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
        source=task.source.split('/',1)[1]
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        if type:
            run_sub='immediately'
        data = "{'type':'backup','data':{'id':'%s','name':'%s','script':'%s'" \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % (id, task.name,task.script_path,worker.ip, source, dir, vol, policy.protection,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)











    def to_db(self,msg):
        if msg['type'] == 'return':
            dict=msg['data']
            key=dict['sub']
            value=dict[key]
            ret=self.db.upda
        elif msg['initialize'] == 'return':
            dict = msg['data']


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


