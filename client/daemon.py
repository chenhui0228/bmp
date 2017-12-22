#!/usr/bin/env python
# coding:utf-8
import sys
import os
import atexit
from signal import SIGTERM
import threading
from threading import Timer
from datetime import *
import time
import Queue
import socket
from apscheduler.schedulers.background import BackgroundScheduler
from message import Message
from singletask import SingleTask
from workerpool import WorkerPool,Delete
import ConfigParser
import logging
#logging.basicConfig()

def send_server(message,log,send_type,**kwargs):
    if send_type == 'state':
        id=kwargs.get('id')
        value=kwargs.get('state')
        data = "{'type':'state','data':{'id':'%s','state':'%s'}}" % (id, value)
        ret = message.send(data)
        if ret != 0:
            log.logger.error('message send failed %s' % ret)
    elif send_type == 'keepalive':
        ip=kwargs.get('ip')
        hostname = kwargs.get('hostname')
        version = kwargs.get('version')
        group = kwargs.get('group')
        data = "{'type': 'keepalive', 'data': {'ip': '%s', 'hostname': '%s', 'version': '%s','group':'%s'}}" % (ip, hostname, version, group)
        try:
            message.send(data)
        except Exception as e:
            log.logger.error(e.message)
    elif send_type =='initialize':
        ip=kwargs.get('ip')
        hostname = kwargs.get('hostname')
        version = kwargs.get('version')
        group = kwargs.get('group')
        data = "{'type': 'initialize', 'data': {'ip': '%s', 'hostname': '%s', 'version': '%s','group':'%s'}}" % (ip, hostname, version, group)
        try:
            message.send(data)
        except Exception as e:
            log.logger.error(e.message)
    else:
        pass

class Backup:
    def __init__(self,log,task_dict,glusterip_list,q,message,task_update,scheduler,queue_task_list,workpool_workid_dict):
        self.q=q
        self.glusterip_list=glusterip_list
        self.log=log
        self.task_dict=task_dict
        self.message=message
        self.task_sum= task_update.task_sum
        self.scheduler=scheduler
        self.queue_task_list=queue_task_list
        self.workpool_workid_dict=workpool_workid_dict

    def __call__(self, message_dict):
        dict = message_dict['data']
        if dict['run_sub'] == 'date':
            self.addtask(message_dict, 'date')
        elif dict['run_sub'] == 'cron':
            self.addtask(message_dict, 'cron')
        elif dict['run_sub'] == 'immediately':
            dict = message_dict['data']
            dict['op'] = "backup"
            dict['ip'] = self.glusterip_list
            put_in_queue=True
            for workpool_id,task_id in self.workpool_workid_dict.items():
                if task_id == dict['id']:
                    put_in_queue=False
            if dict['id'] in self.queue_task_list:
                put_in_queue=False
            if put_in_queue:
                self.q.put([str(dict), 2], block=True, timeout=None)
                self.queue_task_list.append(dict['id'])
                send_server(self.message,self.log,'state',id=dict['id'], state='waiting')
            else:
                self.log.logger.warning('%s %s is in doing or in queue' % (dict['id'], dict['name']))

    def addtask(self,data,do_type):
        dict = data['data']
        ms = dict['id']
        if self.task_dict.has_key(ms):
            self.log.logger.warning('the work %s is in client'%ms)
            send_server(self.message, self.log, 'state', id=dict['id'], state='waiting')
            return
        dict['op'] =data['type']
        self.log.logger.info('create a new %s backup work,the id of it is %s' %(do_type,ms) )
        new_task = SingleTask(ms, self.scheduler, dict, self.q, self.glusterip_list, self.log,self.queue_task_list,self.workpool_workid_dict)
        new_task.start(do_type)
        self.task_dict[ms] = new_task
        self.task_sum = self.task_sum + 1
        send_server(self.message,self.log,'state', id=dict['id'], state='waiting')

class Update:
    def __init__(self,log,task_dict,glusterip_list,q,message,task_update,scheduler,queue_task_list,workpool_workid_dict):
        self.q=q
        self.glusterip_list=glusterip_list
        self.log=log
        self.task_dict=task_dict
        self.message=message
        self.task_sum=task_update.task_sum
        self.scheduler=scheduler
        self.queue_task_list=queue_task_list
        self.workpool_workid_dict=workpool_workid_dict

    def __call__(self, message_dict):
        dict = message_dict['data']
        self.log.logger.info('change a work,the id of it is %s' % dict['id'])
        ms = dict['id']
        if self.task_dict.has_key(ms):
            try:
                self.task_dict[ms].do_remove_job()
                del self.task_dict[ms]
                self.task_sum = self.task_sum - 1
                dict['op'] = dict['sub']
                new_task = SingleTask(ms, self.scheduler, dict, self.q, self.glusterip_list, self.log,self.queue_task_list,self.workpool_workid_dict)
                new_task.start(dict['run_sub'])
                self.task_dict[ms] = new_task
                self.task_sum = self.task_sum + 1
                send_server(self.message,self.log, 'state', id=dict['id'], state='waiting')
            except:
                pass
        else:
            self.log.logger.error('No any work which id is %s' % ms)

class Recover:
    def __init__( self,log,task_dict,glusterip_list,q,message,queue_task_list,workpool_workid_dict ):
        self.q=q
        self.glusterip_list=glusterip_list
        self.log=log
        self.task_dict=task_dict
        self.message=message
        self.queue_task_list=queue_task_list
        self.workpool_workid_dict=workpool_workid_dict

    def __call__(self, message_dict):
        dict = message_dict['data']
        if dict['run_sub'] == 'immediately':
            dict = message_dict['data']
            dict['op'] = "recover"
            dict['ip'] = self.glusterip_list
            put_in_queue=True
            for workpool_id,task_id in self.workpool_workid_dict.items():
                if task_id == dict['id']:
                    put_in_queue=False
            if dict['id'] in self.queue_task_list:
                put_in_queue=False
            if put_in_queue:
                self.q.put([str(dict), 2], block=True, timeout=None)
                self.queue_task_list.append(dict['id'])
                send_server(self.message,self.log,'state',id=dict['id'], state='waiting')
            else:
                self.log.logger.warning('%s %s is in doing or in queue' % (dict['id'], dict['name']))
        else:
            self.log.logger.error('recover  must be immediately')

class Deleted:
    def __init__( self,log,task_dict,glusterip_list,q,message,task_update,queue_task_list ):
        self.q=q
        self.glusterip_list=glusterip_list
        self.log=log
        self.task_dict=task_dict
        self.message=message
        self.task_sum=task_update.task_sum
        self.queue_task_list=queue_task_list

    def __call__(self, message_dict):
        # print "do delete"
        dict = message_dict['data']
        self.log.logger.info('delete a work,the id of it is %s' % dict['id'])
        ms = dict['id']
        if dict.has_key('deletework'):
            self.deleteAllDataOfaWork(dict['id'])
        if self.task_dict.has_key(ms):
            self.task_dict[ms].do_remove_job()
            del self.task_dict[ms]
            self.task_sum = self.task_sum - 1
        else:
            self.log.logger.error('No any work which id is %s' % ms)
        if dict.has_key('delete'):
            send_server(self.message,self.log, 'state', id=ms, state='deleted')
        elif dict.has_key('changeworker'):
            pass
        else:
            send_server(self.message,self.log, 'state', id=ms, state='stopped')

    def deleteAllDataOfaWork(self,id):
        task_list = self.task_dict
        task = task_list[id]
        msg = task.st
        duration = msg.get('duration')
        vol = msg.get('destination_vol')
        dir = msg.get('destination_address')
        name = msg.get('name')
        id = msg.get('id')
        dict={}
        dict['duration'] = duration
        dict['vol'] = vol
        dict['dir'] = dir
        dict['name'] = name
        dict['id'] = id
        dict['op'] = 'delete'
        dict['state'] = 'deleting'
        dict['ip']=self.glusterip_list
        if duration != None or vol != None or dir != None or id != None:
            self.q.put([str(dict), 2], block=True, timeout=None)
            self.queue_task_list.append(dict['id'])

    def deleteBackupData(self):
        task_dict=self.task_dict
        for ms in task_dict:
            task=task_dict[ms]
            msg=task.st
            duration=msg.get('duration')
            vol=msg.get('destination_vol')
            dir=msg.get('destination_address')
            name=msg.get('name')
            id = msg.get('id')
            dict={}
            dict['duration'] = duration
            dict['vol'] = vol
            dict['dir'] = dir
            dict['name'] = name
            dict['id'] = id
            dict['op'] = 'delete'
            dict['state'] = 'deleting'
            dict['ip'] = self.glusterip_list
            if duration!=None or vol !=None or dir!=None:
                t=Delete(self.log,duration=duration,vol=vol,dir=dir,ip=self.glusterip_list,name=name,id=id)
                t.start()

class Dump:
    def __init__(self,log,task_dict,glusterip_list,q,message,task_update,scheduler,queue_task_list,workpool_workid_dict ):
        self.q=q
        self.glusterip_list=glusterip_list
        self.log=log
        self.task_dict=task_dict
        self.message=message
        self.task_sum=task_update.task_sum
        self.scheduler=scheduler
        self.queue_task_list=queue_task_list
        self.workpool_workid_dict=workpool_workid_dict

    def __call__(self, message_dict):
        dict = message_dict['data']
        if dict['run_sub'] == 'cron':
            self.addtask(message_dict, 'cron')
        elif dict['run_sub'] == 'date':
            self.addtask(message_dict, 'date')
        elif dict['run_sub'] == 'immediately':
            dict = message_dict['data']
            dict['op'] = "dump"
            dict['ip'] = self.glusterip_list
            put_in_queue=True
            for workpool_id,task_id in self.workpool_workid_dict.items():
                if task_id == dict['id']:
                    put_in_queue=False
            if dict['id'] in self.queue_task_list:
                put_in_queue=False
            if put_in_queue:
                self.q.put([str(dict), 2], block=True, timeout=None)
                self.queue_task_list.append(dict['id'])
                send_server(self.message,self.log,'state',id=dict['id'], state='waiting')
            else:
                self.log.logger.warning('%s %s is in doing or in queue' % (dict['id'], dict['name']))

    def addtask( self, data, do_type ):
        dict = data['data']
        ms = dict['id']
        if self.task_dict.has_key(ms):
            self.log.logger.warning('the work %s is in client'%ms)
            send_server(self.message, self.log, 'state', id=dict['id'], state='waiting')
            return
        dict['op'] = data['type']
        self.log.logger.info('create a new %s dump work,the id of it is %s' % (do_type, ms))
        new_task = SingleTask(ms, self.scheduler, dict, self.q, self.glusterip_list, self.log,self.queue_task_list,self.workpool_workid_dict)
        new_task.start(do_type)
        self.task_dict[ms] = new_task
        self.task_sum = self.task_sum + 1
        send_server(self.message,self.log, 'state', id=dict['id'], state='waiting')

class Keepalive:
    def __init__( self,log,message,clientip,hostname,version,group):
        self.log=log
        self.message=message
        self.clientip=clientip
        self.hostname=hostname
        self.version=version
        self.group=group

    def __call__(self, message_dict):
        send_server(self.message,self.log,'keepalive',ip=self.clientip,hostname=self.hostname,version=self.version,group=self.group)

class Pause:
    def __init__( self,log,tp ,workpool_workid_dict):
        self.log=log
        self.tp=tp
        self.workpool_workid_dict=workpool_workid_dict

    def __call__(self, message_dict):
        dict = message_dict['data']
        ms = dict['id']
        for t in self.tp:
            if self.workpool_workid_dict.has_key(t.name):
                if self.workpool_workid_dict[t.name] == ms:
                    try:
                        if dict.has_key('stop'):
                            t.stopwork(False)

                        else:
                            t.stopwork()
                    except Exception as e:
                        self.log.logger.error(e.message)
                    break

class Pauseall:
    def __init__(self,log,tp ,workpool_workid_dict,client,task_update):
        self.log=log
        self.tp=tp
        self.workpool_workid_dict=workpool_workid_dict
        self.client=client
        self.task_update=task_update

    def __call__(self, message_dict):
        self.task_update.client_stop=True
        self.client.backup_and_dump_queue.queue.clear()
        self.client.recover_and_workimmediately_queue.queue.clear()
        self.pauseall()
        self.log.logger.info('pause all work')
        time.sleep(10)
        self.client.stopclient()

    def pauseall(self):
        for t in self.tp:
            if self.workpool_workid_dict.has_key(t.name):
                try:
                    t.stopwork()
                except Exception as e:
                    self.log.logger.error(e.message)
                    break

class First:
    def __init__(self,log):
        self.log=log

    def __call__(self, message_dict):
        data=message_dict.get('data')
        if data:
            self.log.logger.error(data)

class Task_Undate:
    def __init__(self,client):
        self.q=client.recover_and_workimmediately_queue
        self.glusterip_list=client.glusterip_list
        self.log=client.log
        self.message=client.message
        self.command_dict={}
        self.task_dict={}
        self.tp=client.tp
        self.workpool_workid_dict=client.workpool_workid_dict
        self.queue_task_list=client.queue_task_list
        self.client=client
        self.ip=client.ip
        self.hostname=client.hostname
        self.version=client.version
        self.group=client.group
        self.task_sum=0
        self.scheduler = BackgroundScheduler()
        self.client_stop=False
        self.command_initialization()

    def periodic_deletion(self):
        ret = self.scheduler.add_job(self.command_dict['delete'].deleteBackupData, 'cron', hour='0', minute='0', second='0')
        self.scheduler.start()



    def command_initialization(self):
        backup=Backup(self.log,self.task_dict,self.glusterip_list,self.q,self.message, self,self.scheduler,self.queue_task_list,self.workpool_workid_dict)
        update=Update(self.log,self.task_dict,self.glusterip_list,self.q,self.message, self,self.scheduler,self.queue_task_list,self.workpool_workid_dict)
        recover=Recover(self.log,self.task_dict,self.glusterip_list,self.q,self.message,self.queue_task_list,self.workpool_workid_dict)
        delete=Deleted(self.log,self.task_dict,self.glusterip_list,self.q,self.message, self,self.queue_task_list)
        dump=Dump(self.log,self.task_dict,self.glusterip_list,self.q,self.message, self,self.scheduler,self.queue_task_list,self.workpool_workid_dict)
        keepalive=Keepalive(self.log,self.message,self.ip,self.hostname,self.version,self.group)
        pause=Pause(self.log,self.tp,self.workpool_workid_dict)
        pauseall=Pauseall(self.log,self.tp,self.workpool_workid_dict,self.client,self)
        first=First(self.log)
        self.command_dict['backup'] = backup
        self.command_dict['update'] = update
        self.command_dict['recover'] = recover
        self.command_dict['delete'] = delete
        self.command_dict['dump'] = dump
        self.command_dict['keepalive'] = keepalive
        self.command_dict['pause'] = pause
        self.command_dict['pauseall'] = pauseall
        self.command_dict['start'] = first
        self.periodic_deletion()

    def updatetask(self,message_dict):
        type=message_dict.get('type')
        if not type:
            self.log.logger.error('the message %s is incomplete')
            return
        else:
            if not self.client_stop:
                self.command_dict[type](message_dict)

class Listen(threading.Thread):
    def __init__(self,message,log,task_update):
        threading.Thread.__init__(self)
        self.message=message
        self.log=log
        self.task_update=task_update

    def run(self):  # listen msg from clien
        self.log.logger.debug('Listen   start')
        while True:
            if self.message.con.acquire():
                if not self.message.q.empty():
                        msg = self.message.get_queue()
                        self.message.con.release()
                        msg_data = msg.split(":", 1)[1]
                        self.log.logger.info(msg_data)
                        message_dict = eval(msg_data)
                        self.task_update.updatetask(message_dict)
                else:
                        self.message.con.wait(1)
                        self.message.con.release()
                #time.sleep(1)

class Daemon:
    def __init__(self, pidfile,  mylogger, version, stdin='/dev/stderr', stdout='/dev/stderr',
                  stderr='/dev/stderr' ):
        cp = ConfigParser.ConfigParser()
        cp.read('/etc/fbmp/client.conf')
        self.log=mylogger
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.timer_interval = int(cp.get('client', 'timer_interval'))
        self.qdpth = int(cp.get('client', 'queue_depth'))
        # print "pid file:",self.pidfile
        self.timer_id = 0
        self.workpool_size = int(cp.get('client', 'workpool_size')) # 线程池大小

        self.immediate_workpool_size = int(cp.get('client', 'immediate_workpool_size'))
        self.version = version
        self.group = cp.get('client', 'group')
        self.client_port = cp.get('client', 'client_port')
        self.info_l = ""
        self.glusterip_list = cp.get('client', 'gluster_ip').split()
        self.task_list = {}
        self.work_list=[]
        self.message = Message("tcp")
        self.tp = []
        self.hostname = str(socket.gethostname())
        self.ip = socket.gethostbyname(self.hostname)
        self.workpool_workid_dict={}

    def _daemonize( self ):
        try:
            pid = os.fork()  # 第一次fork，生成子进程，脱离父进程
            if pid > 0:
                print "backup work start in backend!"
                self.log.logger.info("backup work start in backend!")
                sys.exit(0)  # 退出主进程
        except OSError as e:
            sys.stderr.write('fork #1 failed: %d (%s)\n' %
                             (e.errno, e.strerror))
            self.log.logger.error('fork #1 failed: %d (%s)\n' %
                              (e.errno, e.strerror))
            sys.exit(1)

        os.chdir("/")  # 修改工作目录
        os.setsid()  # 设置新的会话连接
        os.umask(0)  # 重新设置文件创建权限

        try:
            pid = os.fork()  # 第二次fork，禁止进程打开终端
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            sys.stderr.write('fork #2 failed: %d (%s)\n' %
                             (e.errno, e.strerror))
            self.log.logger.error('fork #2 failed: %d (%s)\n' %
                              (e.errno, e.strerror))
            sys.exit(1)

            # 重定向文件描述符
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # 注册退出函数，根据文件pid判断是否存在进程
        atexit.register(self.delpid)
        pid = str(os.getpid())
        # print "pid is:",pid
        file(self.pidfile, 'w+').write('%s\n' % pid)
        self.log.logger.debug("pid file write succeed")

    def delpid( self ):
        os.remove(self.pidfile)

    def start( self ):
        # 检查pid文件是否存在以探测是否存在进程

        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            if os.path.exists('/proc/%s'%pid):
                message = 'pidfile %s already exist. Daemon already running!\n'
                self.log.logger.error('pidfile %s already exist. Daemon already running!\n' % self.pidfile)
                sys.stderr.write(message % self.pidfile)
                sys.stderr.flush()
                sys.exit(1)

            # 启动监控
        self.log.logger.info('client start now')
        self._daemonize()
        self._run()

    def stop(self):
        data="{'type':'pauseall'}"
        addr = (self.ip, int(self.client_port))
        info={}
        info['data']=data
        info['addr']=addr
        self.message.issued(info)
        time.sleep(10)
        try:
            # self.message.closeall()
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except Exception as err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                message = 'stop client'
                sys.stderr.write(message)
                # print str(err)
                sys.exit(1)

    def stopclient( self ):
        # 从pid文件中获取pid
        try:
           # self.message.closeall()
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None


        if not pid:  # 重启不报错
            message = 'pidfile %s does not exist. Daemon not running!\n'
            self.log.logger.error('pidfile %s does not exist. Daemon not running!\n' % (self.pidfile))
            sys.stderr.write(message % self.pidfile)
            return

            # 杀进程
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                sys.exit(1)

    def restart( self ):
        self.stop()
        self.start()


    def _timer_func( self ):
        self.timer_id = self.timer_id + 1
        """
        没过60秒判断一次线程是否挂了，如果挂了需要重新启动线程加入到threadpool中
        """

        if self.listen.isAlive():
            pass
        else:
            self.log.logger.warning('listen thread is dead ,restart it now')
            self.listen = Listen(self.message,self.log,self.task_update)
            self.listen.setDaemon(True)
            self.listen.start()

        for t in self.tp:
            if t.isAlive():
                continue
            self.log.logger.warning('there is a workpool is dead,restart it now')
            thread_number=t.getName()
            self.tp.remove(t)
            if int(thread_number)<=self.workpool_size:
                newthread = WorkerPool(self.backup_and_dump_queue, t.getName(), self.workpool_size,self.workpool_workid_dict,self.log,self.queue_task_list)
            else:
                newthread = WorkerPool(self.recover_and_workimmediately_queue, t.getName(), self.workpool_size,self.workpool_workid_dict, self.log,self.queue_task_list)
            self.tp.append(newthread)
            newthread.setDaemon(True)
            newthread.start()

        self.t = Timer(self.timer_interval, self._timer_func)
        self.t.start()


    """
    守护进程主体：
    启动timer，此timer 主要更新备份周期的功能

    """

    def _run( self ):
        """ run your fun"""
        now = datetime.now()
        self.hostname = socket.gethostname()
        os.system("ulimit -n " + "65535")
        self.log.logger.debug("To start  listen:")
        try:
            self.message.start_server()
        except:
            self.log.logger.error('client message start error')
            self.stopclient()
        self.log.logger.debug("to start timer:")
        self.t = Timer(self.timer_interval, self._timer_func)
        self.log.logger.debug('run job scheduler')
        self.log.logger.debug("To start threading pool:")
        self.backup_and_dump_queue = Queue.Queue(self.qdpth)
        self.recover_and_workimmediately_queue = Queue.Queue(self.qdpth)
        self.queue_task_list=[]
        for i in range(self.workpool_size):
            t = WorkerPool(self.backup_and_dump_queue, i,self.workpool_size ,self.workpool_workid_dict,self.log,self.queue_task_list)
            self.tp.append(t)
        for i in range(self.workpool_size,self.workpool_size+self.immediate_workpool_size):
            t = WorkerPool(self.recover_and_workimmediately_queue, i,self.workpool_size, self.workpool_workid_dict, self.log,self.queue_task_list)
            self.tp.append(t)
        for t in self.tp:
            t.setDaemon(True)
            t.start()
        self.task_update=Task_Undate(self)
        self.listen = Listen(self.message,self.log,self.task_update)
        self.listen.setDaemon(True)
        self.listen.start()
        send_server(self.message, self.log, 'initialize', ip=self.ip, hostname=self.hostname, version=self.version,group=self.group)
        self.t.start()
        self.log.logger.debug("start threadpool over")
