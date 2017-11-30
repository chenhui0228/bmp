#!/usr/bin/env python
#coding:utf-8
import os
from os.path import join, getsize, isfile
#from datetime import *
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
        self.arglist = arglist
        cp = ConfigParser.ConfigParser()
        cp.read('/etc/SFbackup/client.conf')
        self.mount = cp.get('client', 'mount_dir')
        self.errormessage=""
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

    def send_bk(self,sub,**kwargs):
        data={}
        data['type']='return'
        dict={}
        data['data']=dict
        dict['sub']=sub
        dict['id']=self.arglist['id']
        dict['bk_id']=self.arglist['bk_id']
        if sub == 'frist':
            dict['start_time']=kwargs['start_time']
            dict['total_size'] = kwargs['total_size']
            dict['process']='0'
            dict['state']='runing'
        elif sub == 'run':
            dict['process'] = kwargs['process']
            dict['current_size']=kwargs['current_size']
        elif sub == 'last':
            dict['state'] = kwargs['state']
            dict['end_time'] = kwargs['end_time']
            dict['message']=self.errormessage
        ret=self.message.send(str(data))
        if ret!=0:
            self.log.logger.error(ret)




    def do_mount(self):
        n=len(self.arglist['ip'])
        if os.path.ismount(self.mount_dir):
            self.log.logger.error("the dir has mounted,maybe there is a direct work doing now")
            #self.send_bk('message','the dir has mounted,maybe there is a direct work doing now')
            return -1
        while n>0:
            self.glusterip=self.arglist['ip'][n-1]
            try:
                cmd = ("mount.glusterfs %s:/%s %s 2>/dev/null" % (self.glusterip, self.vol, self.mount_dir))
                try:
                    ret = os.system(cmd)
                    #print "do mount succeed"
                    if ret!=0:
                        self.errormessage='mount falied'
                        return -1
                    self.log.logger.info("do mount succeed")
                    return 0
                except  Exception,e:
                    #print ("do mount failed %s"%e)
                    #self.send_bk('message',"do mount failed %s"%e)
                    self.log.logger.warning("do mount failed")
                    return -1
            except Exception,e:
                #print ("do mount failed %s"%e)
                #self.send_bk('message',"do mount failed %s"%e)
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
                if ret!=0:
                    self.errormessage='mkdir failed'
                    return -1
                self.log.logger.info("do mkdir succeed")
                return 0
            except Exception,e:
                self.errormessage =e.message
               # print ("do mkidr failed %s"%e)
                self.log.logger.info("do mkdir failed")
                #self.send_bk('message',"do mkidr failed %s"%e)
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
        fp = tempfile.TemporaryFile(mode='w+t')
        process = subprocess.Popen(cmd, shell=True, stdout=fp,stderr=subprocess.PIPE )
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
                        self.send_bk('run',process=str(pro),current_size=str(write_all))
                        self.sendpro=pro
                else:
                    write_old = 0
                    write_now = 0
                time.sleep(1)
            if process.poll() != None:
                list=pd.split('/')
                new_file=os.path.join(vd,list[-1])
                if self.get_file_size(pd)==self.get_file_size(new_file):
                    self.proclen=self.proclen+self.get_file_size(new_file)
                    pro=(int((self.proclen * 100) / self.proctotal))
                    if pro-self.sendpro>=2 or pro==100:
                        self.send_bk('run',process=str(pro),current_size=str(write_all))
                        self.sendpro=pro
                else:
                    return -1
                break
        fp.close()
        outdata, errdata = process.communicate()
        if  len(errdata) != 0:
            #print 'error info:%s' % error
            self.log.logger.error("cmd %s work failed"%cmd)
            self.log.logger.error(errdata)
            self.errormessage=str(errdata)
            return -1
       # print write_all
       # print 'finished'
        self.log.logger.info("cmd %s work finished"%cmd)
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
            return -1


    def get_file_size(self, file_path):
        size = 0L
        if isfile(file_path):
            size = getsize(file_path)
        else:
            for root, dirs, files in os.walk(file_path):
                size += sum([getsize(join(root, name)) for name in files])
        return size


    def start(self):
        self.op=self.arglist['op']
        if self.op == 'backup':
            #if self.arglist.has_key('destination _ip'):
            #    self.arglist['ip'].append(self.arglist['destination _ip'])
            self.pfile = self.arglist['source_address']
            self.proctotal = self.get_file_size(self.pfile)
            if self.proctotal==0:
                self.proctotal+=1
            start_time=float(int(time.time()))
            timeArray = time.localtime(start_time)
            self.send_bk('frist',total_size=self.proctotal,start_time=str(start_time))
            self.vfile = self.arglist['destination_address'] +"/"+ self.arglist['name']+"_"+self.arglist['id'] + "_" + time.strftime("%Y%m%d%H%M%S", timeArray) + "/"  # 添加时间戳
            self.mount_dir = "%s%s" % (self.mount,self.arglist['threadId'])
            self.vol = self.arglist['destination_vol']


            ret = self.do_mount()
            if ret != 0:
                #print "mount failed"
                if self.errormessage == "":
                    self.errormessage = 'backup failed'
                self.send_bk('last', state='failed',end_time=str(time.time()))
                return
            ret = self.do_mkdir(self.mount_dir+'/'+self.vfile)
            if ret != 0:
                self.do_close()
                #print "mkdir failed"
                self.log.logger.error('mkdir failed')
                if self.errormessage == "":
                    self.errormessage = 'mkdir failed'
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
            ret = self.do_work(self.pfile,self.mount_dir+'/'+self.vfile)
            if ret != 0:
                self.do_close()
                #print "work failed"
                if self.errormessage == "":
                    self.errormessage = 'backup failed'
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
            ret = self.do_close()
            if ret != 0:
                self.errormessage = 'umont failed'
                self.do_close()
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
        elif self.op=='dump':
            #if self.arglist.has_key('destination _ip'):
            #    self.arglist['ip'].append(self.arglist['source_ip'])
            start_time=float(int(time.time()))
            timeArray = time.localtime(start_time)
            self.send_bk('frist',total_size=-1,start_time=str(start_time))
            self.mount_dir =  "%s%s" % (self.mount,self.arglist['threadId'])
            self.vol = self.arglist['destination_vol']
            self.vfile=self.arglist['destination_address'] +"/"+ self.arglist['name']+"_"+self.arglist['id'] + "_" + time.strftime("%Y%m%d%H%M%S", timeArray) + "/"  # 添加时间戳
            path=self.arglist['source_address']

            ret = self.do_mount()
            if ret != 0:
                self.errormessage = 'mount failed'
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return

            ret = self.do_mkdir(self.mount_dir+'/'+self.vfile)
            if ret != 0:
                self.do_close()
                #print "mkdir failed"
                if self.errormessage == "":
                    self.errormessage = 'mkdir failed'
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
            cmd = './%s %s/%s' % (path, self.mount_dir, self.vfile)
            ret=os.system(cmd)
            if ret!=0:
                self.do_close()
                if self.errormessage == "":
                    self.errormessage = 'dump failed'
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
            self.send_bk('run', process=100, current_size=self.get_file_size(self.mount_dir+'/'+self.vfile))
            ret = self.do_close()
            #print "end do_cloes"
            if ret != 0:
                time.sleep(2)
                if self.errormessage == "":
                    self.errormessage = 'umount failed'
                self.do_close()
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
        elif self.op=='recover':
            #if self.arglist.has_key('destination _ip'):
             #   self.arglist['ip'].append(self.arglist['source_ip'])

            self.mount_dir = "%s%s" % (self.mount, self.arglist['threadId'])
            self.vol = self.arglist['source_vol']
            self.vfile = self.mount+'recover'+self.arglist['destination_address']
            self.pfile = self.arglist['source_address']
            ret = self.do_mount()
            if ret != 0:
                return
            self.proctotal = self.get_file_size((self.mount_dir + self.pfile))
            if self.proctotal == 0:
                self.proctotal+=1
            self.send_bk('frist', total_size=self.proctotal, start_time=str(time.time()))
            ret = self.do_mkdir(self.vfile)
            if ret != 0:
                self.do_close()
                if self.errormessage == "":
                    self.errormessage='mkdir failed'
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
            #self.vfile=os.path.join(self.vfile)
            ret = self.do_work(self.mount_dir+self.pfile,self.vfile)
            if ret != 0:
                self.do_close()
                if self.errormessage == "":
                    self.errormessage = 'recover failed'
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
            time.sleep(2)
            ret = self.do_close()
            if ret != 0:
                if self.errormessage == "":
                    self.errormessage = 'umont failed'
                self.do_close()
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
        else:
            self.send_bk('last', state='failed', end_time=str(time.time()))
            return
            #print "end do_cloes"
        self.send_bk('last', state='success', end_time=str(time.time()))
        self.log.logger.info("the work %s is success"%self.arglist['name'])
        return
