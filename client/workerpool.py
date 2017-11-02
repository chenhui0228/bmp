#!/usr/bin/env python
#coding:utf-8
from SocketServer import BaseRequestHandler,ThreadingTCPServer,ThreadingUDPServer
from message import Message,Performance
import socket # 套接字
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
from work import Work




class WorkerPool(threading.Thread):
    def __init__(self, workq, i, cip):
        # self.logger = logging.getLogger(__name__)
        threading.Thread.__init__(self)
        self.queue = workq
        self.thread_stop = False
        print "tp to init ", i
        #  self.logger.debug('tp to init: ' + str(i))
        self.work_id = 0
        self.name = str(i)
        self.threadID = i
        self.confip = cip
        self.arglist = {}

    """
    将json 格式的数据转换为字典
    """

    def jsonDicts(self, params):
        # dicts = {'ip': None, 'v': None, 'dir': None, 'op': None, 'vf': None, 'pf': None}
        dicts = {}
        if len(params) == 0:
            return dicts
        # dicts['op'] = params['ip']
        for k, v in params.iteritems():
            dicts[k] = v
        print "jsonDicts is:", dicts
        #  self.logger.debug('jsonDicts is:' + str(dicts))
        return dicts

    def transDicts(self, params):
        # dicts = {'ip': None, 'v': None, 'dir': None, 'op': None, 'vf': None, 'pf': None}
        dicts = {'ip': None, 'v': None, 'dir': None, 'op': None, 'vf': None, 'pf': None, 'vfile': None, 'pfile': None,
                 'confip': None, 'duration': None, 'id2': None, 'task_id': None, 'wait_start': None}
        if len(params) == 0:
            # print "no data to dicts"
            return dicts
        params = params.split(' ')
        for param in params:
            dicts[param.split('=')[0]] = param.split('=')[1]
        print "transDicts is: ", dicts
        # self.logger.debug('tranDicts is:' + str(dicts))
        return dicts

    """
    当读写操作失败时的错误处理流程，暂时未添加

    """

    def get_task_id(self):
        if self.arglist.has_key('task_id'):
            return self.arglist['task_id']
        else:
            return -1

    def do_fail(self):
        print "new todo failed cmd!"
        # self.logger.error("new todo failed cmd!")

    """
    主要工作者线程池实例
    1、work_id 单调递增
    2、
    """

    def run(self):

        # global sock_info
        if not self.confip:
            return 1
        now = datetime.now()
        print "%s Hello wangpeng at time: %s" % (self.getName(), now)
        # self.logger.debug("%s Hello wangpeng at time: %s" %
        #                 (self.getName(), now))
        # while True:
        while not self.thread_stop:  # do forever
            time.sleep(1)
            self.work_id = self.work_id + 1
            # print("thread%d %s: waiting for tast" %(self.ident,self.name))
            # print "thread work:",self.work_id
            if self.queue.empty():
                continue
            if not self.queue.empty():
                try:

                    task = self.queue.get(block=True, timeout=20)  # 接收消息

                except:
                    print "get queue timerout!!!!!!!!!!!!"
                    # self.logger.error("get queue timerout!!!!!!!!!!!!")
                    continue
            else:
                print "error info ,to here"
                #  self.logger.error('error msg in line 872')
                # addtwodimdict(sock_info, 'threadpool', self.name, 'waiting')
                continue
            print "task recv:%s ,task No:%d" % (task[0], task[1])
            #  self.logger.info("task recv:%s ,task No:%d" % (task[0], task[1]))

            """
            获取的数据是通过http格式拿到的json 格式数据，通过转换为dicts 后进行处理
            打桩测试的数据也已经转换为json 格式的本地文本
            """
            if True:
                task_d = eval(task[0])
                print "bay bay", task
                print "task_d is:", task_d
                # self.logger.debug('bay day %s\ntask_d is %s' % (task, task_d))
                self.arglist = self.jsonDicts(task_d)
            if self.arglist is None:
                continue
            ret = 0
            """
            建立工作实例，Work 类提供了对glusterfs 的各种操作，此时开始进行读写等操作
            """

            # some confip to init:
            self.arglist['confip'] = self.confip

            # self.work = Work(arglist['op'],arglist['ip'],arglist['v'],arglist['vf'],arglist['pf'],arglist['dir'],arglist['confip'])
            self.arglist['threadId'] = self.name
            self.work = Work(self.arglist)

            if not self.work:
                return -1
            print "todo work", self.threadID
            # self.logger.info('todo work:%s' % (self.threadID))
            ret = self.work.start()
            self.queue.task_done()  # 完成一个任务
            if ret < 0:
                print "cmd failed:"
                # self.logger.error("cmd failed:")
                self.do_fail()
            res = self.queue.qsize()  # 判断消息队列大小
            if res > 0:
                print("ahua!There are still %d tasks to do" % (res))
                # self.logger.warning("There are still %d tasks to do" % (res))
