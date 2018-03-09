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
from workerpool import WorkerPool, Delete
import ConfigParser
import commands
import logging


# logging.basicConfig()


def send_server(message, log, send_type, **kwargs):
    """
    send message to server
    """
    if send_type == 'state':

        # send message to modify the task table state item

        id = kwargs.get('id')
        value = kwargs.get('state')
        data = "{'type':'state','data':{'id':'%s','state':'%s'}}" % (id, value)
        ret = message.send(data)
        if ret != 0:
            log.logger.error('message send failed %s' % ret)
    elif send_type == 'keepalive':
        ip = kwargs.get('ip')
        hostname = kwargs.get('hostname')
        version = kwargs.get('version')
        group = kwargs.get('group')
        data = "{'type': 'keepalive', 'data': {'ip': '%s', 'hostname': '%s', 'version': '%s','group':'%s'}}" % (
            ip, hostname, version, group)
        try:
            message.send(data)
        except Exception as e:
            log.logger.error(e.message)
    elif send_type == 'initialize':
        ip = kwargs.get('ip')
        hostname = kwargs.get('hostname')
        version = kwargs.get('version')
        group = kwargs.get('group')
        data = "{'type': 'initialize', 'data': {'ip': '%s', 'hostname': '%s', 'version': '%s','group':'%s'}}" % (
            ip, hostname, version, group)
        try:
            message.send(data)
        except Exception as e:
            log.logger.error(e.message)
    else:
        pass


class Backup:
    """
    Process backup tasks
    """

    def __init__(self, log, task_dict, glusterip_list, q, message, task_schedul, scheduler, queue_task_list,
                 workpool_workid_dict):
        self.q = q
        self.glusterip_list = glusterip_list
        self.log = log
        self.task_dict = task_dict
        self.message = message
        self.task_sum = task_schedul.task_sum
        self.task_schedul = task_schedul
        self.scheduler = scheduler
        self.queue_task_list = queue_task_list
        self.workpool_workid_dict = workpool_workid_dict

    def __call__(self, message_dict):
        """
        For non-immediate implementation of the task, to create a singlgtask class, to put the task
        on time to the appropriate work queue, waiting for the execution of the worker thread. 'Cron'
        is a periodic task, 'date' is a one-time task. 'Date' and 'immediately' the difference is
        'date' to set the execution time, and 'immediately' do not have to, immediately after receiving
        the implementation.

        For immediate execution of the task, put it directly to the appropriate work queue, wait
        Sfor the worker thread to execute it

       """
        dict = message_dict['data']
        if dict['run_sub'] == 'date':
            self.addtask(message_dict, 'date')
        elif dict['run_sub'] == 'cron':
            self.addtask(message_dict, 'cron')
        elif dict['run_sub'] == 'immediately':
            dict = message_dict['data']
            dict['op'] = "backup"
            dict['ip'] = self.glusterip_list
            put_in_queue = True
            for workpool_id, task_id in self.workpool_workid_dict.items():
                if task_id == dict['id']:
                    #  For immediate execution of the task, to determine whether there is
                    #  the same task being performed, if any, Put_in_queue will be set to
                    #  False, do not put it into the task waiting queue
                    put_in_queue = False
            if dict['id'] in self.queue_task_list:
                #  For immediate execution of the task, to determine whether there is
                #  waiting for the same task, if any, will put_in_queue set to False,
                #  do not put it into the task waiting queue
                put_in_queue = False
            if put_in_queue:
                self.queue_task_list.append(dict['id'])
                self.q.put([str(dict), 2], block=True, timeout=None)
                send_server(self.message, self.log, 'state', id=dict['id'], state='waiting')
            else:
                self.log.logger.warning('%s %s is in doing or in queue' % (dict['id'], dict['name']))

    def addtask(self, data, do_type):
        """
        The singlgtask class to put tasks on the job queue at regular intervals
        """
        dict = data['data']
        ms = dict['id']
        #  If the client has the same task, it returns
        if self.task_dict.has_key(ms):
            self.log.logger.warning('the work %s is in client' % ms)
            send_server(self.message, self.log, 'state', id=dict['id'], state='waiting')
            return
        dict['op'] = data['type']
        self.log.logger.debug('create a new %s backup work,the id of it is %s' % (do_type, ms))
        new_task = SingleTask(ms, self.scheduler, dict, self.task_schedul.client.backup_and_dump_queue,
                              self.glusterip_list, self.log, self.queue_task_list, self.workpool_workid_dict)
        new_task.start(do_type)
        self.task_dict[ms] = new_task
        self.task_sum = self.task_sum + 1
        send_server(self.message, self.log, 'state', id=dict['id'], state='waiting')


class Update:
    """
    Update the task
    """

    def __init__(self, log, task_dict, glusterip_list, q, message, task_schedul, scheduler, queue_task_list,
                 workpool_workid_dict):
        self.q = q
        self.glusterip_list = glusterip_list
        self.log = log
        self.task_dict = task_dict
        self.message = message
        self.task_sum = task_schedul.task_sum
        self.scheduler = scheduler
        self.task_schedul = task_schedul
        self.queue_task_list = queue_task_list
        self.workpool_workid_dict = workpool_workid_dict

    def __call__(self, message_dict):
        """
        First delete the old task in the client, save the latest task
        """
        dict = message_dict['data']
        self.log.logger.info('update a work,the id of it is %s' % dict['id'])
        ms = dict['id']
        if self.task_dict.has_key(ms):
            try:
                self.task_dict[ms].do_remove_job()
                del self.task_dict[ms]
                self.task_sum = self.task_sum - 1
                dict['op'] = dict['sub']
                new_task = SingleTask(ms, self.scheduler, dict, self.task_schedul.client.backup_and_dump_queue,
                                      self.glusterip_list, self.log, self.queue_task_list, self.workpool_workid_dict)
                new_task.start(dict['run_sub'])
                self.task_dict[ms] = new_task
                self.task_sum = self.task_sum + 1
            except Exception, e:
                self.log.logger.error(str(e))
        else:
            self.log.logger.error('No any work which id is %s' % ms)


class Recover:
    """
    Process recover tasks
    """

    def __init__(self, log, task_dict, glusterip_list, q, message, queue_task_list, workpool_workid_dict):
        self.q = q
        self.glusterip_list = glusterip_list
        self.log = log
        self.task_dict = task_dict
        self.message = message
        self.queue_task_list = queue_task_list
        self.workpool_workid_dict = workpool_workid_dict

    def __call__(self, message_dict):
        """
        Recovery tasks are performed immediately
        """
        dict = message_dict['data']
        if dict['run_sub'] == 'immediately':
            dict = message_dict['data']
            dict['op'] = "recover"
            dict['ip'] = self.glusterip_list
            put_in_queue = True
            for workpool_id, task_id in self.workpool_workid_dict.items():
                if task_id == dict['id']:
                    #  For immediate execution of the task, to determine whether there is
                    #  the same task being performed, if any, Put_in_queue will be set to
                    #  False, do not put it into the task waiting queue
                    put_in_queue = False
            if dict['id'] in self.queue_task_list:
                #  For immediate execution of the task, to determine whether there is
                #  waiting for the same task, if any, will put_in_queue set to False,
                #  do not put it into the task waiting queue
                put_in_queue = False
            if put_in_queue:
                self.queue_task_list.append(dict['id'])
                self.q.put([str(dict), 2], block=True, timeout=None)
                send_server(self.message, self.log, 'state', id=dict['id'], state='waiting')
            else:
                self.log.logger.warning('%s %s is in doing or in queue' % (dict['id'], dict['name']))
        else:
            self.log.logger.error('recover  must be immediately')


class Deleted:
    """
    Delete tasks and backup data
    """

    def __init__(self, log, task_dict, glusterip_list, q, message, task_schedul, queue_task_list):
        self.q = q
        self.glusterip_list = glusterip_list
        self.log = log
        self.task_dict = task_dict
        self.message = message
        self.task_sum = task_schedul.task_sum
        self.queue_task_list = queue_task_list

    def __call__(self, message_dict):
        """
        Delete the task in three cases: 1. The task was deleted; 2 task was stopped; 3 task execution host changed.
        If there is a 'deletework' field in the information of the delete operation that is issued, it indicates that
        the case is 1,need to delete the data backed up by the task.; If there is a 'changeworker' field indicating
        that the case is 3; There is no 'delete' field for Case 2
        """
        dict = message_dict['data']
        self.log.logger.info('delete a work,the id of it is %s' % dict['id'])
        ms = dict['id']
        # Determine if you need to delete the data
        if dict.has_key('deletework'):
            self.deleteAllDataOfaWork(dict['id'])
        # Delete local task
        if self.task_dict.has_key(ms):
            self.task_dict[ms].do_remove_job()
            del self.task_dict[ms]
            self.task_sum = self.task_sum - 1
        else:
            self.log.logger.error('No any work which id is %s' % ms)
        # Determine the type of task
        if dict.has_key('delete'):
            # Delete the task
            pass
        elif dict.has_key('changeworker'):
            # Modify the task execution host
            pass
        else:
            # Stop the task
            send_server(self.message, self.log, 'state', id=ms, state='stopped')

    def deleteAllDataOfaWork(self, id):
        """
        Will delete the task data required information combined into a
        dictionary, placed in the task queue, waiting for the execution
        of the worker thread
        """
        task_list = self.task_dict
        task = task_list[id]
        msg = task.st
        duration = msg.get('duration')
        vol = msg.get('destination_vol')
        dir = msg.get('destination_address')
        name = msg.get('name')
        id = msg.get('id')
        dict = {}
        dict['duration'] = duration
        dict['vol'] = vol
        dict['dir'] = dir
        dict['name'] = name
        dict['id'] = id
        dict['op'] = 'delete'
        dict['state'] = 'deleting'
        dict['ip'] = self.glusterip_list
        if duration != None or vol != None or dir != None or id != None:
            self.queue_task_list.append(dict['id'])
            self.q.put([str(dict), 2], block=True, timeout=None)

    def deleteBackupData(self):
        """
        This method is used to periodically delete data over the save cycle,
         is to directly create the Delete class and execute
        """
        task_dict = self.task_dict
        for ms in task_dict:
            task = task_dict[ms]
            msg = task.st
            duration = msg.get('duration')
            vol = msg.get('destination_vol')
            dir = msg.get('destination_address')
            name = msg.get('name')
            id = msg.get('id')
            dict = {}
            dict['duration'] = duration
            dict['vol'] = vol
            dict['dir'] = dir
            dict['name'] = name
            dict['id'] = id
            dict['op'] = 'delete'
            dict['state'] = 'deleting'
            dict['ip'] = self.glusterip_list
            if duration != None or vol != None or dir != None:
                t = Delete(self.log, duration=duration, vol=vol, dir=dir, ip=self.glusterip_list, name=name, id=id)
                t.start()


class Dump:
    """
    Process dump tasks
    """

    def __init__(self, log, task_dict, glusterip_list, q, message, task_schedul, scheduler, queue_task_list,
                 workpool_workid_dict):
        self.q = q
        self.glusterip_list = glusterip_list
        self.log = log
        self.task_dict = task_dict
        self.message = message
        self.task_sum = task_schedul.task_sum
        self.scheduler = scheduler
        self.task_schedul = task_schedul
        self.queue_task_list = queue_task_list
        self.workpool_workid_dict = workpool_workid_dict

    def __call__(self, message_dict):
        """
        For non-immediate implementation of the task, to create a singlgtask class, to put the task
        on time to the appropriate work queue, waiting for the execution of the worker thread. 'Cron'
        is a periodic task, 'date' is a one-time task. 'Date' and 'immediately' the difference is
        'date' to set the execution time, and 'immediately' do not have to, immediately after receiving
        the implementation.

        For immediate execution of the task, put it directly to the appropriate work queue, wait
        Sfor the worker thread to execute it

       """
        dict = message_dict['data']
        if dict['run_sub'] == 'cron':
            self.addtask(message_dict, 'cron')
        elif dict['run_sub'] == 'date':
            self.addtask(message_dict, 'date')
        elif dict['run_sub'] == 'immediately':
            dict = message_dict['data']
            dict['op'] = "dump"
            dict['ip'] = self.glusterip_list
            put_in_queue = True
            for workpool_id, task_id in self.workpool_workid_dict.items():
                if task_id == dict['id']:
                    #  For immediate execution of the task, to determine whether there is
                    #  the same task being performed, if any, Put_in_queue will be set to
                    #  False, do not put it into the task waiting queue
                    put_in_queue = False
            if dict['id'] in self.queue_task_list:
                #  For immediate execution of the task, to determine whether there is
                #  waiting for the same task, if any, will put_in_queue set to False,
                #  do not put it into the task waiting queue
                put_in_queue = False
            if put_in_queue:
                self.queue_task_list.append(dict['id'])
                self.q.put([str(dict), 2], block=True, timeout=None)
                send_server(self.message, self.log, 'state', id=dict['id'], state='waiting')
            else:
                self.log.logger.warning('%s %s is in doing or in queue' % (dict['id'], dict['name']))

    def addtask(self, data, do_type):
        """
        The singlgtask class to put tasks on the job queue at regular intervals
        """
        dict = data['data']
        ms = dict['id']
        #  If the client has the same task, it returns
        if self.task_dict.has_key(ms):
            self.log.logger.warning('the work %s is in client' % ms)
            send_server(self.message, self.log, 'state', id=dict['id'], state='waiting')
            return
        dict['op'] = data['type']
        self.log.logger.debug('create a new %s dump work,the id of it is %s' % (do_type, ms))
        new_task = SingleTask(ms, self.scheduler, dict, self.task_schedul.client.backup_and_dump_queue,
                              self.glusterip_list, self.log, self.queue_task_list, self.workpool_workid_dict)
        new_task.start(do_type)
        self.task_dict[ms] = new_task
        self.task_sum = self.task_sum + 1
        send_server(self.message, self.log, 'state', id=dict['id'], state='waiting')


class KeepaliveReceiver:
    """
    Received the heartbeat message, post back their own ip, hostname, version, group
    """

    def __init__(self, log, message, clientip, hostname, version, group, keepalive_sender):
        self.log = log
        self.message = message
        self.clientip = clientip
        self.hostname = hostname
        self.version = version
        self.group = group
        self.keepalive_sender = keepalive_sender

    def __call__(self, message_dict):
        dict = {}
        dict['clientip'] = self.clientip
        dict['hostname'] = self.hostname
        dict['version'] = self.version
        dict['group'] = self.group
        self.keepalive_sender.con.acquire()
        self.keepalive_sender.queue.put_nowait(dict)
        self.keepalive_sender.con.notify()
        self.keepalive_sender.con.release()


class Pause:
    """
    Stop the current task execution, does not affect the follow-up of scheduled execution
    """

    def __init__(self, log, tp, workpool_workid_dict):
        self.log = log
        self.tp = tp
        self.workpool_workid_dict = workpool_workid_dict

    def __call__(self, message_dict):
        dict = message_dict['data']
        ms = dict['id']
        # Traverse the ongoing work queue, find the task, and stop the current implementation
        for t in self.tp:
            if self.workpool_workid_dict.has_key(t.name):
                if self.workpool_workid_dict[t.name] == ms:
                    try:
                        if dict.has_key('do_not_return'):
                            t.stopwork(False)

                        else:
                            t.stopwork()
                    except Exception as e:
                        self.log.logger.error(e.message)
                    break


class Pauseall:
    """
    When the client is stopped, stop all ongoing tasks
    """

    def __init__(self, log, tp, workpool_workid_dict, client, task_schedul):
        self.log = log
        self.tp = tp
        self.workpool_workid_dict = workpool_workid_dict
        self.client = client
        self.task_schedul = task_schedul

    def __call__(self, message_dict):
        self.task_schedul.client_stop = True
        self.client.backup_and_dump_queue.queue.clear()
        self.client.recover_and_workimmediately_queue.queue.clear()
        self.pauseall()
        self.log.logger.info('pause all work')
        while len(self.workpool_workid_dict) != 0:
            time.sleep(1)
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
    """
    After the client starts, the server receives the return, and promised to log
    """

    def __init__(self, log):
        self.log = log

    def __call__(self, message_dict):
        data = message_dict.get('data')
        if data:
            self.log.logger.error(data)


class Task_Schedul:
    """
    According to the instructions issued by the server scheduling tasks
    """

    def __init__(self, client):
        self.q = client.recover_and_workimmediately_queue
        self.glusterip_list = client.glusterip_list
        self.log = client.log
        self.message = client.message
        self.command_dict = {}
        self.task_dict = {}
        self.tp = client.tp
        self.workpool_workid_dict = client.workpool_workid_dict
        self.queue_task_list = client.queue_task_list
        self.client = client
        self.ip = client.ip
        self.hostname = client.hostname
        self.version = client.version
        self.group = client.group
        self.keepalive_sender = client.keepalive_sender
        self.task_sum = 0
        self.scheduler = BackgroundScheduler()
        self.client_stop = False
        self.command_initialization()

    def periodic_deletion(self):
        """
        Periodically delete outdated backup data
        """
        ret = self.scheduler.add_job(self.command_dict['delete'].deleteBackupData, 'cron', hour='0', minute='0',
                                     second='0')
        self.scheduler.start()

    def command_initialization(self):
        """
        Function registration
        """
        backup = Backup(self.log, self.task_dict, self.glusterip_list, self.q, self.message, self, self.scheduler,
                        self.queue_task_list, self.workpool_workid_dict)
        update = Update(self.log, self.task_dict, self.glusterip_list, self.q, self.message, self, self.scheduler,
                        self.queue_task_list, self.workpool_workid_dict)
        recover = Recover(self.log, self.task_dict, self.glusterip_list, self.q, self.message, self.queue_task_list,
                          self.workpool_workid_dict)
        delete = Deleted(self.log, self.task_dict, self.glusterip_list, self.q, self.message, self,
                         self.queue_task_list)
        dump = Dump(self.log, self.task_dict, self.glusterip_list, self.q, self.message, self, self.scheduler,
                    self.queue_task_list, self.workpool_workid_dict)
        keepalive_receiver = KeepaliveReceiver(self.log, self.message, self.ip, self.hostname, self.version, self.group,
                                              self.keepalive_sender)
        pause = Pause(self.log, self.tp, self.workpool_workid_dict)
        pauseall = Pauseall(self.log, self.tp, self.workpool_workid_dict, self.client, self)
        first = First(self.log)
        self.command_dict['backup'] = backup
        self.command_dict['update'] = update
        self.command_dict['recover'] = recover
        self.command_dict['delete'] = delete
        self.command_dict['dump'] = dump
        self.command_dict['keepalive'] = keepalive_receiver
        self.command_dict['pause'] = pause
        self.command_dict['pauseall'] = pauseall
        self.command_dict['start'] = first
        self.periodic_deletion()

    def schedul_task(self, message_dict):
        type = message_dict.get('type')
        if not type:
            self.log.logger.error('the message %s is incomplete')
            return
        else:
            if not self.client_stop:
                self.command_dict[type](message_dict)


class KeepaliveSender(threading.Thread):
    def __init__(self, queue, log):
        self.log = log
        threading.Thread.__init__(self)
        self.message = Message("tcp", self.log)
        self.queue = queue
        self.con = threading.Condition()

    def run(self):
        while True:
            if self.con.acquire():
                if not self.queue.empty():
                    dict = self.queue.get_nowait()
                    self.con.release()
                    send_server(self.message, self.log, 'keepalive', ip=dict.get('clientip'),
                                hostname=dict.get('hostname'),
                                version=dict.get('version'),
                                group=dict.get('group'))
                else:
                    self.con.wait(1)
                    self.con.release()
                    # time.sleep(1)


class Listen(threading.Thread):
    def __init__(self, message, log, task_schedul):
        threading.Thread.__init__(self)
        self.message = message
        self.log = log
        self.task_schedul = task_schedul

    def run(self):  # listen msg from clien
        self.log.logger.debug('Listen   start')
        while True:
            if self.message.con.acquire():
                if not self.message.q.empty():
                    msg = self.message.get_queue()
                    self.message.con.release()
                    message_dict = []
                    try:
                        msg_list = msg.split("}{")
                        if len(msg_list) == 1:
                            message_dict = eval(msg)
                            self.log.logger.debug(message_dict)
                        elif len(msg_list) > 1:
                            for i in range(len(msg_list)):
                                if i == 0:
                                    msg_list[i] = msg_list[i] + "}"
                                else:
                                    msg_list[i] = "{" + msg_list[i]
                            for msg_data_inlist in msg_list:
                                message_dict = eval(msg_data_inlist)
                                self.log.logger.debug(message_dict)
                    except Exception as e:
                        self.log.logger.error(e.message)
                        continue
                    self.task_schedul.schedul_task(message_dict)
                else:
                    self.message.con.wait(1)
                    self.message.con.release()
                    # time.sleep(1)


class Daemon:
    def __init__(self, pidfile, mylogger, version, stdin='/dev/stderr', stdout='/dev/stderr',
                 stderr='/dev/stderr'):
        cp = ConfigParser.ConfigParser()
        cp.read('/etc/fbmp/client.conf')
        self.log = mylogger
        self.message = Message("tcp", self.log)
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.timer_interval = int(cp.get('client', 'timer_interval'))
        self.qdpth = int(cp.get('client', 'queue_depth'))
        # print "pid file:",self.pidfile
        self.timer_id = 0
        self.workpool_size = int(cp.get('client', 'workpool_size'))  # 线程池大小

        self.immediate_workpool_size = int(cp.get('client', 'immediate_workpool_size'))
        self.version = version
        self.group = cp.get('client', 'group')
        self.client_port = cp.get('client', 'client_port')
        self.info_l = ""
        self.glusterip_list = cp.get('client', 'gluster_ip').split()
        self.work_dir = cp.get('client', 'work_dir')
        self.task_list = {}
        self.work_list = []
        self.tp = []
        self.hostname = str(socket.gethostname())
        self.ip = socket.gethostbyname(self.hostname)
        self.workpool_workid_dict = {}

    def _daemonize(self):
        try:
            pid = os.fork()  # 第一次fork，生成子进程，脱离父进程
            if pid > 0:
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

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        # 检查pid文件是否存在以探测是否存在进程

        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            if os.path.exists('/proc/%s' % pid):
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
        data = "{'type':'pauseall'}"
        addr = (self.ip, int(self.client_port))
        info = {}
        info['data'] = data
        info['addr'] = addr
        self.message.issued(info)
        while True:
            try:
                pf = file(self.pidfile, 'r')
                pid = int(pf.read().strip())
                pf.close()
            except IOError:
                pid = None
            if pid:
                if os.path.exists('/proc/%s' % pid):
                    time.sleep(1)
                else:
                    self.log.logger.info('clinet stop success')
                    break
            else:
                message = 'pidfile %s does not exist.' % (self.pidfile)
                self.log.logger.error('pidfile %s does not exist.' % (self.pidfile))
                print message
                sys.exit(1)

    def stopclient(self):
        # 从pid文件中获取pid
        try:
            # self.message.closeall()
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = 'pidfile %s does not exist. Daemon not running!\n' % (self.pidfile)
            self.log.logger.error('pidfile %s does not exist. Daemon not running!\n' % (self.pidfile))
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

    def _timer_func(self):
        """
        Regularly detect whether the sub-thread survival, if dead, then restart
        """
        self.timer_id = self.timer_id + 1
        if self.listen.isAlive():
            pass
        else:
            self.log.logger.warning('listen thread is dead ,restart it now')
            self.listen = Listen(self.message, self.log, self.task_schedul)
            self.listen.setDaemon(True)
            self.listen.start()

        if self.keepalive_sender.isAlive():
            pass
        else:
            self.log.logger.warning('keepalivesender thread is dead ,restart it now')
            self.keepalive_sender = KeepaliveSender(self.keepalive_sender_queue, self.log)
            self.keepalive_sender.setDaemon(True)
            self.keepalive_sender.start()

        for t in self.tp:
            if t.isAlive():
                continue
            self.log.logger.warning('there is a workpool is dead,restart it now')
            thread_number = t.getName()
            self.tp.remove(t)
            if int(thread_number) <= self.workpool_size:
                newthread = WorkerPool(self.backup_and_dump_queue, t.getName(), self.workpool_size,
                                       self.workpool_workid_dict, self.log, self.queue_task_list)
            else:
                newthread = WorkerPool(self.recover_and_workimmediately_queue, t.getName(), self.workpool_size,
                                       self.workpool_workid_dict, self.log, self.queue_task_list)
            self.tp.append(newthread)
            newthread.setDaemon(True)
            newthread.start()

        self.t = Timer(self.timer_interval, self._timer_func)
        self.t.start()

    def check_gluster(self):
        """
        Judge gluseter cluster can connect
        """
        ret = -1
        for gluster_ip in self.glusterip_list:
            cmd = 'ping -c 3 %s' % gluster_ip
            ret, out = commands.getstatusoutput(cmd)
            if ret == 0:
                return ret
            self.log.logger.warning('Can not connect ip %s' % gluster_ip)
        return ret

    def check_server(self):
        """
        Judge whether the server can connect
        """
        ret = -1
        cmd = 'ping -c 3 %s' % self.message.send_ip
        ret, out = commands.getstatusoutput(cmd)
        if ret == 0:
            return ret
        self.log.logger.error('Can not connect ip %s' % self.message.send_ip)
        return ret

    def umount_dir(self):
        """
        Start the client, the working directory will be fully unmounted,
         to prevent the client before the abnormal closure of the impact
        """
        fp = open('/proc/mounts', 'r')
        lines = fp.readlines()
        for line in lines:
            list = line.split()
            try:
                dir = list[1]
                leng = len(self.work_dir)
                if leng >= 1:
                    if dir[0:leng] == self.work_dir:
                        cmd = 'umount %s' % dir
                        ret, out = commands.getstatusoutput(cmd)
                        if ret != 0:
                            self.log.logger.error('umount work_dir failed %s' % out)
            except Exception, e:
                print e
                self.log.logger.error(e)
                self.stopclient()

    def check_listen(self):
        """
        When starting the client, first close the listening port,
        and then open, to prevent the client before the abnormal
        closure of the impact
        """
        try:
            while 1:
                time.sleep(0.1)
                pid = os.popen("netstat -anp|grep %s |awk '{print $7}'" % self.client_port).read().split('/')[0]
                os.popen('kill -9 {0}'.format(int(pid)))
                self.log.logger.debug('stop a listen process')
        except:
            pass
        self.log.logger.debug('now client port is available')

    def _run(self):
        """
        Initialize the environment, start each sub-thread
        """
        self.check_listen()
        self.umount_dir()
        ret = self.check_gluster()
        if ret != 0:
            message = 'Error,can not connect gluster cluster'
            self.log.logger.error(message)
            sys.stderr.write(message)
            self.stopclient()
        now = datetime.now()
        self.hostname = socket.gethostname()
        os.system("ulimit -n " + "65535")
        self.log.logger.debug("To start  listen:")
        try:
            ret = self.message.start_server()
            if ret != 0:
                sys.stderr.write('client message start error\n')
                self.log.logger.error('client message start error')
                self.stopclient()
        except:
            sys.stderr.write('client message start error\n')
            self.log.logger.error('client message start error')
            self.stopclient()
        ret = self.check_server()
        if ret != 0:
            message = 'Error,can not connect server '
            self.log.logger.error(message)
            sys.stderr.write(message)
            self.stopclient()
        self.log.logger.debug("to start timer:")
        self.t = Timer(self.timer_interval, self._timer_func)
        self.log.logger.debug('run job scheduler')
        self.log.logger.debug("To start threading pool:")
        self.backup_and_dump_queue = Queue.Queue(self.qdpth)
        self.recover_and_workimmediately_queue = Queue.Queue(self.qdpth)
        self.keepalive_sender_queue = Queue.Queue()
        self.queue_task_list = []
        # Start the worker thread pool
        for i in range(self.workpool_size):
            t = WorkerPool(self.backup_and_dump_queue, i, self.workpool_size, self.workpool_workid_dict, self.log,
                           self.queue_task_list)
            self.tp.append(t)
        for i in range(self.workpool_size, self.workpool_size + self.immediate_workpool_size):
            t = WorkerPool(self.recover_and_workimmediately_queue, i, self.workpool_size, self.workpool_workid_dict,
                           self.log, self.queue_task_list)
            self.tp.append(t)
        for t in self.tp:
            t.setDaemon(True)
            t.start()
        self.keepalive_sender = KeepaliveSender(self.keepalive_sender_queue, self.log)
        self.keepalive_sender.setDaemon(True)
        self.keepalive_sender.start()
        self.task_schedul = Task_Schedul(self)
        self.listen = Listen(self.message, self.log, self.task_schedul)
        self.listen.setDaemon(True)
        self.listen.start()
        send_server(self.message, self.log, 'initialize', ip=self.ip, hostname=self.hostname, version=self.version,
                    group=self.group)
        self.t.start()
        self.log.logger.debug("start threadpool over")
        self.log.logger.info("backup work start in backend!")
