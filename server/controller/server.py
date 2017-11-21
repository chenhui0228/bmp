import os, sys
from datetime import *
import time
from message import Message,Performance
import ConfigParser
sys.path.append('../')
from db.sqlalchemy import api as db_api
from db.sqlalchemy import models
from threading import Lock
import threading
import six
import logging
logger=logging.getLogger('backup')

class Singleton(type):
    _instances = {}
    lock = Lock()

    def __call__(cls, *args, **kwargs):
        cls.lock.acquire()
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(
                *args, **kwargs)
        cls.lock.release()
        return cls._instances[cls]

super_context = {
    'is_superuser': True
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

@six.add_metaclass(Singleton)
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
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.setDaemon(True)
        self.listen_thread.start()

    def suspend(self,id):
        task = self.db.get_task(super_context,id)
        worker = self.db.get_worker(super_context,'%s' % task.worker_id)
        addr = (worker.ip, int(self.port))
        data = "{'typr':'suspend','data':{'id':'%s'}}" % id
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def delete(self,id):
        task = self.db.get_task(super_context,id)
        worker = self.db.get_worker(super_context, task.worker_id)
        addr = (worker.ip, int(self.port))
        data = "{'typr':'delete','data':{'id':'%s'}}" % id
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def restart(self,id):
        task = self.db.get_task(super_context,id)
        worker = self.db.get_worker(super_context,task.worker_id)
        addr = (worker.ip, int(self.port))
        data = "{'typr':'restart','data':{'id':'%s'}}" % id
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def update_task(self,id):
        task = self.db.get_task(super_context,id)
        worker = task.worker
        policy = task.policy
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
        data = "{'type':'update','data':{'id':'%s','name':'%s'," \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % ( id, task.name, worker.ip,source, dir, vol, policy.protection,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        data2=data['data']
        data2['sub']=task.type
        if data2['sub'] == 'dump':
            data2['script'] == task.script_path
        elif data2['sub'] == 'recover':
            vol_dir = destination.split('//')[1]
            vol = vol_dir.split('/', 1)[0]
            dir = vol_dir.split('/', 1)[1]
            source = task.source.split('/', 1)[1]
            data2['source_vol']=vol
            data2['source_address'] =dir
            data2['destination_address']=source
            data2['destination_ip'] = worker.ip

        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)


    def update_worker(self,id,**kwargs):
        with open('/home/python/test/update_worker.txt', 'w+') as tp:
            tp.write('1')
            tasks_all=self.db.get_tasks(super_context,worker_id=id)
            tp.write('1.1')
            tasks=tasks_all[0]
            tp.write('1.2')
            try:
                worker = self.db.get_worker(super_context, id)
            except Exception,e:
                tp.write(e.message)


            tp.write('ok')
            if kwargs.has_key('ip'):
                tp.write('2.1')
                old_ip=kwargs['ip']
            else:
                old_ip=worker.ip
            if worker.ip == old_ip:
                tp.write('2.2')
                if len(tasks)!=0:
                    tp.write('2.21')
                    for task in tasks:
                        tp.write('2.22')
                        self.update_task(task.id)
                else:
                    tp.write('2.23')
                    pass
            else:
                tp.write('2.3')
                for task in tasks:
                    if task.worker_id == id:
                        addr = (old_ip, int(self.port))
                        data = "{'typr':'delete','data':{'id':'%s'}}" % task.id
                        info = {}
                        info['data'] = data
                        info['addr'] = addr
                        self.message.issued(info)
                for task in tasks:
                    if task.worker_id == id:
                        self.update_task(task.id)
            tp.write('3')


    def update_policy(self,id):
        tasks=self.db.get_tasks(super_context)[0]
        for task in tasks:
            if task.policy_id == id:
                self.update_task(task.id)







    def backup(self,id,do_type=False):
        task = self.db.get_task(super_context,id)
        worker = self.db.get_worker(super_context, task.worker_id)
        policy = self.db.get_policy(super_context, task.policy_id)
        addr = (worker.ip, int(self.port))
        destination = task.destination
        vol_dir = destination.split('//')[1]
        new_vor_dir= vol_dir.split('/', 1)
        if len(new_vor_dir) == 0:
            return
        elif len(new_vor_dir) == 1:
            vol=new_vor_dir[0]
            dir=''
        elif len(new_vor_dir)==2:
            vol = new_vor_dir[0]
            dir = new_vor_dir[1]
        dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
        source = task.source.split('/', 1)[1]
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        if do_type:
            run_sub='immediately'
        data = "{'type':'backup','data':{'id':'%s','name':'%s'," \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % (id, task.name, worker.ip, source, dir, vol, policy.protection,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def recover(self,id,do_type=False):         # need change
        task = self.db.get_task(super_context, id)
        worker = self.db.get_worker(super_context,task.worker_id)
        policy = self.db.get_policy(super_context, task.policy_id)
        addr = (worker.ip, int(self.port))
        destination = task.destination
        vol_dir = destination.split('//')[1]
        new_vor_dir= vol_dir.split('/', 1)
        if len(new_vor_dir) == 0:
            return
        elif len(new_vor_dir) == 1:
            vol=new_vor_dir[0]
            dir=''
        elif len(new_vor_dir)==2:
            vol = new_vor_dir[0]
            dir = new_vor_dir[1]
        dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
        source = task.source.split('/', 1)[1]
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        if do_type:
            run_sub='immediately'
        data = "{'type':'recover','data':{'id':'%s','name':'%s'," \
               "'source_vol':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_ip':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % (id, task.name, vol,  dir ,source, worker.ip,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)



    def dump(self,id,do_type=False):
        task = self.db.get_task(super_context, id)
        worker = self.db.get_worker(super_context, task.worker_id)
        policy = self.db.get_policy(super_context,task.policy_id)
        addr = (worker.ip, int(self.port))
        destination = task.destination
        vol_dir = destination.split('//')[1]
        new_vor_dir= vol_dir.split('/', 1)
        if len(new_vor_dir) == 0:
            return
        elif len(new_vor_dir) == 1:
            vol=new_vor_dir[0]
            dir=''
        elif len(new_vor_dir)==2:
            vol = new_vor_dir[0]
            dir = new_vor_dir[1]
        dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
        source=task.source.split('/',1)[1]
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        if do_type:
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
            with open('/home/python/test/return.txt','a') as fp:
                fp.write('1\n')
                dict=msg['data']
                fp.write(str(dict))
                fp.write('\n')
                key=dict['sub']
                value=dict[key]
                fp.write('2\n')
                try:
                    bk = self.db.get_bk_state(super_context, dict['bk_id'])
                except:
                    bk_value={}
                    bk_value['id']=dict['bk_id']
                    bk_value['task_id']=dict['id']
                    bk=self.db.bk_create(super_context,bk_value)
                fp.write('3')
                bk_dict={}
                bk_dict['id'] = bk.id
                bk_dict[key]=value
                self.db.bk_update(super_context,bk_dict)
                fp.write('4\n')
        elif msg['type'] == 'state':
            with open('/home/python/test/state.txt','a') as fp:
                fp.write('1\n')
                dict = msg['data']
                fp.write(str(dict))
                fp.write('\n')
                try:
                    task=self.db.get_task(super_context,dict['id'])
                    fp.write('2\n')
                    task_dict={}
                    task_dict['id']=dict['id']
                    task_dict['state']=dict['state']
                    self.db.update_task(super_context,task_dict)
                    fp.write('3\n')
                except:
                    pass
                fp.write('4\n')
        elif msg['type'] == 'initialize':
            dict = msg['data']
            worker_name=dict['hostname']
            with open('/home/python/test/initialize.txt', 'a') as tp:
                tp.write('initialize start %s'%str(dict))
                try:
                    tp.write('t 111')
                    worker=self.db.get_worker_by_name(super_context,worker_name)
                    tp.write('t 222')
                    worker_value={}
                    worker_value['id'] = worker.id
                    worker_value['ip'] = dict['ip']
                    worker_value['version'] = dict['version']
                    worker_value['group_id'] =dict['group']
                    worker_value['status'] = 'Active'
                    worker_value['start_at'] = str(time.time())
                    self.db.update_worker(super_context,worker_value)

                    tp.write('t 333')
                    info = {}
                    info['data'] = "{'type':'show'}"
                    info['addr'] = ('10.202.125.83',11111)
                    self.message.issued(info)
                    tp.write('t 44123123214')
                    #self.update_worker(worker.id)
                except:
                    worker_value={}
                    worker_value['name']=worker_name
                    worker_value['ip']=dict['ip']
                    worker_value['version'] = dict['version']
                    worker_value['group_id'] =dict['group']
                    worker_value['owner']=  'robot'
                    worker_value['status'] = 'Active'
                    worker_value['start_at'] = str(time.time())
                    try:
                        worker=self.db.create_worker(super_context,worker_value)
                    except Exception ,e:
                        tp.write(str(e))
                tp.write('initialize end')






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


