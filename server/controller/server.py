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
import eventlet


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
        self.workstate_dict={}
        try:
            self.listen_thread = threading.Thread(target=self.listen)
        except Exception,e:
            with open('/home/python/test/name.txt', 'a') as fp:
                fp.write(e.message)
        with open('/home/python/test/name.txt','a') as fp:
            fp.write(self.listen_thread.name)
        self.listen_thread.setDaemon(True)
        self.listen_thread.start()
        self.pool = eventlet.GreenPool(10000)
        with open('/home/python/test/name.txt','a') as fp:
            fp.write('ok\n')


    def stop(self,id):
        task = self.db.get_task(super_context,id)
        worker = task.worker
        addr = (worker.ip, int(self.port))
        data = "{'type':'delete','data':{'id':'%s'}}" % (id)
        info = {}
        info['data'] = data
        info['addr'] = addr
        try:
            self.message.issued(info)
        except Exception,e:
            logger.error(e.message)

    def delete(self,id):
        task = self.db.get_task(super_context,id)
        worker = task.worker
        addr = (worker.ip, int(self.port))
        task_value = {}
        task_value['id'] = id
        task_value['state'] = 'deleteing'
        data = "{'type':'delete','data':{'id':'%s','deletework':'yes'}}" % (id)
        info = {}
        info['data'] = data
        info['addr'] = addr
        if task.state == 'waiting' or task.state == 'running_w':
            try:
                self.message.issued(info)
                self.db.update_task(super_context, task_value)
            except Exception,e:
                logger.error(e.message)
        else:
            try:
                task_value['state'] = 'deleted'
                task_value['deleted'] = 'deleted'
                self.db.update_task(super_context, task_value)
            except Exception,e:
                logger.error(e.message)


    def resume(self,id):
        task = self.db.get_task(super_context,id)
        if task.type=='backup':
            self.backup(id)
        elif task.type=='recover':
            self.recover(id)
        elif task.type =='dump':
            self.dump(id)

    def update_task(self,id,isRestart=False):
        logger.debug('update_task start')
        try:
            task = self.db.get_task(super_context,id)
            if task.state == 'stopped':
                return
            worker = task.worker
            policy = task.policy
            addr = (worker.ip, int(self.port))
            destination = task.destination
            vol_dir = destination.split('//')[1]
            new_vor_dir = vol_dir.split('/', 1)
            if len(new_vor_dir) == 0:
                return
            elif len(new_vor_dir) == 1:
                vol = new_vor_dir[0]
                dir = ''
            elif len(new_vor_dir) == 2:
                vol = new_vor_dir[0]
                dir = new_vor_dir[1]
            dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
            source = task.source.split('/', 1)[1]

            if policy.recurring=='once':
                run_sub='date'
            else:
                run_sub='cron'
        except Exception,e:
            logger.error(e.message)
            pass
        data = "{'type':'update','data':{'id':'%s','name':'%s','state':'%s'," \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % ( id, task.name, task.state, worker.ip,source, dir, vol, policy.protection,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])

        try:
            data=eval(data)
        except Exception,e:
            logger.error(e.message)
        data2 = data.get('data')
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
        if isRestart:
            data['type']=data2['sub']

        info = {}
        info['data'] = str(data)
        info['addr'] = addr
        self.message.issued(info)
        logger.debug('update_task send message dnow')



    def update_worker(self,id,isRestart=False,**kwargs):
        logger.debug('update_worker start')
        tasks_all=self.db.get_tasks(super_context,worker_id=id)
        tasks=tasks_all[0]
        try:
            worker = self.db.get_worker(super_context, id)
        except Exception,e:
            logger.error(e.message)
        if kwargs.has_key('ip'):
            old_ip=kwargs.get('ip')
        else:
            old_ip=worker.ip
        if worker.ip == old_ip:
            if len(tasks)!=0:
                for task in tasks:
                    if  isRestart:
                        self.update_task(task.id,True)
                        logger.debug('the restart msg end to updatetask')
                    else:
                        self.update_task(task.id)
            else:
                logger.debug('the worker is no task')
                pass
        else:
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



    def update_policy(self,id):
        tasks=self.db.get_tasks(super_context)[0]
        for task in tasks:
            if task.policy_id == id:
                self.update_task(task.id)





    def backup(self,id,do_type=False):
        try:
            task = self.db.get_task(super_context,id)
            worker = task.worker
            policy = task.policy
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
        except:
            pass
        data = "{'type':'backup','data':{'id':'%s','name':'%s','state':'%s'," \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % (id, task.name, task.state, worker.ip, source, dir, vol, policy.protection,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)

    def recover(self,id):         # need change
        try:
            task = self.db.get_task(super_context, id)
            worker = task.worker
            policy = task.policy
            addr = (worker.ip, int(self.port))
            source = task.source
            vol_dir = source.split('//')[1]
            new_vor_dir= vol_dir.split('/', 1)
            if len(new_vor_dir) == 0:
                return
            elif len(new_vor_dir) == 1:
                vol=new_vor_dir[0]
                dir='/'
            elif len(new_vor_dir)==2:
                vol = new_vor_dir[0]
                dir = '/'+new_vor_dir[1]
            #dict=translate_date(policy.recurring,policy.start_time,policy.recurring_options_every,policy.recurring_options_week)
            destination = task.destination.split('/', 1)[1]
        except Exception,e:
            logger.error(e.message)
            pass
        #if policy.recurring=='once':
        #    run_sub='date'
        #else:
        #    run_sub='cron'
        #if do_type:
        run_sub='immediately'
        data = "{'type':'recover','data':{'id':'%s','name':'%s','state':'%s'," \
               "'source_vol':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_ip':'%s','run_sub':'%s',}} " % (id, task.name, task.state, vol,  dir ,destination, worker.ip,run_sub)
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)



    def dump(self,id,do_type=False):
        task = self.db.get_task(super_context, id)
        worker = task.worker
        policy = task.policy
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
        data = "{'type':'backup','data':{'id':'%s','name':'%s','script':'%s','state':'%s'" \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % (id, task.name,task.script_path, task.state,worker.ip, source, dir, vol, policy.protection,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)


    def to_db(self,msg):
        logger.debug('to_db start')
        if msg.get('type') == None:
            logger.error('msg error')
            return
        if msg['type'] == 'return':

            dict=msg.get('data')
            logger.debug(str(dict))
            bk_value = {}
            bk_value['id'] = dict.get('bk_id')
            bk_value['task_id'] = dict.get('id')
            typeofMessage=dict['sub']
            if typeofMessage == 'frist':
                bk_value['start_time']=dict.get('start_time')
                bk_value['total_size'] = dict.get('total_size')
                bk_value['process'] = dict.get('process')
                bk_value['state'] = dict.get('state')
                try:
                    bk = self.db.bk_create(super_context, bk_value)
                    self.workstate_dict[dict['bk_id']] = 0
                except Exception,e:
                    pass
                return
            elif typeofMessage == 'run':
                bk_value['process'] = dict.get('process')
                bk_value['current_size'] = dict.get('current_size')
                if not self.workstate_dict.has_key(dict['bk_id']):
                    return
                if self.workstate_dict[dict['bk_id']]>int(dict['process']):
                    return
            elif typeofMessage == 'last':
                bk_value['state'] = dict.get('state')
                bk_value['end_time'] = dict.get('end_time')
                bk_value['message'] = dict.get('errormessage')
                del self.workstate_dict[dict['bk_id']]
            #if key == 'process':
            #    if int(bk.process) < int(dict[key]):
            #        return
            try:
                self.db.bk_update(super_context,bk_value)
            except Exception,e:
                pass

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
                    if dict['state'] == 'deleted':
                        task_dict['deleted'] == 'deleted'
                    self.db.update_task(super_context,task_dict)
                    fp.write('3\n')
                except:
                    pass
                fp.write('4\n')
        elif msg['type'] == 'initialize':
            dict = msg['data']
            workers=self.db.get_workers(super_context,name=dict['hostname'],group_id=dict['group'],worker_ip=dict['ip'])[0]
            if len(workers)==1:
                logger.debug('get worker')
                worker=workers[0]
                worker_value={}
                worker_value['id'] = worker.id
                worker_value['ip'] = dict['ip']
                worker_value['version'] = dict['version']
                worker_value['group_id'] =dict['group']
                worker_value['status'] = 'Active'
                worker_value['start_at'] = str(time.time())
                try:
                    self.db.update_worker(super_context,worker_value,True)
                except Exception,e:
                    pass
                info = {}
                info['data'] = "{'type':'show'}"
                info['addr'] = ('10.202.125.83',11111)
                self.message.issued(info)
                logger.debug('send msg dnow')
                try:
                    self.update_worker(worker.id,True)
                    logger.debug('update_worker end')
                except Exception,e:
                    logger.error(e.message)
                    pass
            elif len(workers)==0:
                worker_value={}
                worker_value['name']=dict['hostname']
                worker_value['ip']=dict['ip']
                worker_value['version'] = dict['version']
                worker_value['group_id'] =dict['group']
                worker_value['owner']=  'robot'
                worker_value['status'] = 'Active'
                worker_value['start_at'] = str(time.time())
                try:
                    worker=self.db.create_worker(super_context,worker_value)
                except Exception ,e:
                    logger.error(e.message)

            else:
                logger.error('more than one client has same information')






    def listen(self):  # listen msg from clien
        print 'listen'
        logger.debug('listen start')
        while True:
            if self.message.con.acquire():
                if not self.message.q.empty():
                        logger.info(self.listen_thread.name)
                        msg = self.message.get_queue()
                        self.message.con.release()
                        msg_data = msg.split(":", 1)[1]
                        logger.debug(msg_data)
                        date = eval(msg_data)
                        try:
                            self.pool.spawn_n(self.to_db,date)
                            self.pool.waitall()
                            logger.debug(str(self.pool.running()))
                        except Exception,e:
                            logger.error(e.message)
                            pass
                else:
                        self.message.con.wait(1)
                        self.message.con.release()
                #time.sleep(1)



