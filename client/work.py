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
        self.process=''
        self.pause=False
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
            if kwargs.get('process'):
                dict['process']=kwargs.get('process')
            else:
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

                ret = os.system(cmd)
                #print "do mount succeed"
                if ret!=0:
                    self.errormessage='mount falied'
                    return -1
                self.log.logger.info("do mount succeed")
                return 0

            except Exception as e:
                #print ("do mount failed %s"%e)
                #self.send_bk('message',"do mount failed %s"%e)
                self.errormessage = str(e)
                self.log.logger.warning("do mount failed %s"%e)
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
            except Exception as e:
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
                return 0
            for filename in filelist:

                try:
                    filepath=os.path.join(pd,filename)
                except Exception as e:
                    self.log.logger.error(e)

                #print filepath + '\n'

                if os.path.isdir(filepath):
                    ret=self.do_write_dir(filepath,vd,filename)
                    if ret!=0:
                        return ret

                else:
                    ret=self.do_write_file(filepath,vd)
                    if ret != 0:
                        return ret
        else:
            #print "0\n"
            ret=self.do_write_file(pd,vd)
        return ret

    def do_dump(self,cmd):
        write_now = 0
        self.log.logger.info('do dump')
        self.process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            write_now=self.get_file_size(self.mount_dir+'/'+self.vfile)
            self.send_bk('run', process=-1, current_size=str(write_now))
            time.sleep(1)
            if self.process.poll() != None:
                write_now = self.get_file_size(self.mount_dir+'/'+self.vfile)
                self.send_bk('run', process=200, current_size=str(write_now))
                break
        outdata, errdata = self.process.communicate()
        if self.pause:
            self.log.logger.info('dump is pause')
            self.errormessage='dump is pause'
            return -1
        if self.process.poll() != 0:
            # print 'error info:%s' % error
            self.log.logger.error("dump work failed" )
            self.log.logger.error(errdata)
            self.errormessage = errdata
            return -1
            # print write_all
            # print 'finished'
        self.log.logger.info("dump work finished" )
        return 0

    def do_write_file(self,pd,vd):
        write_all = self.proclen
        write_old = 0
        write_now = 0
        seek_old=0
        seek_now=0
        self.log.logger.info('write file %s'%pd)
        cmd = ('rsync -avlP %s %s' % (pd, vd))
        #print cmd
        fp = tempfile.TemporaryFile(mode='w+t')
        self.process = subprocess.Popen(cmd, shell=True, stdout=fp,stderr=subprocess.PIPE )
        while True:
            seek_now=seek_old
            fp.seek(seek_now)
            seek_old=int(fp.tell())
            lines = fp.readlines()
            #print fp.tell()
            for line in lines:
                s = line
                if len(s) <= 1:
                    continue
                list = s.split()
                #print 'line is',str(s)
                #print 'list is',str(list)
                if list[0].isdigit():
                    write_old = write_now
                    list_digit=[]
                    for i in list:
                        if i.isdigit():
                           list_digit.append(int(i))
                    write_now = int(max(list_digit))
                    write_all = write_all + (write_now - write_old)
                    write_old = write_now
                    pro=(int((write_all * 100) / self.proctotal))
                    if pro-self.sendpro>=2:
                        self.send_bk('run',process=str(pro),current_size=str(write_all))
                        self.sendpro=pro
                time.sleep(1)
            if self.process.poll() != None:
                list=pd.split('/')
                new_file=os.path.join(vd,list[-1])
                if self.get_file_size(pd)==self.get_file_size(new_file):
                    self.proclen=self.proclen+self.get_file_size(new_file)
                    pro=(int((self.proclen * 100) / self.proctotal))
                    if pro-self.sendpro>=2 or pro==100:
                        self.send_bk('run',process=str(pro),current_size=str(self.proclen))
                        self.sendpro=pro
                else:
                    self.errormessage = 'the document copy incomplete'
                    return -1
                break
        fp.close()
        outdata, errdata = self.process.communicate()
        if self.pause:
            self.log.logger.info('the work is pause')
            self.errormessage='the work is pause'
            return -1
        if  self.process.poll() != 0:
            #print 'error info:%s' % error
            self.log.logger.error("cmd %s work failed"%cmd)
            self.log.logger.error(errdata)
            self.errormessage=errdata
            return -1
       # print write_all
       # print 'finished'
        self.log.logger.info("cmd %s work finished"%cmd)
        return 0

    def do_write_dir(self,pdir,vdir,pname):
        vfilepath = os.path.join(vdir, pname)
        try:
            os.mkdir(vfilepath)
        except Exception as e:
            self.log.logger.error(e)
        ret=self.do_work(pdir,vfilepath)
        return ret

    def do_close(self):
        try:
            cmd = ('umount %s' % (self.mount_dir))
            ret = os.system(cmd)
           # print "do close succeed"
            if ret !=0:
                self.log.logger.error("do close failed" )
                return -1
            else:
                self.log.logger.info("do close succeed")
                return 0
        except Exception as e:
           # print e
            self.log.logger.error("do close failed %s"%e)
            return -1

    def get_file_size(self, file_path):
        size = 0L
        try:
            if isfile(file_path):
                size = getsize(file_path)
            elif os.path.isdir(file_path):
                for root, dirs, files in os.walk(file_path):
                    size += sum([getsize(join(root, name)) for name in files])
        except Exception as e:
            self.log.logger.error(e)
            self.errormessage=str(e)
            size=-1L
        return size

    def start(self):
        self.op=self.arglist['op']
        if self.op == 'backup':
            #if self.arglist.has_key('destination _ip'):
            #    self.arglist['ip'].append(self.arglist['destination _ip'])
            self.pfile = self.arglist['source_address']
            self.proctotal = self.get_file_size(self.pfile)
            start_time=float(int(time.time()))
            timeArray = time.localtime(start_time)
            if self.proctotal < 0:
                self.send_bk('frist', total_size=self.proctotal, start_time=str(start_time))
                time.sleep(5)
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
            elif self.proctotal == 0:
                self.send_bk('frist', total_size=self.proctotal, start_time=str(start_time))
                time.sleep(5)
                self.errormessage='the size of file is zero'
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
            self.send_bk('frist',total_size=self.proctotal,start_time=str(start_time))
            self.vfile = self.arglist['destination_address'] +"/"+ self.arglist['name']+"_"+self.arglist['id'] + "_" + time.strftime("%Y%m%d%H%M%S", timeArray) + "/"  # 添加时间戳
            self.mount_dir = "%s%s" % (self.mount,self.arglist['threadId'])
            self.vol = self.arglist['destination_vol']


            ret = self.do_mount()
            if ret != 0:
                #print "mount failed"
                if self.errormessage == "":
                    self.errormessage = 'mount failed'
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
                #print "work failed"
                if self.errormessage == "":
                    self.errormessage = 'backup failed'
                if self.pause:
                    self.log.logger.info('backup aborted')
                    self.send_bk('last', state='aborted', end_time=str(time.time()))
                    self.errormessage = 'backup aborted'
                else:
                    self.log.logger.error('backup failed')
                    self.send_bk('last', state='failed', end_time=str(time.time()))
                try:
                    self.do_close()
                except Exception as e:
                    self.log.logger.error(e)
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
            self.send_bk('frist',total_size=-1,start_time=str(start_time),process=200)
            self.mount_dir =  "%s%s" % (self.mount,self.arglist['threadId'])
            self.vol = self.arglist['destination_vol']
            self.vfile=self.arglist['destination_address'] +"/"+ self.arglist['name']+"_"+self.arglist['id'] + "_" + time.strftime("%Y%m%d%H%M%S", timeArray) + "/"  # 添加时间戳
            path=self.arglist['source_address']

            ret = self.do_mount()
            if ret != 0:
                self.errormessage = 'mount failed'
                self.log.logger.error('mount failed')
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
            ret=self.do_dump(cmd)
            if ret!=0:
                self.do_close()
                if self.errormessage == "":
                    self.errormessage = 'dump failed'
                self.send_bk('last', state='failed', end_time=str(time.time()))
                return
            self.send_bk('run', process=200, current_size=self.get_file_size(self.mount_dir+'/'+self.vfile))
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
            if self.proctotal < 0:
                self.send_bk('frist', total_size=self.proctotal, start_time=str(time.time()))
                time.sleep(5)
                self.send_bk('last', state='failed', end_time=str(time.time()))
                self.do_close()
                return
            elif self.proctotal == 0:
                self.send_bk('frist', total_size=self.proctotal, start_time=str(time.time()))
                time.sleep(5)
                self.errormessage = 'the size of file is zero'
                self.send_bk('last', state='failed', end_time=str(time.time()))
                self.do_close()
                return
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
                if self.pause:
                    self.log.logger.info('recover pause')
                    self.errormessage = 'recover pause'
                    self.send_bk('last', state='aborted', end_time=str(time.time()))
                else:
                    self.log.logger.error('recover failed')
                    if self.errormessage == "":
                        self.errormessage = 'recover failed'
                    self.send_bk('last', state='failed', end_time=str(time.time()))
                return
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

    def stop(self):
        if self.process!='':
            self.pause=True
            self.process.kill()
            self.log.logger.info('kill process')

