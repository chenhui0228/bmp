#!/usr/bin/env python
#coding:utf-8
import threading
from datetime import *
import time
from work import Work
from message import Message
import os
import  ConfigParser
import shutil
import  uuid


class WorkerPool(threading.Thread):
    def __init__(self, workq, i,n ,workpool_workid_dict,log,queue_task_list):
        # self.logger = logging.getLogger(__name__)
        threading.Thread.__init__(self)
        self.log = log
        ms = Message("tcp")
        self.message=ms
        self.queue = workq
        self.thread_stop = False
        self.queue_task_list=queue_task_list
       # print "tp to init ", i
        #  self.logger.debug('tp to init: ' + str(i))
        self.work_id = 0
        self.name = str(i)
        self.threadID = i
        self.allcron=n
        self.workpool_workid_dict = workpool_workid_dict
        self.arglist = {}
        self.change_tasktable=True
        if self.workpool_workid_dict.has_key(self.name):
            del self.workpool_workid_dict[self.name]

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

    def generate_uuid( dashed=True ):
        """Creates a random uuid string.
        :param dashed: Generate uuid with dashes or not
        :type dashed: bool
        :returns: string
        """
        if dashed:
            return str(uuid.uuid4())
        return uuid.uuid4().hex

    def get_threadID(self):
        return  self.threadID


    """

    主要工作者线程池实例
    1、work_id 单调递增
    2、
    """

    def send_ta(self,id,value,bk_id=None):
        data="{'type':'state','data':{'id':'%s','state':'%s','bk_id':'%s'}}"%(id,value,bk_id)
        ret=self.message.send(data)
        if ret!=0:
            self.log.logger.error('message send failed %s'%ret)


    def run(self):
        now = datetime.now()
        while not self.thread_stop:  # do forever
            time.sleep(1)
            self.work_id = self.work_id + 1
            if self.queue.empty():
                continue
            task = None
            if not self.queue.empty():
                try:

                    task = self.queue.get(block=True, timeout=20)  # 接收消息
                    self.log.logger.info("task recv:%s ,task No:%d" % (task[0], task[1]))

                except:
                    #print "get queue timerout!!!!!!!!!!!!"
                    self.log.logger.error("get queue timerout!!!!!!!!!!!!")
                    continue

            #print "task recv:%s ,task No:%d" % (task[0], task[1])


            """
            获取的数据是通过http格式拿到的json 格式数据，通过转换为dicts 后进行处理
            打桩测试的数据也已经转换为json 格式的本地文本
            """
            if task:
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
            self.log.logger.info('todo work:%s' % (self.threadID))


            self.workpool_workid_dict[self.name] = self.arglist['id']
            self.queue_task_list.remove(self.arglist['id'])
            self.arglist['threadId'] = self.name
            self.arglist['bk_id'] = self.generate_uuid()
            if self.name>=self.allcron and self.arglist['state']=='stoped':
                self.send_ta(self.arglist['id'],'running_s',self.arglist['bk_id'])
            else:
                self.send_ta(self.arglist['id'], 'running_w',self.arglist['bk_id'])
            self.work = Work(self.arglist, self.log)

            if not self.work:
                self.log.logger.error('work create failed %s'% (self.threadID))

            ret = self.work.start()
            self.queue.task_done()  # 完成一个任务
            if self.arglist['op'] == 'backup' or self.arglist['op'] == 'dump':
                if  self.arglist['state']=='stoped' or self.arglist['state']=='running_s':
                    if self.change_tasktable:
                        self.send_ta(self.arglist['id'],'stopped')
                else:
                    if self.change_tasktable:
                        self.send_ta(self.arglist['id'], 'waiting')
                self.log.logger.debug('change the work %s state'%self.arglist['name'])
            else:
                self.send_ta(self.arglist['id'], 'end')
            if self.workpool_workid_dict.has_key(self.name):
                del self.workpool_workid_dict[self.name]
            self.change_tasktable=True
            res = self.queue.qsize()  # 判断消息队列大小
            if res > 0:
                #print("ahua!There are still %d tasks to do" % (res))
                self.log.logger.warning("There are still %d tasks to do" % (res))

    def stopwork(self,change_tasktable=True):
        self.change_tasktable=change_tasktable
        self.work.stop()


class Delete:
    def __init__(self,log,**kwargs):
        self.log=log
        self.duration = kwargs.get('duration')
        self.vol = kwargs.get('vol')
        self.dir = kwargs.get('dir')
        self.ip = kwargs.get('ip')
        self.name=kwargs.get('name')
        self.id=kwargs.get('id')
        ms = Message("tcp")
        self.message=ms

    def send_bk(self,sub,**kwargs):
        data={}
        data['type']='return'
        dict={}
        data['data']=dict
        dict['sub']=sub
        dict['id']=kwargs['id']
        dict['name'] = kwargs['name']
        dict['start_time'] = kwargs['start_time']

        ret=self.message.send(str(data))
        if ret!=0:
            self.log.logger.error(ret)

    def do_mount(self):
            n = len(self.ip)
            if n==0:
                return -1
            if os.path.ismount(self.mount_dir):
                self.log.logger.error("the dir has mounted,maybe there is a delete work doing now")
                return -1
            while n > 0:
                self.glusterip = self.ip[n - 1]
                try:
                    cmd = ("mount.glusterfs %s:/%s %s 2>/dev/null" % (self.glusterip, self.vol, self.mount_dir))
                    try:
                        ret = os.system(cmd)
                        # print "do mount succeed"
                        if ret != 0:
                            self.log.logger.error("do mount failed ")
                            return -1
                        return 0
                    except  Exception as e:
                        # print ("do mount failed %s"%e)
                        # self.send_bk('message',"do mount failed %s"%e)
                        self.log.logger.warning("do mount failed%s"%e.message)
                        return -1
                except Exception as e:
                    # print ("do mount failed %s"%e)
                    # self.send_bk('message',"do mount failed %s"%e)
                    self.log.logger.warning("do mount failed%s"%e.message)
                    return -1
                n = n - 1

    def close(self):
        try:
            cmd = ('umount %s' % (self.mount_dir))
            ret = os.system(cmd)
           # print "do close succeed"
            if ret !=0:
                self.log.logger.error("do close failed" )
                return -1
            self.log.logger.info("do close succeed")
            return 0
        except Exception as e:
           # print e
            self.log.logger.error("do close failed %s"%e)
            return -1

    def delete(self,delAll):
        tarfilename='%s_%s'%(self.name,self.id)
        oldtime=self.get_oldtime(self.duration)
        tardir=os.path.join(self.mount_dir,self.dir)
        if not os.path.exists(tardir):
            return 0
        filename_list=os.listdir(tardir)
        for filename in filename_list:
            n=len(tarfilename)
            if filename[0:n]==tarfilename:
                if int(filename[n+1:n+9]) < oldtime or delAll :
                    realdir=os.path.join(tardir,filename)
                    start_time=int(time.mktime(time.strptime(str(filename[-14:]), '%Y%m%d%H%M%S')))
                    try:
                        shutil.rmtree(realdir)
                        self.send_bk('delete',start_time=start_time,id=self.id,name=self.name)
                    except Exception as e:
                        self.log.logger.error(e.message)
                        return -1
        return 0


    def get_oldtime(self,dt):
        old= time.localtime(int(time.time())-24*3600*int(dt))
        old_timeint=int(time.strftime("%Y%m%d", old))
        return old_timeint

    def start(self,delAll=False):
        if int(self.duration)==-1:
            return
        cp = ConfigParser.ConfigParser()
        cp.read('/etc/fbmp/client.conf')
        self.mount = cp.get('client', 'work_dir')
        self.mount_dir = "%sdelete/" % (self.mount)
        ret = self.do_mount()
        if ret !=0:
            self.log.logger.error('delete mount failed')
            return
        ret = self.delete(delAll)
        if ret !=0:
            self.close()
            self.log.logger.error('delete mount failed')
            return
        ret = self.close()
        if ret !=0:
            self.close()
            self.log.logger.error('delete mount failed')
        self.log.logger.info('delete work success')

        return