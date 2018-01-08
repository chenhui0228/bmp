import os, sys
from datetime import *
import time
from servermessage import Message,Performance
import ConfigParser
sys.path.append('../')
from db.sqlalchemy import api as db_api
from db.sqlalchemy import models
from threading import Lock
import threading
import six
import logging
import Queue
logger=logging.getLogger('backup')

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


class Return:
    """
    According to the client's return, modify the backupstate table
    """
    def __init__(self,db,server):
        self.db=db
        self.server=server

    def __call__(self, message_dict):
        dict = message_dict.get('data')
        logger.debug(str(dict))
        bk_value = {}
        bk_value['id'] = dict.get('bk_id')
        bk_value['task_id'] = dict.get('id')
        typeofMessage = dict['sub']
        if typeofMessage == 'frist':
            # The first time a single task returns, the server will create a new one in backupstate,The main content is start_time,total_size
            try:
                bk=self.db.get_bk_state(super_context,bk_value['id'])
                logger.error('the backup_state %s created before get command to create it'%bk_value['id'])
                return
            except:
                pass
            bk_value['start_time'] = dict.get('start_time')
            bk_value['total_size'] = dict.get('total_size')
            bk_value['process'] = str(dict.get('process'))
            bk_value['state'] = dict.get('state')
            if str(bk_value['total_size']) == '-1':
                num=-1
            else:
                num=0
            try:
                # Record the progress of the task execution
                if self.server.workstatelock.acquire():
                    self.server.workstate_dict[dict['bk_id']] =num
                    self.server.workstatelock.release()
                bk = self.db.bk_create(super_context, bk_value)
                logger.info("create new one in backupstate which id is %s"%bk.id)
            except Exception as e:
                logger.error(e)
            return
        elif typeofMessage == 'run':
            # Return of a single task during execution,The main content is process,current_size
            try:
                bk_old = self.db.get_bk_state(super_context, bk_value['id'])
            except Exception, e:
                logger.error(str(e))
                return
            if bk_old.state == 'failed' or bk_old.state == 'success':
                logger.error('then you get the message in run,the work is end')
                return
            bk_value['process'] = str(dict.get('process'))
            bk_value['current_size'] = int(dict.get('current_size'))
            logger.debug(str(self.server.workstate_dict))
            if self.server.workstatelock.acquire():
                if not self.server.workstate_dict.has_key(dict['bk_id']):
                    self.server.workstatelock.release()
                    return
                if int(self.server.workstate_dict[dict['bk_id']]) > int(dict['process']):
                    self.server.workstatelock.release()
                    return
                else:
                    self.server.workstate_dict[dict['bk_id']] = int(dict['process'])
                    self.server.workstatelock.release()
            try:
                self.db.bk_update(super_context, bk_value)
                logger.info("update one in backupstate which id is %s" % bk.id)
            except Exception as e:
                logger.error(e)
            return
        elif typeofMessage == 'last':
            # The last return of a single mission,The main content is end_time,message(Wrong log)
            if self.server.workstatelock.acquire():
                try:
                    del self.server.workstate_dict[dict['bk_id']]
                except Exception, e:
                    logger.error(e.message)
                self.server.workstatelock.release()
            try:
                task = self.db.get_task(super_context, bk_value['task_id'])
            except Exception, e:
                logger.error(e.message)
                bk_value['end_time'] = dict.get('end_time')
                bk_value['message'] = dict.get('message')+'you get the message that the backup_state is finished before it created,there must be sometings wrong'
                bk_value['state'] = dict.get('state')
                try:
                    bk = self.db.bk_create(super_context, bk_value)
                except Exception as e:
                    logger.error(e)
                return
            bk_value['state'] = dict.get('state')
            if (task.source[0] == 'f' or task.source[0] == 'g') and bk_value['state'] == 'success':
                bk_value['process'] = 100
                try:
                    bk_old = self.db.get_bk_state(super_context, bk_value['id'])
                    bk_value['current_size'] = int(bk_old.total_size)
                except Exception, e:
                    logger.error(e.message)
            bk_value['end_time'] = dict.get('end_time')
            bk_value['message'] = dict.get('message')
            try:
                time.sleep(1)
                self.db.bk_update(super_context, bk_value)
            except Exception, e:
                logger.error(str(bk_value))
                logger.error(e.message)
                return
        elif typeofMessage == 'delete':
            # Delete the backup file
            backupstate_list = self.db.bk_list(super_context, task_id=dict['id'])[0]
            for line in backupstate_list:
                logger.debug(line.id)
                if line.start_time == dict['start_time']:
                    logger.debug('find backupstate')
                    try:
                        self.db.bk_delete(super_context, line.id)
                    except Exception as e:
                        logger.error(e)
                        return
                    logger.info('delete a backupstate which id is %s' % bk_value['id'])
                    return


class State:
    """
    According to the client's return, modify the task table's state
    """
    def __init__(self,db,server):
        self.db=db
        self.server=server

    def __call__(self, message_dict):
        dict = message_dict['data']
        task_dict = {}
        task_dict['id'] = dict['id']
        task_dict['state'] = dict['state']
        if task_dict['state'] == 'running_s' or task_dict['state'] == 'running_w':
            bk_id = dict.get('bk_id')
            try:
                bk_old = self.db.get_bk_state(super_context, bk_id)
                if bk_old.state == 'success' or bk_old.state == 'failed' or bk_old.state == 'aborted':
                    task_dict['state'] = 'waiting'
            except:
                pass
        logger.debug(str(dict))
        if dict['state'] == 'deleted':
            task_dict['deleted'] == 'deleted'
        try:
            self.db.update_task(super_context, task_dict)
            logger.debug('the work %s state change to %s'%(task_dict['id'],task_dict['state']))
        except Exception as e:
            logger.error(e.message)
        logger.info('change task %s state to %s'%(task_dict['id'],task_dict['state']))


class Initialize:
    """
    After the client starts, send Initialize message to the server,
    server to determine whether there is a worker, the task of issuing
    the worker, did not create a new worker
    """
    def __init__(self,db,server):
        self.db=db
        self.server=server

    def __call__(self, message_dict):
        dict = message_dict['data']
        try:
            workers = self.db.get_workers(super_context, name=dict['hostname'], worker_ip=dict['ip'])[0]
        except Exception as e:
            logger.error(e)
            return
        if len(workers) == 1:
            # There is a worker
            logger.debug('get worker')
            worker = workers[0]
            worker_value = {}
            worker_value['id'] = worker.id
            worker_value['ip'] = dict['ip']
            worker_value['version'] = dict['version']
            group = self.db.group_get_by_name(super_context, dict['group'])
            worker_value['group_id'] = group.id
            worker_value['group_name'] = group.name
            worker_value['status'] = 'Active'
            worker_value['start_at'] = int(time.time())
            worker_value['last_report'] = int(time.time())
            try:
                self.db.update_worker(super_context, worker_value)
            except Exception as e:
                logger.error(e)
            addr = (worker.ip, int(self.server.client_port))
            info = {}
            info['data'] = "{'type':'start'}"
            info['addr'] = addr
            self.server.message.issued(info)
            logger.debug('send msg to client')
            # Deliver the job on this worker
            try:
                self.server.update_worker(worker.id, True)
                logger.debug('update_worker end')
            except Exception as e:
                logger.error(e)
        elif len(workers) == 0:
            # No worker
            worker_value = {}
            worker_value['name'] = dict['hostname']
            worker_value['ip'] = dict['ip']
            worker_value['version'] = dict['version']
            # Query group information
            try:
                group = self.db.group_get_by_name(super_context, dict['group'])
            except Exception, e:
                logger.error(e.message)
                addr=(dict['ip'],int(self.server.client_port))
                info = {}
                info['data'] = "{'type':'start','data':'%s is not exist'}"%dict['group']
                info['addr'] = addr
                self.server.message.issued(info)
                return
            worker_value['group_id'] = group.id
            worker_value['group_name'] = group.name
            worker_value['status'] = 'Active'
            worker_value['start_at'] = int(time.time())
            worker_value['last_report'] = int(time.time())
            # Create a worker
            try:
                worker = self.db.create_worker(super_context, worker_value)
            except Exception as e:
                logger.error(e)
                return
            addr = (worker.ip, int(self.server.client_port))
            info = {}
            info['data'] = "{'type':'start'}"
            info['addr'] = addr
            self.server.message.issued(info)
        else:
            logger.error('more than one client has same information')


class Keepalive:
    """
    Process client sends heartbeat message
    """
    def __init__(self,db,server):
        self.db=db
        self.server=server

    def __call__(self, message_dict):
        dict = message_dict['data']
        try:
            workers = self.db.get_workers(super_context, name=dict['hostname'], worker_ip=dict['ip'])[0]
        except Exception as e:
            logger.error(e)
            return
        if len(workers) == 1:
            worker = workers[0]
            worker_value = {}
            worker_value['id'] = worker.id
            worker_value['name'] = dict['hostname']
            worker_value['ip'] = dict['ip']
            worker_value['last_report'] = int(time.time())
            try:
                worker = self.db.update_worker(super_context, worker_value)
                logger.debug(
                    'the worker which ip is %s,hostname is %s is alive' % (worker_value['ip'], worker_value['name']))
            except Exception as e:
                logger.error(e)
        else:
            logger.error('more than one client has same information or has no client')


class Process_returnMessagedict:
    """
    Dispatch process returns information
    """

    def __init__(self,db,server):
        self.db=db
        self.server=server
        self.command_dict={}
        self.command_initialization()

    def command_initialization(self):
        # Function registration
        retur=Return(self.db,self.server)
        state=State(self.db,self.server)
        initialize=Initialize(self.db,self.server)
        keepalive=Keepalive(self.db,self.server)
        self.command_dict['return']=retur
        self.command_dict['state']=state
        self.command_dict['initialize']=initialize
        self.command_dict['keepalive']=keepalive

    def processMessage(self,message_dict):
        type=message_dict.get('type')
        if not type:
            logger.error('the message %s is incomplete')
            return
        else:
            self.command_dict[type](message_dict)



class Send_Keepalive(threading.Thread):
    """
    Send heartbeat regularly
    """
    def __init__(self,db,server):
        threading.Thread.__init__(self)
        self.db=db
        self.server=server

    def run(self):
        self.t = threading.Timer(self.server.timer_interval, self.keeplaive)
        self.t.setDaemon(True)
        self.t.start()

    def keeplaive(self):
        logger.debug('start sned keepalive %s' % str(self.server.workeralivedict))
        workers = self.db.get_workers(super_context)
        workersnum = workers[1]
        workerslist = workers[0]
        for i in range(workersnum):
            worker = workerslist[i]
            worker_id = worker.id
            data = "{'type':'keepalive'}"
            info = {}
            addr = (worker.ip, int(self.server.client_port))
            info['data'] = data
            info['addr'] = addr
            self.server.message.issued(info)
            last_update = int(worker.last_report)
            now = int(time.time())
            logger.debug(
                'the worker is %s,status is %s,interval is %s' % (worker_id, worker.status, str(now - last_update)))
            # According to the current time and the client last reported
            # time difference is greater than 4 times the delivery cycle
            # to determine whether the client Offline,
            if worker.status == 'Active':
                if now - last_update >= 4 * self.server.timer_interval:
                    worker_value = {}
                    worker_value['id'] = worker.id
                    worker_value['status'] = 'Offline'
                    try:
                        self.db.update_worker(super_context, worker_value)
                    except Exception as e:
                        logger.error(e)
                    logger.warning('the worker %s is onffline' % worker.id)

            elif worker.status == 'Offline':
                if now - last_update < 4 * self.server.timer_interval:
                    worker_value = {}
                    worker_value['id'] = worker.id
                    worker_value['status'] = 'Active'
                    try:
                        self.db.update_worker(super_context, worker_value)
                    except Exception as e:
                        logger.error(e)
        self.t = threading.Timer(self.server.timer_interval, self.keeplaive)
        self.t.setDaemon(True)
        self.t.start()

class Workerpool(threading.Thread):
    """
    Worker thread pool, server multithreading message reported by the client
    """
    def __init__(self,i,process_returnMessagedict):
        threading.Thread.__init__(self)
        self.con=threading.Condition()
        self.queue=Queue.Queue()
        self.name=i
        self.process_returnMessagedict=process_returnMessagedict

    def run(self):
        logger.debug('Workerpool %s    start')
        while True:
            if self.con.acquire():
                if not self.queue.empty():
                        message_dict = self.queue.get_nowait()
                        self.con.release()
                        self.process_returnMessagedict.processMessage(message_dict)
                        logger.debug("workerpool %s is end a work %s"%(self.name,message_dict))
                else:
                        self.con.wait(1)
                        self.con.release()


class Choose_workerpool:
    """
    Determine which single thread to process a single message. For the id of the message,
    do hash hash over id, so that the same task with the same thread of information to ensure
    that the order of treatment of the same message. No id on the news, such as heartbeat,
    let the thread's task queue to do the smallest thread
    """
    def __init__(self,workerpool_list):
        self.workerpool_list=workerpool_list

    def __call__(self, message_dict):
        data = message_dict.get('data')
        id = data.get('id')
        if id != None :
            workerpool_id=hash(id)%len(self.workerpool_list)
        else:
            min_queue_size=65536
            index=0
            for i in range(len(self.workerpool_list)):
                queue_size=self.workerpool_list[i].queue.qsize()
                if queue_size<min_queue_size:
                    index=i
                    min_queue_size=queue_size
            workerpool_id=index
        try:
            logger.debug("%s %s" % (workerpool_id, id))
            self.workerpool_list[workerpool_id].con.acquire()
            self.workerpool_list[workerpool_id].queue.put_nowait(message_dict)
            self.workerpool_list[workerpool_id].con.notify()
            self.workerpool_list[workerpool_id].con.release()
        except Exception as e:
            logger.error(e.message)


@six.add_metaclass(Singleton)
class Server:
    """
    For delivery operation.The parameters of each function 'id', almost all task id, if not, will explain
    """
    def __init__(self,conf):
        mysqlconf = conf.get('database')
        try:
            self.db= db_api.get_database(mysqlconf)
        except Exception as e:
            logger.error(e)
            return
        server_dict=conf.get('servercontroller')
        logger.info(str(server_dict))
        self.server_port=server_dict['server_port']
        self.client_port=server_dict['client_port']
        self.worker_size=int(server_dict['worker_size'])
        self.timer_interval=server_dict['timer_interval']
        if self.server_port==None or self.timer_interval == None or self.worker_size == None or self.client_port == None:
            logger.error('conf is lost')
            logger.error(str(conf))
            return

        self.workstate_dict={}
        self.message = Message('tcp',self.server_port,self.client_port)
        self.message.start_server()
        self.alivelock=threading.Lock()
        self.workstatelock = threading.Lock()
        self.workeralivedict={}
        self.workerpool_list=[]
        self.process_returnMessagedict = Process_returnMessagedict(self.db, self)
        self.create_workerpool()
        self.choose_workerpool=Choose_workerpool(self.workerpool_list)
        self.create_listen()
        self.create_sendKeepalive()


    def create_workerpool(self):
        """
        Create a thread pool
        """
        for i in range(self.worker_size):
            t=Workerpool(i,self.process_returnMessagedict)
            t.setDaemon(True)
            self.workerpool_list.append(t)
            t.start()

    def create_sendKeepalive(self):
        """
        Create a thread pool
        """


        t=Send_Keepalive(self.db,self)
        t.setDaemon(True)
        t.start()


    def create_listen(self):
        """
        Create monitor
        """

        listen=Listen(self.message,self.choose_workerpool)
        listen.setDaemon(True)
        try:
            listen.start()
        except Exception as e:
            logger.error(e)

    def pause(self,id,deleted=False,stopped=False):
        try:
            task = self.db.get_task(super_context,id,deleted=deleted)
        except Exception as e:
            logger.error(e.message)
            return
        worker = task.worker
        addr = (worker.ip, int(self.client_port))
        if stopped:
            data = "{'type':'pause','data':{'id':'%s','stop':'True'}}" % (id)
        else:
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
        """
        Stop the task by strategy backup
        """
        logger.info('stop task %s'%id)
        try:
            task = self.db.get_task(super_context,id)
        except Exception as e:
            logger.error(e.message)
            return
        worker = task.worker
        addr = (worker.ip, int(self.client_port))
        # Stop the current task execution
        self.pause(id,False,True)
        data = "{'type':'delete','data':{'id':'%s'}}" % (id)
        info = {}
        info['data'] = data
        info['addr'] = addr
        # Remove this task from the client
        try:
            self.message.issued(info)
        except Exception as e:
            logger.error(e)

    def delete(self,id):
        """
        Delete the task
        """
        logger.info('delete task %s' % id)
        try:
            task = self.db.get_task(super_context,id,deleted=True)
        except Exception as e:
            logger.error(e.message)
            return
        worker = task.worker
        addr = (worker.ip, int(self.client_port))
        # Stop the current task execution
        self.pause(id,True)
        task_value = {}
        task_value['id'] = id
        task_value['state'] = 'deleteing'
        data = "{'type':'delete','data':{'id':'%s','deletework':'yes'}}" % (id)
        info = {}
        info['data'] = data
        info['addr'] = addr
        if task.type == 'backup' or task.type == 'dump':
            if task.state == 'stopped' or task.state == 'running_s':
                #  For the task has been stopped, the client did not
                #  retain the task information, the task needs to be issued
                self.backup(task.id)
            try:
                self.message.issued(info)
                self.db.update_task(super_context, task_value)
            except Exception as e:
                logger.error(e)
        else:
            #   For recover tasks, because
            #   they are executed immediately, you can delete
            try:
                task_value['state'] = 'deleted'
                task_value['deleted'] = 'deleted'
                self.db.update_task(super_context, task_value)
            except Exception as e:
                logger.error(e)

    def resume(self,id):
        """
        Task recovery is executed by strategy
        """
        logger.info('resume task %s' % id)
        try:
            task = self.db.get_task(super_context,id)
        except Exception as e:
            logger.error(e.message)
            return
        task_value={}
        task_value['id']=task.id
        task_value['state']='waiting'
        try:
            self.db.update_task(super_context,task_value)
        except Exception as e:
            logger.error(e.message)
            return
        if task.type=='backup':
            self.backup(id)
        elif task.type=='recover':
            self.recover(id)

    def update_task(self,id,isRestart=False):
        """
        With new tasks

        :param isRestart: Whether the task is because the client started and need to be issued
        """
        if not isRestart:
            logger.info('update_task start %s'%id)
        else:
            logger.debug('update_task start %s' % id)
        try:
            task = self.db.get_task(super_context,id,deleted=True)
        except Exception as e:
            logger.error(e.message)
            return
        if task.state == 'stopped' or task.state == 'running_s':
            if isRestart:
                # Client restart stopped tasks do not need to be issued
                task_value={}
                task_value['id']=task.id
                task_value['state']='stopped'
                try:
                    self.db.update_task(super_context,task_value)
                except Exception as e:
                    logger.error(e.message)
            return
        worker = task.worker
        policy = task.policy
        addr = (worker.ip, int(self.client_port))
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
                instance=task.name.split('_')[1]
                data2['instance']=instance
        if task.source.split('/', 1)[0] == 'shell:':
            data2['sub']='dump'
            instance = task.name.split('_')[1]
            data2['instance'] = instance


        info = {}
        info['data'] = str(data)
        info['addr'] = addr
        self.message.issued(info)

    def update_worker(self,id,isRestart=False,**kwargs):
        """
        With new worker
        :param id: worker id
        :param isRestart: Whether the task is because the client started and need to be issued
        """
        if not isRestart:
            logger.info('update_worker  %s'%id)
        else:
            logger.debug('update_worker  %s' % id)
        try:
            tasks_all=self.db.get_tasks(super_context,worker_id=id)
        except Exception as e:
            logger.error(e.message)
            return
        tasks=tasks_all[0]
        try:
            worker = self.db.get_worker(super_context, id)
        except Exception as e:
            logger.error(e)
            return
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
            # If the new and old workers ip different, you need
            # to delete the old task now the old worker, and
            # then create a new task on the new worker
            for task in tasks:
                if task.worker_id == id:
                    addr = (old_ip, int(self.client_port))
                    data = "{'typr':'delete','data':{'id':'%s','changeworker':'yes'}}" % task.id
                    info = {}
                    info['data'] = data
                    info['addr'] = addr
                    self.message.issued(info)
            for task in tasks:
                if task.worker_id == id:
                    self.update_task(task.id)

    def update_policy(self,id):
        """
        With new policy
        :param id: policy id
        """
        logger.info('update_policy %s'%id)
        try:
            tasks=self.db.get_tasks(super_context)[0]
        except Exception as e:
            logger.error(e.message)
            return
        for task in tasks:
            if task.policy_id == id:
                self.update_task(task.id)

    def backup(self,id,do_type=False):
        """
        Create a new backup task
        :param do_type: if do it immediately
        """
        logger.info('create a backup task %s'%id)
        try:
            task = self.db.get_task(super_context,id,deleted=True)
        except Exception as e:
            logger.error(e.message)
            return
        worker = task.worker
        policy = task.policy
        addr = (worker.ip, int(self.client_port))
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
                data2=data['data']
                instance=task.name.split('_')[1]
                data2['instance']=instance
        except Exception as e:
            logger.error(e)
            return
        info = {}
        info['data'] = str(data)
        info['addr'] = addr
        self.message.issued(info)

    def recover(self,id):
        """
        Create a recovery task:
        """
        logger.info('create a recover task %s' % id)
        try:
            task = self.db.get_task(super_context, id)
            worker = task.worker
            policy = task.policy
            addr = (worker.ip, int(self.client_port))
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
            return
        run_sub='immediately'
        data = "{'type':'recover','data':{'id':'%s','name':'%s','state':'%s'," \
               "'source_vol':'%s','source_address':'%s','destination_address': '%s'," \
               "'destination_ip':'%s','run_sub':'%s'}} " % (id, task.name, task.state, vol,  dir ,destination, worker.ip,run_sub)
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)



class Listen(threading.Thread):
    """
    Listen to the message queue
    """
    def __init__(self,message,choose_workerpool):
        threading.Thread.__init__(self)
        self.message=message
        self.choose=choose_workerpool

    def run(self):  # listen msg from clien
        logger.debug('Listen   start')
        while True:
            if self.message.con.acquire():
                if not self.message.q.empty():
                        msg = self.message.get_queue()
                        self.message.con.release()
                        message_dict = []
                        logger.info(msg)
                        try:
                            msg_list=msg.split("}{")
                            if len(msg_list) == 1:
                                message_dict = eval(msg)
                                logger.debug(message_dict)
                            elif len(msg_list) > 1:
                                for i in range(len(msg_list)):
                                    if i == 0:
                                        msg_list[i] = msg_list[i] + "}"
                                    else:
                                        msg_list[i] = "{"+msg_list[i]
                                for msg_data_inlist in msg_list:
                                    message_dict = eval(msg_data_inlist)
                                    logger.debug(message_dict)
                        except Exception as e:
                            logger.error(e)
                            continue
                        self.choose(message_dict)
                else:
                        self.message.con.wait(1)
                        self.message.con.release()
                #time.sleep(1)


