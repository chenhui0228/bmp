#!/usr/bin/env python
#coding:utf-8
import os
from os.path import join, getsize, isfile
from datetime import *
import subprocess
import time
import shutil
from message import Message
import tempfile
import ConfigParser


class Work():
    # def
    # __init__(self,op,ip,volume,vfile=None,pfile=None,pdir=None,confip=None):

    def __init__(self, arglist,log):
        self.log =log
        self.proclen=0
        self.proctotal=0
        ms = Message("tcp")
        self.message=ms
        self.sendpro=0
        #print "to init arglist"
        self.wait_start = datetime.strptime(arglist['wait_start'], "%Y-%m-%d %H:%M:%S")  # 开始等待
        self.arglist = arglist
        cp = ConfigParser.ConfigParser()
        cp.read('/etc/SFbackup/client.conf')
        self.mount = cp.get('client', 'mount_dir')
        #print "work arglist is:", self.arglist, " time at:", datetime.now()
        #self.log.logger.info("work arglist is:", self.Z, " time at:", datetime.now())
        #self.log.logger.debug('work arglist is ' + str(self.arglist))
        # self.max_size = 4194304  # 4M
        if self.arglist is None:
            #print "arg is NULL ?"
            self.log.logger.warning('arg is NULL!')
            self.send_bk("log","arg is NULL ?")
            return
        return

    def send_bk(self,sub,value):
        data="{'type':'return','data':{'sub':'%s','id':'%s','bk_id':'%s','%s':'%s'}}"%(sub,self.arglist['id'],self.arglist['bk_id'],sub,value)
        ret=self.message.send(data)
        if ret!=0:
            self.log.logger.error(ret)

    def do_mount(self):
        n=len(self.arglist['ip'])
        if os.path.ismount(self.mount_dir):
            self.log.logger.error("the dir has mounted,maybe there is a direct work doing now")
            self.send_bk('message','the dir has mounted,maybe there is a direct work doing now')
            return -1
        while n>0:
            self.glusterip=self.arglist['ip'][n-1]
            try:
                cmd = ("mount.glusterfs %s:/%s %s 2>/dev/null" % (self.glusterip, self.vol, self.mount_dir))
                try:
                    ret = os.system(cmd)
                    #print "do mount succeed"
                    self.log.logger.info("do mount succeed")
                    return 0
                except  Exception,e:
                    #print ("do mount failed %s"%e)
                    self.send_bk('message',"do mount failed %s"%e)
                    self.log.logger.warning("do mount failed")
                    return -1
            except Exception,e:
                #print ("do mount failed %s"%e)
                self.send_bk('message',"do mount failed %s"%e)
                self.log.logger.warning("do mount failed")
                return -1
            n=n-1



    def do_mkdir(self,dir):
        if os.path.exists('%s'%dir):
            return 0
        else:
            try:
                cmd = ("mkdir -p %s" % dir)
                ret = os.system(cmd)
               # print "do mkidr succeed"
                self.log.logger.info("do mkdir succeed")
                return 0
            except Exception,e:
               # print ("do mkidr failed %s"%e)
                self.log.logger.info("do mkdir failed")
                self.send_bk('message',"do mkidr failed %s"%e)
                return -1




    def do_work(self,pd, vd):
        ret=0
        #print "do work"
        if os.path.isdir(pd):
            #print "1\n"
            filelist=os.listdir(pd)
            if len(filelist) == 0:
                #print pd
                return
            for filename in filelist:

                try:
                    filepath=os.path.join(pd,filename)
                except Exception,e:
                    self.log.logger.error(e)

                #print filepath + '\n'

                if os.path.isdir(filepath):
                    ret=self.do_write_dir(filepath,vd,filename)
                else:
                    ret=self.do_write_file(filepath,vd)
        else:
            #print "0\n"
            ret=self.do_write_file(pd,vd)
        return ret



    def do_write_file(self,pd,vd):
        write_all = self.proclen
        write_old = 0
        write_now = 0
        self.log.logger.info('write file %s'%pd)
        cmd = ('rsync -avlP %s %s' % (pd, vd))
       #print cmd
        try:
            fp = tempfile.TemporaryFile(mode='w+t')
            process = subprocess.Popen(cmd, shell=True, stdout=fp,stderr=subprocess.PIPE)
            while True:
                lines = fp.readlines()
                for line in lines:
                    s = line
                    if len(s) <= 1:
                        continue
                    list = s.split()
                    if list[0].isdigit():
                        write_old = write_now
                        write_now = int(list[0])
                        write_all = write_all + (write_now - write_old)
                        #print 'the size of file is %d' % (int((write_all * 100) / self.proctotal))
                        pro=(int((write_all * 100) / self.proctotal))
                        if pro-self.sendpro>=2:
                            self.send_bk('process',str(pro))
                            self.send_bk('current_size', str(write_all))
                            self.sendpro=pro
                    else:
                        write_old = 0
                        write_now = 0
                    time.sleep(1)
                if process.poll() == 0:
                    list=pd.split('/')
                    new_file=os.path.join(vd,list[-1])
                    if self.get_file_size(pd)==self.get_file_size(new_file):
                        self.proclen=self.proclen+self.get_file_size(new_file)
                        pro=(int((self.proclen * 100) / self.proctotal))
                        if pro-self.sendpro>=2 or pro==100:
                            self.send_bk('process',str(pro))
                            self.send_bk('current_size', str(self.proclen ))
                            self.sendpro=pro
                    else:
                        #print "size is not same"
                        return -1
                    break
            fp.close()
            error = process.stderr.read()
            if not error == '':
                #print 'error info:%s' % error
                self.log.logger.error("cmd %s work failed"%cmd)
                self.send_bk('message',"cmd %s work failed"%cmd)
                return -1
           # print write_all
           # print 'finished'
            self.log.logger.info("cmd %s work finished"%cmd)
        except Exception,e:
            self.log.logger.error("cmd %s work failed %s"%(cmd,e))
            return -1
        return 0

    def do_write_dir(self,pdir,vdir,pname):
        vfilepath = os.path.join(vdir, pname)
        try:
            os.mkdir(vfilepath)
        except Exception,e:
            self.log.logger.error(e)
        ret=self.do_work(pdir,vfilepath)
        return ret




    def do_close(self):
        try:
            cmd = ('umount %s' % (self.mount_dir))
            ret = os.system(cmd)
           # print "do close succeed"
            self.log.logger.info("do close succeed")
            return 0
        except Exception,e:
           # print e
            self.log.logger.error("do close failed %s"%e)
            self.send_bk('message',"do close failed %s"%e)
            return -1


    def get_file_size(self, file_path):
        size = 0L
        if isfile(file_path):
            size = getsize(file_path)
        else:
            for root, dirs, files in os.walk(file_path):
                size += sum([getsize(join(root, name)) for name in files])
        return size

    def do_delete(self):
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

    def start(self):
        self.op=self.arglist['op']
        self.send_bk('start_time', str(time.time()))
        if self.op == 'backup':
            #if self.arglist.has_key('destination _ip'):
            #    self.arglist['ip'].append(self.arglist['destination _ip'])
            self.pfile = self.arglist['source_address']
            self.proctotal = self.get_file_size(self.pfile)
            print self.proctotal
            self.send_bk('total_size',self.proctotal)
            self.vfile = self.arglist['destination_address'] +"/"+ self.arglist['name']+"_"+self.arglist['id'] + "_" + self.wait_start.strftime(
                '%Y%m%d%H%M') + "/"  # 添加时间戳
            self.mount_dir = "%s%s" % (self.mount,self.arglist['threadId'])
            self.vol = self.arglist['destination_vol']


            ret = self.do_mount()
            if ret != 0:
                #print "mount failed"
                self.send_bk('state', 'failed')
                self.send_bk('end_time', str(time.time()))
                return
            ret = self.do_mkdir(self.mount_dir+'/'+self.vfile)
            if ret != 0:
                self.do_close()
                #print "mkdir failed"
                self.send_bk('state', 'failed')
                self.send_bk('end_time', str(time.time()))
                return
            ret = self.do_work(self.pfile,self.mount_dir+'/'+self.vfile)
            if ret != 0:
                self.do_close()
                #print "work failed"
                self.send_bk('state', 'failed')
                self.send_bk('end_time', str(time.time()))
                return
            ret = self.do_delete()
            if ret != 0:
               # print "delete failed"
                self.log.logger.error("delete failed")
            ret = self.do_close()
            #print "end do_cloes"
            if ret != 0:
                self.do_close()
                self.send_bk('state', 'failed')
                self.send_bk('end_time', str(time.time()))
                return
        elif self.op=='dump':
            #if self.arglist.has_key('destination _ip'):
            #    self.arglist['ip'].append(self.arglist['source_ip'])
            self.mount_dir =  self.arglist['source_address']
            self.vol = self.arglist['destination_vol']
            self.vfile=self.arglist['destination_address']
            path=self.arglist['script']
            ret = self.do_mount()
            if ret != 0:
                self.send_bk('state', 'failed')
                self.send_bk('end_time', str(time.time()))
                return
            ret=os.system(path)
            if ret!=0:
                self.do_close()
                self.send_bk('state', 'failed')
                self.send_bk('end_time', str(time.time()))
                return
            ret = self.do_close()
            #print "end do_cloes"
            if ret != 0:
                time.sleep(2)
                self.do_close()
                self.send_bk('state', 'failed')
                self.send_bk('end_time', str(time.time()))
                return
        elif self.op=='recover':
            #if self.arglist.has_key('destination _ip'):
             #   self.arglist['ip'].append(self.arglist['source_ip'])

            self.mount_dir = "%s%s" % (self.mount, self.arglist['threadId'])
            self.vol = self.arglist['source_vol']
            self.vfile = self.arglist['destination_address']
            self.pfile = self.arglist['source_address'] + "/" + self.arglist['name'] + '_'+self.arglist['id']+'_'+\
                         self.arglist['backup_time']
            ret = self.do_mount()
            if ret != 0:
                self.send_bk('state', 'failed')
                self.send_bk('end_time', str(time.time()))
                return
            self.proctotal = self.get_file_size((self.mount_dir + self.pfile))
            ret = self.do_mkdir(self.vfile+'/'+self.arglist['name'] + '_'+self.arglist['id']+'_'+\
                         self.arglist['backup_time'])
            if ret != 0:
                self.do_close()
                self.send_bk('state', 'failed')
                self.send_bk('end_time', str(time.time()))
                return
            self.vfile=os.path.join(self.vfile,self.arglist['name'] + '_'+self.arglist['backup_time'])
            ret = self.do_work(self.mount_dir+self.pfile,self.vfile)
            if ret != 0:
                self.do_close()
                self.send_bk('state', 'failed')
                self.send_bk('end_time', str(time.time()))
                return
            ret = self.do_close()
            if ret != 0:
                self.do_close()
                self.send_bk('state', 'failed')
                self.send_bk('end_time', str(time.time()))
                return
        else:
            self.send_bk('state', 'failed')
            self.send_bk('end_time', str(time.time()))
            return
            #print "end do_cloes"
        self.send_bk('state','success')
        self.send_bk('end_time', str(time.time()))
        self.log.logger.info("the work %s is success"%self.arglist['name'])
        return
