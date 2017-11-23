#!/usr/bin/env python
#coding:utf-8
import threading
from datetime import *
import time
from work import Work
from message import Message




class WorkerPool(threading.Thread):
    def __init__(self, workq, i,n ,cip,log):
        # self.logger = logging.getLogger(__name__)
        threading.Thread.__init__(self)
        self.log = log
        ms = Message("tcp")
        self.message=ms
        self.queue = workq
        self.thread_stop = False
       # print "tp to init ", i
        #  self.logger.debug('tp to init: ' + str(i))
        self.work_id = 0
        self.name = str(i)
        self.threadID = i
        self.allcron=n
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
        #print "jsonDicts is:", dicts
        self.log.logger.debug('jsonDicts is:' + str(dicts))
        return dicts

    """
    当读写操作失败时的错误处理流程，暂时未添加

    """

    def get_threadID(self):
        return  self.threadID


    """

    主要工作者线程池实例
    1、work_id 单调递增
    2、
    """

    def send_ta(self,id,value):
        data="{'type':'state','data':{'id':'%s','state':'%s'}}"%(id,value)
        ret=self.message.send(data)
        if ret!=0:
            self.log.logger.error('message send failed %s'%ret)


    def run(self):

        if not self.confip:
            return 1
        now = datetime.now()
        while not self.thread_stop:  # do forever
            time.sleep(1)
            self.work_id = self.work_id + 1
            if self.queue.empty():
                continue
            if not self.queue.empty():
                try:

                    task = self.queue.get(block=True, timeout=20)  # 接收消息

                except:
                    #print "get queue timerout!!!!!!!!!!!!"
                    self.log.logger.error("get queue timerout!!!!!!!!!!!!")
                    continue

            #print "task recv:%s ,task No:%d" % (task[0], task[1])
            self.log.logger.info("task recv:%s ,task No:%d" % (task[0], task[1]))

            """
            获取的数据是通过http格式拿到的json 格式数据，通过转换为dicts 后进行处理
            打桩测试的数据也已经转换为json 格式的本地文本
            """
            if True:
                task_d = eval(task[0])
                #print "bay bay", task
                #print "task_d is:", task_d
                self.arglist = self.jsonDicts(task_d)
            if self.arglist is None:
                continue
            ret = 0
            """
            建立工作实例，Work 类提供了对glusterfs 的各种操作，此时开始进行读写等操作
            """
            self.arglist['confip'] = self.confip
            self.arglist['threadId'] = self.name
            if self.name>=self.allcron and self.arglist['state']=='stoped':
                self.send_ta(self.arglist['id'],'running_s')
            else:
                self.send_ta(self.arglist['id'], 'running_w')
            self.work = Work(self.arglist, self.log)

            if not self.work:
                self.log.logger.error('work create failed %s'% (self.threadID))
            
            self.log.logger.info('todo work:%s' % (self.threadID))
            ret = self.work.start()
            self.queue.task_done()  # 完成一个任务
            if self.arglist['op'] == 'backup':
                if self.name>=self.allcron and self.arglist['state']=='stoped':
                    self.send_ta(self.arglist['id'],'stopped')
                else:
                    self.send_ta(self.arglist['id'], 'waiting')
            else:
                self.send_ta(self.arglist['id'], 'end')
            res = self.queue.qsize()  # 判断消息队列大小
            if res > 0:
                #print("ahua!There are still %d tasks to do" % (res))
                self.log.logger.warning("There are still %d tasks to do" % (res))
