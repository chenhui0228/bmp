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


class Daemon:
    def __init__( self, pidfile, Message, glusterip="", confip="", stdin='/dev/stderr', stdout='/dev/stderr',
                  stderr='/dev/stderr' ):
        # self.logger = logging.getLogger(__name__)

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
        self.tp_size = 1  # 线程池大小
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
                # self.logger.info("backup work start in backend!")
                sys.exit(0)  # 退出主进程
        except OSError, e:
            sys.stderr.write('fork #1 failed: %d (%s)\n' %
                             (e.errno, e.strerror))
            # self.logger.error('fork #1 failed: %d (%s)\n' %
            #                  (e.errno, e.strerror))
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
            # self.logger.error('fork #2 failed: %d (%s)\n' %
            #                  (e.errno, e.strerror))
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
        # self.logger.debug("pid file write succeed")

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
            # self.logger.error(
            #    'pidfile %s already exist. Daemon already running!\n' % self.pidfile)
            sys.stderr.write(message % self.pidfile)
            sys.stderr.flush()
            sys.exit(1)

            # 启动监控

        # self._daemonize()
        self._run()

    def stop( self ):
        # 从pid文件中获取pid

        try:
            self.message.closeall()
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:  # 重启不报错
            message = 'pidfile %s does not exist. Daemon not running!\n'
            # self.logger.error(
            #     'pidfile %s does not exist. Daemon not running!\n' % (self.pidfile))
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
                print str(err)
                sys.exit(1)

    def restart( self ):
        self.stop()
        self.start()

    def listen( self ):
        while True:
            if not self.message.q.empty():
                msg = self.message.get_queue()
                print msg
                msg_data = msg.split(":", 1)[1]
                print msg_data
                date = eval(msg_data)
                self.schd_task(date)
                time.sleep(2)

    def _timer_func( self ):
        # print "timer running at:",datetime.now()
        # get json file
        # check json if need to backup


        self.timer_id = self.timer_id + 1

        """
        没过5秒判断一次线程是否挂了，如果挂了需要重新启动线程加入到threadpool中
        """
        if self.listen_thread.isAlive():
            pass
        else:
            self.listen_thread = threading.Thread(target=self.listen)
            self.listen_thread.setDaemon(True)
            self.listen_thread.start()

        for t in self.tp:
            if t.isAlive():
                continue
            self.tp.remove(t)

            # self.logger.warning(
            #   "thread id %s is dead, going to restart!!!" % (t.getName()))
            newthread = WorkerPool(self.q, t.getName(), self.confip)
            self.tp.append(newthread)
            newthread.setDaemon(True)
            newthread.start()

        # update scheduler job
        self.t = Timer(self.timer_interval, self._timer_func)
        self.t.start()
        # cur_t = time.strftime("%H:%M:%S")
        # if cur_t == "00:00:00":
        #   self.do_reset_job_timer("date")

    """
      读取到的所有的配置信息以task 为单位，用list 存储，
      如果最大task_id 没变，说明没有新的任务产生
      如果max_task_sum 变化，说明肯定有任务增减

    """

    def do_now( self, data ):
        pass

    def schd_task( self, data ):
        if data['type'] == 'backup':  # 创建新任务
            if data['op_code'] == 'direct':
                print "do backup use direct"
                pass
            elif data['op_code'] == 'queue':
                print "do backup use queue"
                dict = data['data']
                ms = dict['uuid']
                new_task = SingleTask(ms, self.scheduler, dict, self.q, self.glusterlist, self.confip)
                new_task.start()
                self.task_list[ms] = new_task
                self.task_sum = self.task_sum + 1
                pass
        elif data['type'] == 'revise':
            print "do revise"
            dict = data['data']
            ms = dict['uuid']
            self.task_list[ms].updateconf(dict)
        elif data['type'] == 'recover':  # 恢复备份文件
            print "do recover"
            pass
        elif data['type'] == 'suspend':  # 暂停
            print "do suspend"
            dict = data['data']
            ms = dict['uuid']
            self.task_list[ms].add_suspendlist(ms)
        elif data['type'] == 'delete':  # 删除任务
            print "do delete"
            dict = data['data']
            ms = dict['uuid']
            self.task_list[ms].do_remove_job()
            del self.task_list[ms]
            self.task_sum = self.task_sum - 1
        elif data['type'] == 'restart':  # 重启备份任务
            print "do restart"
            dict = data['data']
            ms = dict['uuid']
            self.task_list[ms].del_suspendlist(ms)
        elif data['type'] == 'dump':  # 准备dump
            print "do dump"
            pass
        elif data['type'] == 'update':
            oneline = data['data']
            if oneline['sub'] == 'log':
                print "dp update log"
                pass
            elif oneline['sub'] == 'progress':
                print "do update progress"
                pass
            elif oneline['sub'] == 'alarm':
                print "do update alarm"
                pass
            elif oneline['sub'] == 'result':
                print "do update result"
                pass
            elif oneline['sub'] == 'state':
                print "do update state"
                pass
            elif oneline['sub'] == 'gluster_config':
                print "do update gluster_config"
                self.glusterlist = oneline['gluster_config']
        elif data['type'] == 'initialize':  # 初始化
            print "do update initialze"
            pass

    """
    守护进程主体：
    启动timer，此timer 主要更新备份周期的功能

    """

    def _run( self ):
        fp = open('/zyt/test', 'a')
        fp.write('_run')
        fp.close()
        """ run your fun"""
        # self.logger.info("****run backup service***")
        # global sock_info
        now = datetime.now()
        # sys config:
        self.hostname = socket.gethostname()
        # self.local_ip = socket.gethostbyname(self.hostname)
        print "run in :", self.hostname
        # self.logger.info("run in:%s" % (self.hostname))
        os.system("ulimit -n " + "65535")
        # start timer:
        print "to start timer:"
        # self.logger.debug("to start timer:")
        self.t = Timer(self.timer_interval, self._timer_func)
        # self.t.start()
        # sock_info['start_time'] = str(now)
        print "load config info"
        # self.logger.debug("load config info")
        log = logging.getLogger('apscheduler.executors.default')
        log.setLevel(logging.INFO)  # DEBUG
        fmt = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        h = logging.StreamHandler()
        h.setFormatter(fmt)
        log.addHandler(h)
        print " run job scheduler"
        # self.logger.debug('run job scheduler')
        self.scheduler = BackgroundScheduler()
        # threading pool init:

        print "to start tp:"
        #  self.logger.debug("To start threading pool:")
        self.q = Queue.Queue(self.qdpth)
        self.tp = []
        for i in range(self.tp_size):
            t = WorkerPool(self.q, i, self.confip)
            self.tp.append(t)
        for t in self.tp:
            t.setDaemon(True)
            t.start()
        self.listen_thread = threading.Thread(target=self.listen)
        self.listen_thread.setDaemon(True)
        self.listen_thread.start()
        self.t.start()

        self.scheduler.start()
        # self.dump_status()
        print "start threadpool over"
        # self.logger.debug("start threadpool over")
        # while True:
        #    pass
        # except (KeyboardInterrupt, SystemExit):
        """
        """
