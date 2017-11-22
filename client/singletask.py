#!/usr/bin/env python
# coding:utf-8
from datetime import *
import time
from message import Message
import uuid



class SingleTask():
    def __init__( self, name, schd, info, q, glusterip, confip,log):
        # self.logger = logging.getLogger(__name__)
        self.log = log
        ms = Message("tcp")
        self.message=ms
        self.info = info
        self.name = name
        self.sumid = 0  # 已经执行的任务次数总和
        self.lastid = 0  # 已经执行的任务次数
        self.st = info
        self.schd = schd
        self.queue = q
        self.job = ""
        self.job_create = 0
        self.gluster = glusterip
        self.police = {}
        self.st["date"] = ""
        self.confip = confip
        self.suspendlist = []



    def add_suspendlist( self, id ):
        self.suspendlist.append(id)

    def del_suspendlist( self, id ):
        if id in self.suspendlist:
            self.suspendlist.remove(id)


    def do_insert_job( self ):  # add work job
        self.lastid = self.sumid
        self.sumid = self.sumid + 1
        self.st['ip'] = self.gluster
        if not self.st['id'] in self.suspendlist:
            #print "**********************put workerpool time:", time.asctime(time.localtime(time.time())), " name is:", self.name
            self.log.logger.info(
                "put workerpool time:" + time.asctime(time.localtime(time.time())) + " name is:" + self.name)
            self.queue.put([str(self.st), 2], block=True, timeout=None)

    """
    删除任务
    """

    def do_remove_job( self ):
        if self.schd.get_job(job_id=self.name):
            self.log.logger.info(
               "Remove task from scheduling queue: %s" % (self.name))
            self.schd.remove_job(self.name)

    def getname( self ):
        return self.name

    def start( self,sub):
        # self.logger.info("Start new task now!")
        """
        如果当前时间大于开始时间：
        则应该根据备份计算出下一次备份的时间
        """
        #print "**********************set start time:", time.asctime(time.localtime(time.time())), " name is:", self.name
        if sub=='cron':
            self.log.logger.info("Set start time:" + time.asctime(time.localtime(time.time())) + " name is:" + self.name)
            cronconf = self.st['cron']
            self.job = self.schd.add_job(self.do_insert_job, 'cron', year=cronconf['year'], month=cronconf['month'],
                                     day=cronconf['day'], week=cronconf['week'], day_of_week=cronconf['day_of_week'],
                                     hour=cronconf['hour'], minute=cronconf['minute'], second=cronconf['second'],
                                     start_date=cronconf['start_date'], id=self.name)
        elif sub=='date':
            self.log.logger.info(
                "Set start time:" + time.asctime(time.localtime(time.time())) + " name is:" + self.name)
            cronconf = self.st['cron']
            if datetime.strptime(cronconf['start_date'], "%Y-%m-%d %H:%M:%S")>datetime.now():
                self.job = self.schd.add_job(self.do_insert_job, 'date', run_date=cronconf['start_date'])
            else:
                self.job = self.schd.add_job(self.do_insert_job, 'date')
