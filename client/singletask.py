#!/usr/bin/env python
# coding:utf-8
from datetime import *
import time
from message import Message



class SingleTask():
    def __init__( self, name, schd, info, q, glusterip,log,queue_task_list,workpool_workid_dict):
        # self.logger = logging.getLogger(__name__)
        self.log = log
        ms = Message("tcp",self.log)
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
        self.stop = False
        self.queue_task_list=queue_task_list
        self.workpool_workid_dict=workpool_workid_dict



    def stop_job( self):
        """
        Temporarily not used
        """
        self.stop=True

    def restart_job( self):
        """
        Temporarily not used
        """
        if self.stop:
            self.stop=False


    def do_insert_job( self ):
        """
        Add tasks to the work queue
        """
        self.lastid = self.sumid
        self.sumid = self.sumid + 1
        self.st['ip'] = self.gluster
        if not self.stop:
            #print "**********************put workerpool time:", time.asctime(time.localtime(time.time())), " name is:", self.name
            self.log.logger.info(
                "put workerpool time:" + time.asctime(time.localtime(time.time())) + " name is:" + self.name)
            try:
                put_in_queue = True
                for workpool_id, task_id in self.workpool_workid_dict.items():
                    if task_id == self.st['id']:
                        put_in_queue = False
                if self.st['id'] in self.queue_task_list:
                    put_in_queue = False
                if put_in_queue:
                    self.queue.put([str(self.st), self.sumid], block=True, timeout=7200)
                    self.queue_task_list.append(self.st['id'])
                else:
                    self.log.logger.warning('%s %s is in doing or in queue'%(self.st['id'],self.st['name']))
            except Exception as e:
                self.log.logger.error('can put work msg in workerpool queue,%s'%str(e))


    def do_remove_job( self ):
        """
        Temporarily not used
        """
        if self.schd.get_job(job_id=self.name):
            self.log.logger.info(
               "Remove task from scheduling queue: %s" % (self.name))
            self.schd.remove_job(self.name)

    def getname( self ):
        return self.name

    def start( self,sub):
        # self.logger.info("Start new task now!")
        #print "**********************set start time:", time.asctime(time.localtime(time.time())), " name is:", self.name
        if sub=='cron':
            try:
                self.log.logger.info("Set start time:" + time.asctime(time.localtime(time.time())) + " name is:" + self.name)
                cronconf = self.st['cron']
                self.job = self.schd.add_job(self.do_insert_job, 'cron', year=cronconf['year'], month=cronconf['month'],
                                     day=cronconf['day'], week=cronconf['week'], day_of_week=cronconf['day_of_week'],
                                     hour=cronconf['hour'], minute=cronconf['minute'], second=cronconf['second'],
                                     start_date=cronconf['start_date'], id=self.name)
            except Exception as e:
                self.log.logger.error(e)
        elif sub=='date':
            try:
                self.log.logger.info(
                    "Set start time:" + time.asctime(time.localtime(time.time())) + " name is:" + self.name)
                cronconf = self.st['cron']
                if datetime.strptime(cronconf['start_date'], "%Y-%m-%d %H:%M:%S")>datetime.now():
                    self.job = self.schd.add_job(self.do_insert_job, 'date', run_date=cronconf['start_date'])
                else:
                    self.job = self.schd.add_job(self.do_insert_job, 'date')
            except Exception as e:
                self.log.logger.error(e)
