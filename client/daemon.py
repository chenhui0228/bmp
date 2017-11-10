#!/usr/bin/env python
# coding:utf-8
from SocketServer import BaseRequestHandler, ThreadingTCPServer, ThreadingUDPServer
from message import Message, Performance
import socket  # 套接字
from gluster import gfapi
import sys
import os
import atexit
import errno
from os.path import join, getsize, isfile
from signal import SIGTERM
import urllib2
import httplib, urllib  # 加载模块
import BaseHTTPServer
from SocketServer import ThreadingMixIn
import threading
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urlparse
from multiprocessing.pool import ThreadPool as Pool
from threading import Timer
from datetime import *
import time
import Queue
import types
import json
import socket
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import math
import logging.handlers as handlers
from message import Message
from singletask import SingleTask
from workerpool import WorkerPool
from work import Work



class Daemon:
    def __init__( self, pidfile,  mylogger, glusterip="", confip="", stdin='/dev/stderr', stdout='/dev/stderr',
                  stderr='/dev/stderr' ):
        # self.logger = logging.getLogger(__name__)
        self.log=mylogger
        self.message = Message
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.await = 2
        self.timer_interval = 2
        self.qdpth = 50
        # print "pid file:",self.pidfile
        self.timer_id = 0
        self.json_f = "/data/work/test.json"
        self.q = ""
        self.tp_size = 5 # 线程池大小
        self.reload_interval = 30
        self.info_l = ""
        self.glusterlist = ['10.202.125.83']
        self.confip = '10.202.125.83:80'
        self.max_task_id = 0  # 当前最大任务id
        self.task_sum = 0  # 当前最大任务数
        # 本机IP
        self.local_ip = ""
        self.task_list = {}
        self.do_list = {}
        self.worktable_id = 0
        self.statetable_id = ""
        self.tp = []
        # self.conn=pymysql.connect(host='10.202.125.82',port= 3306,user = 'mysqltest',passwd='sf123456',db='mysqltest')

    def _daemonize( self ):

        try:
            pid = os.fork()  # 第一次fork，生成子进程，脱离父进程
            if pid > 0:
                print "backup work start in backend!"
                self.log.logger.info("backup work start in backend!")
                sys.exit(0)  # 退出主进程
        except OSError, e:
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
        except OSError, e:
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
            message = 'pidfile %s already exist. Daemon already running!\n'
            self.log.logger.error('pidfile %s already exist. Daemon already running!\n' % self.pidfile)
            sys.stderr.write(message % self.pidfile)
            sys.stderr.flush()
            sys.exit(1)

            # 启动监控
        self.log.logger.info('client start now')
        self._daemonize()
        self._run()

    def stop( self ):
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
        except OSError, err:
            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                #print str(err)
                sys.exit(1)

    def restart( self ):
        self.stop()
        self.start()

    def listen( self ):
        while True:
            if not self.message.q.empty():
                msg = self.message.get_queue()
                #print msg
                msg_data = msg.split(":", 1)[1]
                #print msg_data
                self.log.logger.info("get msg is that %s"%msg_data)
                date = eval(msg_data)
                self.schd_task(date)
            time.sleep(1)

    def send(self,sub,id,value):
        data="{'type':'update','data':{'sub':'%s','id':'%s','%s':'%s'}}"%(sub,id,sub,value)
        ret=self.message.send(data)
        if ret!=0:
            self.log.logger.error(ret)


    def _timer_func( self ):
        # print "timer running at:",datetime.now()
        self.timer_id = self.timer_id + 1
        """
        没过5秒判断一次线程是否挂了，如果挂了需要重新启动线程加入到threadpool中
        """
        if self.listen_thread.isAlive():
            pass
        else:
            self.log.logger.warning('listen thread is dead ,restart it now')
            self.listen_thread = threading.Thread(target=self.listen)
            self.listen_thread.setDaemon(True)
            self.listen_thread.start()

        for t in self.tp:
            if t.isAlive():
                continue
            self.log.logger.warning('there is a workpool is dead,restart it now')
            self.tp.remove(t)

            # self.logger.warning(
            newthread = WorkerPool(self.q, t.getName(), self.confip,self.log)
            self.tp.append(newthread)
            newthread.setDaemon(True)
            newthread.start()

        self.t = Timer(self.timer_interval, self._timer_func)
        self.t.start()

    """
      读取到的所有的配置信息以task 为单位，用list 存储，
      如果最大task_id 没变，说明没有新的任务产生
      如果max_task_sum 变化，说明肯定有任务增减

    """

    def do_now( self, data ):
        now = datetime.now()
        dict = data['data']
        dict['wait_start'] = now.strftime('%Y-%m-%d %H:%M:%S')
        if data['type']=='backup':
            self.log.logger.info('create a new direct backup work')
            dict['op'] = "write"
        elif data['type']=='dump':
            self.log.logger.info('create a new direct dump work')
            dict['op']='dump'
        elif data['type']=='recover':
            self.log.logger.info('create a new direct recover work')
            dict['op']='recover'
        dict['ip'] = self.glusterlist
        self.qq.put([str(dict), 2], block=True, timeout=None)


    def schd_task( self, data ):
        dict = data['data']
        if data['type'] == 'backup':  # 创建新任务
            if dict['run_sub'] == 'direct':
                #print "do backup use direct"
                self.do_now(data)
            elif dict['run_sub'] == 'queue':
                #print "do backup use queue"
                dict['op'] = "write"
                dict['op_code'] = 'direct'
                ms = dict['id']
                self.log.logger.info('create a new queue backup work,the id of it is %s' %ms)
                new_task = SingleTask(ms, self.scheduler, dict, self.q, self.glusterlist, self.confip,self.log)
                new_task.start()
                self.task_list[ms] = new_task
                self.task_sum = self.task_sum + 1
                pass
        elif data['type'] == 'revise':
            print "do revise"
            self.log.logger.info('change a work,the id of it is %s'%dict['id'])
            ms = dict['id']
            if self.task_list.has_key(ms):
                self.task_list[ms].updateconf(dict)
            else:
                self.log.logger.error('No any work which id is %s' % ms)
                self.send('alarm',ms,'No any work which id is %s' % ms)

        elif data['type'] == 'recover':  # 恢复备份文件
            print "do recover"
            self.do_now(data)
            pass
        elif data['type'] == 'suspend':  # 暂停
            #print "do suspend"
            self.log.logger.info('suspend a work,the id of it is %s' % dict['id'])
            ms = dict['id']
            if self.task_list.has_key(ms):
                self.task_list[ms].add_suspendlist(ms)
            else:
                self.log.logger.error('No any work which id is %s' % ms)
                self.send('alarm',ms,'No any work which id is %s' % ms)
        elif data['type'] == 'delete':  # 删除任务
            #print "do delete"
            self.log.logger.info('delete a work,the id of it is %s' % dict['id'])
            ms = dict['id']
            if self.task_list.has_key(ms):
                self.task_list[ms].do_remove_job()
                del self.task_list[ms]
                self.task_sum = self.task_sum - 1
            else:
                self.log.logger.error('No any work which id is %s'%ms)
                self.send('alarm', ms, 'No any work which id is %s' % ms)
        elif data['type'] == 'restart':  # 重启备份任务
            #print "do restart"
            self.log.logger.info('restart a work,the id of it is %s' % dict['id'])
            ms = dict['id']
            if self.task_list.has_key(ms):
                self.task_list[ms].del_suspendlist(ms)
            else:
                self.log.logger.error('No any work which id is %s' % ms)
                self.send('alarm', ms, 'No any work which id is %s' % ms)
        elif data['type'] == 'dump':  # 准备dump
            if dict['run_sub'] == 'queue':
               # print "do dump in queue"
                dict['op'] = "dump"
                ms = dict['id']
                self.log.logger.info('create a new queue dump work,the id of it is %s' % ms)
                new_task = SingleTask(ms, self.scheduler, dict, self.q, self.glusterlist, self.confip,self.log)
                new_task.start()
                self.task_list[ms] = new_task
                self.task_sum = self.task_sum +1
            elif dict['run_sub'] == 'direct':
                #print "do dump in direct"
                self.do_now(data)
        elif data['type'] == 'show':
            for onetask in self.task_list:
                print onetask
        else:
            self.log.logger.error("get some messages which is to server")

    """
    守护进程主体：
    启动timer，此timer 主要更新备份周期的功能

    """

    def _run( self ):
        """ run your fun"""
        now = datetime.now()
        self.hostname = socket.gethostname()
        #print "run in :", self.hostname
        os.system("ulimit -n " + "65535")
        # start timer:
        #print "to start timer:"
        self.log.logger.debug("to start timer:")
        self.t = Timer(self.timer_interval, self._timer_func)
        #print "load config info"
        #print " run job scheduler"
        self.log.logger.debug('run job scheduler')
        self.scheduler = BackgroundScheduler()
        #print "to start tp:"
        self.log.logger.debug("To start threading pool:")
        self.q = Queue.Queue(self.qdpth)
        self.qq=Queue.Queue()
        self.tp = []
        for i in range(self.tp_size):
            t = WorkerPool(self.q, i, self.confip,self.log)
            self.tp.append(t)
        self.drictway= WorkerPool(self.qq, 5, self.confip,self.log)
        self.tp.append(self.drictway)
        for t in self.tp:
            t.setDaemon(True)
            t.start()
        self.log.logger.debug("To start  listen:")
        self.message = Message("tcp")
        self.message.start_server()
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.setDaemon(True)
        self.listen_thread.start()
        self.t.start()

        hostname = str(socket.gethostname())
        ip = socket.gethostbyname(hostname)
        port = str(24007)
        data = "{'type': 'initialize', 'data': {'ip': '%s', 'hostname': '%s', 'port': '%s'}}" % (ip, hostname, port)
        ret=self.message.send(data)
        if ret!=0:
            self.log.logger.error(ret)

        self.scheduler.start()
        #print "start threadpool over"
        self.log.logger.debug("start threadpool over")
        """
        """
