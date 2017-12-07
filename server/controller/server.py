import os, sys
from datetime import *
import time
from message1 import Message,Performance
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


def translate_date(sub,start_time,every,weekday):
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
        dict['day_of_week']=weekday
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
    def __init__(self,conf):
        mysqlconf = conf.get('database')
        try:
            self.db= db_api.get_database(mysqlconf)
        except Exception as e:
            logger.error(e)
            return
        server_dict=conf.get('servercontroller')
        logger.info(str(server_dict))
        self.port=server_dict['port']
        self.worker_size=server_dict['worker_size']
        self.timer_interval=server_dict['timer_interval']
        if self.port==None or self.timer_interval == None or self.worker_size == None:
            logger.error('conf is lost')
            logger.error(str(conf))
            return
        else:
            logger.info('get right conf %s'%str(server_dict))

        self.workstate_dict={}
        self.message = Message('tcp',self.port)
        self.message.start_server()
        self.alivelock=threading.Lock()
        self.workstatelock = threading.Lock()
        self.workeralivedict={}
        self.create_workerpool()
        self.t = threading.Timer(self.timer_interval, self.keeplaive)
        self.t.setDaemon(True)
        self.t.start()


    def create_workerpool(self):
        for i in range(int(self.worker_size)):
            t=Workerpool(self.message,i,self)
            t.setDaemon(True)
            try:
                t.start()
            except Exception as e:
                logger.error(e)


    def keeplaive(self):
        workers=self.db.get_workers(super_context)
        workersnum=workers[1]
        workerslist=workers[0]
        for i in range(workersnum):
            worker=workerslist[i]
            worker_id=worker.id
            data = "{'type':'keepalive'}"
            info = {}
            addr=(worker.ip, int(self.port))
            if worker.ip=='10.202.127.11':
                addr = (worker.ip, 22222)
            info['data'] = data
            info['addr'] = addr
            self.message.issued(info)
            last_update = int(worker.last_report)
            now = int(time.time())
            logger.debug('the worker is %s,status is %s,interval is %s'%(worker_id,worker.status,str(now-last_update)))
            if worker.status == 'Active':
                if now-last_update>=4*self.timer_interval:
                    worker_value={}
                    worker_value['id']=worker.id
                    worker_value['status']='Offline'
                    try:
                        self.db.update_worker(super_context, worker_value)
                    except Exception as e:
                        logger.error(e)
                    logger.warning('the worker %s is onffline' % worker.id)

            elif worker.status == 'Offline':
                if now - last_update < 4 * self.timer_interval:
                    worker_value={}
                    worker_value['id']=worker.id
                    worker_value['status']='Active'
                    try:
                        self.db.update_worker(super_context, worker_value)
                    except Exception as e:
                        logger.error(e)
        self.t = threading.Timer(self.timer_interval, self.keeplaive)
        self.t.setDaemon(True)
        self.t.start()

    def pause(self,id):
        task = self.db.get_task(super_context,id,True, True)
        worker = task.worker
        addr = (worker.ip, int(self.port))
        if worker.ip == '10.202.127.11':
            addr = (worker.ip, 22222)
        data = "{'type':'pause','data':{'id':'%s'}}" % (id)
        info = {}
        info['data'] = data
        info['addr'] = addr
        if task.state == 'running_s' or task.state == 'running_w':
            try:
                self.message.issued(info)
            except Exception as e:
                logger.error(e)
        else:
            logger.error('Can not pause in waiting or stopped')


    def stop(self,id):
        task = self.db.get_task(super_context,id)
        worker = task.worker
        addr = (worker.ip, int(self.port))
        if worker.ip == '10.202.127.11':
            addr = (worker.ip, 22222)
        data = "{'type':'delete','data':{'id':'%s'}}" % (id)
        info = {}
        info['data'] = data
        info['addr'] = addr
        try:
            self.message.issued(info)
        except Exception as e:
            logger.error(e)

    def delete(self,id):
        task = self.db.get_task(super_context,id,True, True)
        worker = task.worker
        addr = (worker.ip, int(self.port))
        if worker.ip == '10.202.127.11':
            addr = (worker.ip, 22222)
        self.pause(id)
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
            except Exception as e:
                logger.error(e)
        else:
            try:
                task_value['state'] = 'deleted'
                task_value['deleted'] = 'deleted'
                self.db.update_task(super_context, task_value)
            except Exception as e:
                logger.error(e)


    def resume(self,id):
        task = self.db.get_task(super_context,id)
        if task.type=='backup':
            self.backup(id)
        elif task.type=='recover':
            self.recover(id)


    def update_task(self,id,isRestart=False):
        logger.debug('update_task start now')
        task = self.db.get_task(super_context,id)
        if task.state == 'stopped':
            return
        worker = task.worker
        policy = task.policy
        addr = (worker.ip, int(self.port))
        if worker.ip=='10.202.127.11':
            addr = (worker.ip, 22222)
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
        dict=translate_date(policy.recurring,task.start_time,policy.recurring_options_every,policy.recurring_options_week)
        source = task.source.split('/', 1)[1]
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        data = "{'type':'update','data':{'id':'%s','name':'%s','state':'%s'," \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % ( id, task.name, task.state, worker.ip,source, dir, vol, policy.protection,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])

        try:
            data=eval(data)
        except Exception as e:
            logger.error(e)
        data2 = data.get('data')
        data2['sub']=task.type
        if data2['sub'] == 'recover':
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
            if task.source.split('/', 1)[0] == 'shell:':
                data['type'] = 'dump'
        if task.source.split('/', 1)[0] == 'shell:':
            data2['sub']='dump'


        info = {}
        info['data'] = str(data)
        info['addr'] = addr
        self.message.issued(info)



    def update_worker(self,id,isRestart=False,**kwargs):
        logger.debug('update_worker start')
        tasks_all=self.db.get_tasks(super_context,worker_id=id)
        tasks=tasks_all[0]
        try:
            worker = self.db.get_worker(super_context, id)
        except Exception as e:
            logger.error(e)
        logger.debug('get worker ')
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
                    if worker.ip == '10.202.127.11':
                        addr = (worker.ip, 22222)
                    data = "{'typr':'delete','data':{'id':'%s','changeworker':'yes'}}" % task.id
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

        task = self.db.get_task(super_context,id)
        worker = task.worker
        policy = task.policy
        addr = (worker.ip, int(self.port))
        if worker.ip=='10.202.127.11':
            addr = (worker.ip, 22222)
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
        dict=translate_date(policy.recurring,task.start_time,policy.recurring_options_every,policy.recurring_options_week)
        source = task.source.split('/', 1)[1]
        if policy.recurring=='once':
            run_sub='date'
        else:
            run_sub='cron'
        if do_type:
            run_sub='immediately'

        data = "{'type':'backup','data':{'id':'%s','name':'%s','state':'%s'," \
               "'source_ip':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_vol':'%s','duration':'%s','run_sub':'%s','cron': {'year':'%s','month':'%s','day':'%s', 'week':'%s','day_of_week':'%s','hour':'%s','minute':'%s'," \
               "'second':'%s','start_date':'%s'}}} " % (id, task.name,task.state, worker.ip, source, dir, vol, policy.protection,run_sub,dict['year'],dict['month'],dict['day'],dict['week'],dict['day_of_week'],dict['hour'],dict['minute'],dict['second'],dict['start_date'])
        data=eval(data)
        try:
            if task.source.split('/', 1)[0] == 'shell:':
                data['type']='dump'
        except Exception as e:
            logger.error(e)
            return
        info = {}
        info['data'] = str(data)
        info['addr'] = addr
        self.message.issued(info)

    def recover(self,id):         # need change
        try:
            task = self.db.get_task(super_context, id)
            worker = task.worker
            policy = task.policy
            addr = (worker.ip, int(self.port))
            if worker.ip=='10.202.127.11':
                addr = (worker.ip, 22222)
            source = task.source
            vol_dir = source.split('//',1)[1]
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
        except Exception as e:
            logger.error(e)
            pass
        run_sub='immediately'
        data = "{'type':'recover','data':{'id':'%s','name':'%s','state':'%s'," \
               "'source_vol':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_ip':'%s','run_sub':'%s'}} " % (id, task.name, task.state, vol,  dir ,destination, worker.ip,run_sub)
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)


    def revckeepalive(self):
        pass


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
                bk_value['process'] = str(dict.get('process'))
                bk_value['state'] = dict.get('state')
                try:
                    bk = self.db.bk_create(super_context, bk_value)
                    self.workstatelock.acquire()
                    self.workstate_dict[dict['bk_id']] = 0
                    self.workstatelock.release()
                except Exception as e:
                    logger.error(e)
                return
            elif typeofMessage == 'run':
                bk_value['process'] = str(dict.get('process'))
                bk_value['current_size'] = int(dict.get('current_size'))
                logger.info(str(self.workstate_dict))
                if not self.workstate_dict.has_key(dict['bk_id']):
                    return
                if int(self.workstate_dict[dict['bk_id']])>int(dict['process']):
                    return
                else:
                    self.workstatelock.acquire()
                    self.workstate_dict[dict['bk_id']]=int(dict['process'])
                    self.workstatelock.release()

                try:
                    self.db.bk_update(super_context, bk_value)
                except Exception as e:
                    logger.error(e)
                return
            elif typeofMessage == 'last':
                bk_value['state'] = dict.get('state')
                bk_value['end_time'] = dict.get('end_time')
                bk_value['message'] = dict.get('message')

                try:
                    self.db.bk_update(super_context, bk_value)
                except Exception as e:
                    logger.error(e)
                    return
                if not self.workstate_dict.has_key(dict['bk_id']):
                    logger.error('some messages order is wrong  ')
                    return
                self.workstatelock.acquire()
                del self.workstate_dict[dict['bk_id']]
                self.workstatelock.release()
            elif typeofMessage== 'delete':
                logger.info('delete a kackupstate which id is')
                backupstate_list=self.db.bk_list(super_context,task_id=dict['id'])[0]
                for line in backupstate_list:
                    logger.info(line.id)
                    if line.start_time == dict['start_time']:
                        logger.info('find backupstate')
                        try:
                            self.db.bk_delete(super_context, line.id)
                        except Exception as e:
                            logger.error(e)
                        logger.info(str(bk_value))
                        return
            #if key == 'process':
            #    if int(bk.process) < int(dict[key]):
            #        return


        elif msg['type'] == 'state':
                dict = msg['data']
                try:
                    task=self.db.get_task(super_context,dict['id'])
                    task_dict={}
                    task_dict['id']=dict['id']
                    task_dict['state']=dict['state']
                    if dict['state'] == 'deleted':
                        task_dict['deleted'] == 'deleted'
                    self.db.update_task(super_context,task_dict)
                    logger.info('change task state')
                except Exception as e:
                    logger.error(e.message)
        elif msg['type'] == 'initialize':
            dict = msg['data']
            try:
                workers=self.db.get_workers(super_context,name=dict['hostname'],worker_ip=dict['ip'])[0]
            except Exception as e:
                logger.error(e)
            if len(workers)==1:
                logger.debug('get worker')
                worker=workers[0]
                worker_value={}
                worker_value['id'] = worker.id
                worker_value['ip'] = dict['ip']
                worker_value['version'] = dict['version']
                group=self.db.group_get_by_name(super_context,dict['group'])
                worker_value['group_id'] =group.id
                worker_value['group_name'] = group.name
                worker_value['status'] = 'Active'
                worker_value['start_at'] = int(time.time())
                worker_value['last_report'] = int(time.time())
                try:
                    self.db.update_worker(super_context,worker_value)
                except Exception as e:
                    logger.error(e)
                addr=(worker.ip,int(self.port))
                if worker.ip == '10.202.127.11':
                    addr = (worker.ip, 22222)
                info = {}
                info['data'] = "{'type':'start'}"
                info['addr'] =addr
                self.message.issued(info)
                logger.debug('send msg to client')
                try:
                    self.update_worker(worker.id,True)
                    logger.debug('update_worker end')
                except Exception as e:
                    logger.error(e)
            elif len(workers)==0:
                worker_value={}
                worker_value['name']=dict['hostname']
                worker_value['ip']=dict['ip']
                worker_value['version'] = dict['version']
                group=self.db.group_get_by_name(super_context,dict['group'])
                worker_value['group_id'] =group.id
                worker_value['group_name']=  group.name
                worker_value['status'] = 'Active'
                worker_value['start_at'] = int(time.time())
                worker_value['last_report'] = int(time.time())
                try:
                    worker=self.db.create_worker(super_context,worker_value)
                except Exception as e:
                    logger.error(e)
                addr=(worker.ip,int(self.port))
                if worker.ip == '10.202.127.11':
                    addr = (worker.ip, 22222)
                info = {}
                info['data'] = "{'type':'start'}"
                info['addr'] =addr
                self.message.issued(info)
            else:
                logger.error('more than one client has same information')
        elif msg['type'] == 'keepalive':
            dict = msg['data']
            try:
                workers=self.db.get_workers(super_context,name=dict['hostname'],worker_ip=dict['ip'])[0]
            except Exception as e:
                logger.error(e)
            if  len(workers) == 1:
                worker=workers[0]
                worker_value={}
                worker_value['id'] = worker.id
                worker_value['name']=dict['hostname']
                worker_value['ip']=dict['ip']
                worker_value['last_report'] = int(time.time())
                try:
                    worker=self.db.update_worker(super_context,worker_value)
                    logger.debug('the worker which ip is %s,hostname is %s is alive'%(worker_value['ip'],worker_value['name']))
                except Exception as e:
                    logger.error(e)

            else:
                logger.error('more than one client has same information or has no client')



class Workerpool(threading.Thread):
    def __init__(self,message,i,server):
        threading.Thread.__init__(self)
        self.message=message
        self.name=i
        self.s=server



    def run(self):  # listen msg from clien
        logger.debug('workerpool  %s start'%self.name)

        while True:
            if self.message.con.acquire():
                if not self.message.q.empty():
                        msg = self.message.get_queue()
                        self.message.con.release()
                        msg_data = msg.split(":", 1)[1]
                        #logger.debug(self.name,'get meg',str(msg_data))
                        date = eval(msg_data)

                        self.s.to_db(date)


                else:
                        self.message.con.wait(1)
                        self.message.con.release()
                #time.sleep(1)



