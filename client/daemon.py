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
from workerpool import WorkerPool
import ConfigParser
import  uuid

class Daemon:
    def __init__( self, pidfile,  mylogger, glusterip="", confip="", stdin='/dev/stderr', stdout='/dev/stderr',
                  stderr='/dev/stderr' ):
        # self.logger = logging.getLogger(__name__)
        cp = ConfigParser.ConfigParser()
        cp.read('/etc/SFbackup/client.conf')
        log_level = cp.get('client', 'log_level')
        log_file_dir = cp.get('client', 'log_file_dir')
        self.log=mylogger
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.timer_interval = int(cp.get('client', 'timer_interval'))
        self.qdpth = int(cp.get('client', 'qdpth'))
        # print "pid file:",self.pidfile
        self.timer_id = 0
        self.q = ""
        self.uc_size = int(cp.get('client', 'usually_concurrent')) # 线程池大小
        self.ic_size = int(cp.get('client', 'immediately_concurrent'))
        self.version=cp.get('client', 'version')
        self.group = cp.get('client', 'group')
        self.reload_interval = int(cp.get('client', 'reload_interval'))
        self.port = cp.get('server', 'port')
        self.info_l = ""
        self.glusterlist = ['10.202.125.83']
        self.confip = '10.202.125.83:80'
        self.task_sum = 0  # 当前任务数
        self.task_list = {}
        self.tp = []
        self.hostname = str(socket.gethostname())
        self.ip = socket.gethostbyname(self.hostname)

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
            if self.message.con.acquire():
                if not self.message.q.empty():
                        msg = self.message.get_queue()
                        #print msg
                        msg_data = msg.split(":", 1)[1]
                        #print msg_data
                        self.log.logger.info("get msg is that %s"%msg_data)
                        date = eval(msg_data)
                        self.schd_task(date)
                else:
                        self.message.con.wait()
                time.sleep(1)
                self.message.con.release()

    def generate_uuid( dashed=True ):
        """Creates a random uuid string.
        :param dashed: Generate uuid with dashes or not
        :type dashed: bool
        :returns: string
        """
        if dashed:
            return str(uuid.uuid4())
        return uuid.uuid4().hex


    def deleteBackupData(self):
        pass
        if self.arglist['run_sub'] == 'date' or self.arglist['duration'] == '-1':
            return 0
        old_time=self.wait_start-timedelta(days=int(self.arglist['duration']))
        dict=self.arglist['cron']
        start_time=datetime.strptime(dict['start_date'], "%Y-%m-%d %H:%M:%S")
        if start_time>old_time:
            return 0
        self.oldvfile=self.arglist['destination_address'] + self.arglist['name'] +"_"+self.arglist['id']+ "_" + old_time.strftime(
                '%Y%m%d%H%M') + "/"
        if os.path.exists('%s/%s'%(self.mount_dir, self.oldvfile)):
            try:
                shutil.rmtree(self.mount_dir+'/'+self.oldvfile)
                self.log.logger.info("delete %s succeed"%self.oldvfile)
                return 0
            except Exception,e:
                #print "delete failed"
                self.log.logger.error("delete %s failed %s" % (self.oldvfile,e))
                self.send_bk('message',"delete %s failed %s" % (self.oldvfile,e))
                return -1



    def send_ta(self,id,value):
        data="{'type':'state','data':{'id':'%s','state':'%s'}}"%(id,value)
        ret=self.message.send(data)
        if ret!=0:
            self.log.logger.error('message send failed %s'%ret)

    def send_bk(self,sub,id,value):
        if sub == 'live':
            data = "{'type':'return','data':{'sub':'%s','ip':'%s','hostname':'%s','work_num':'%s'}}" % (sub, self.ip, self.hostname, value)
            ret=self.message.send(data)
            if ret!=0:
                self.log.logger.error('message send failed %s'%ret)
        else:
            bk_id = self.generate_uuid()
            data = "{'type':'return','data':{'sub':'%s','id':'%s','bk_id':'%s','%s':'%s'}}" % (sub, id, bk_id, sub, value)
            ret = self.message.send(data)
            if ret != 0:
                self.log.logger.error(ret)


    def _timer_func( self ):
        # print "timer running at:",datetime.now()
        self.timer_id = self.timer_id + 1
        """
        没过2秒判断一次线程是否挂了，如果挂了需要重新启动线程加入到threadpool中
        """
        if self.timer_id * self.timer_interval % self.reload_interval == 0:
            #self.send_bk('live','1',self.task_sum)
            pass


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
            newthread = WorkerPool(self.q, t.getName(), self.uc_size,self.confip,self.log)
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

    def addtask(self,data,do_type):
        dict = data['data']
        dict['bk_id']=self.generate_uuid()
        ms = dict['id']
        dict['op'] =data['type']
        self.log.logger.info('create a new %s backup work,the id of it is %s' %(do_type,ms) )
        new_task = SingleTask(ms, self.scheduler, dict, self.q, self.glusterlist, self.confip, self.log)
        new_task.start(do_type)
        self.task_list[ms] = new_task
        self.task_sum = self.task_sum + 1
        self.send_ta(dict['id'], 'waiting')

    def schd_task( self, data ):
        if data['type'] == 'backup':  # 创建新任务
            dict = data['data']
            if dict['run_sub'] == 'date':
                #print "do backup use direct"
                self.addtask(data,'date')
            elif dict['run_sub'] == 'cron':
                #print "do backup use queue"
                self.addtask(data,'cron')
            elif dict['run_sub'] == 'immediately':
                dict = data['data']
                dict['bk_id'] = self.generate_uuid()
                dict['op'] = "backup"
                dict['ip'] = self.glusterlist
                now = datetime.now()
                dict['wait_start'] = now.strftime('%Y-%m-%d %H:%M:%S')
                self.qq.put([str(dict), 2], block=True, timeout=None)
                self.send_ta(dict['id'],'waiting')
        elif data['type'] == "update":
            print "do revise"
            dict = data['data']
            self.log.logger.info('change a work,the id of it is %s'%dict['id'])
            ms = dict['id']
            if self.task_list.has_key(ms):
                try:
                    self.task_list[ms].do_remove_job()
                    del self.task_list[ms]
                    self.task_sum = self.task_sum - 1
                    dict['op'] = dict['sub']
                    new_task = SingleTask(ms, self.scheduler, dict, self.q, self.glusterlist, self.confip, self.log)
                    new_task.start(dict['run_sub'])
                    self.task_list[ms] = new_task
                    self.task_sum = self.task_sum + 1
                    self.send_ta(dict['id'], 'waiting')
                except:
                    pass
            else:
                self.log.logger.error('No any work which id is %s' % ms)

        elif data['type'] == 'recover':  # 恢复备份文件
            print "do recover"
            dict=data['data']
            if dict['run_sub'] =='immediately':
                dict = data['data']
                dict['bk_id'] = self.generate_uuid()
                dict['op'] = "recover"
                dict['ip'] = self.glusterlist
                now = datetime.now()
                dict['wait_start'] = now.strftime('%Y-%m-%d %H:%M:%S')
                self.qq.put([str(dict), 2], block=True, timeout=None)
                self.send_ta( dict['id'], 'waiting')
            else:
                self.log.logger.error('recover  must be immediately')
        elif data['type'] == 'delete':  # 删除任务
            #print "do delete"
            dict = data['data']
            self.log.logger.info('delete a work,the id of it is %s' % dict['id'])
            ms = dict['id']
            if self.task_list.has_key(ms):
                self.task_list[ms].do_remove_job()
                del self.task_list[ms]
                self.task_sum = self.task_sum - 1
            else:
                self.log.logger.error('No any work which id is %s'%ms)
            if dict.has_key('delete'):
                self.send_ta( ms, 'deleted')
            else:
                self.send_ta(ms, 'stopped')
        elif data['type'] == 'dump':  # 准备dump
            dict = data['data']
            if dict['run_sub'] == 'cron':
               # print "do dump in queue"
               self.addtask(data,'cron')
            elif dict['run_sub'] == 'date':
                #print "do dump in direct"
                self.addtask(data,'date')
            elif dict['run_sub'] == 'immediately':
                dict = data['data']
                dict['bk_id'] = self.generate_uuid()
                dict['op'] = "dump"
                dict['ip'] = self.glusterlist
                now = datetime.now()
                dict['wait_start'] = now.strftime('%Y-%m-%d %H:%M:%S')
                self.qq.put([str(dict), 2], block=True, timeout=None)
                self.send_ta(dict['id'], 'waiting')
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
        self.qq = Queue.Queue(self.qdpth)
        for i in range(self.uc_size):
            t = WorkerPool(self.q, i,self.uc_size ,self.confip,self.log)
            self.tp.append(t)
        for i in range(self.uc_size,self.uc_size+self.ic_size):
            t = WorkerPool(self.qq, i,self.uc_size, self.confip, self.log)
            self.tp.append(t)
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

        self.log.logger.debug("initialize")
        data = "{'type': 'initialize', 'data': {'ip': '%s', 'hostname': '%s', 'version': '%s','group':'%s'}}" % (self.ip, self.hostname, self.version,self.group)
        self.log.logger.debug("group %s "%self.group)
        try:
            ret=self.message.send(data)
            if ret!=0:
                self.log.logger.error(ret)
        except Exception,e:
            print e
        self.log.logger.debug("date")
        self.scheduler.start()
        #print "start threadpool over"
        self.log.logger.debug("start threadpool over")
        """
        """
