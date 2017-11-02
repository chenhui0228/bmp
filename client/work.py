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
import subprocess
import time
import Queue
import types
import json
import socket
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import math
import logging.handlers as handlers


class Work():
    # def
    # __init__(self,op,ip,volume,vfile=None,pfile=None,pdir=None,confip=None):

    def __init__(self, arglist):
        print
        "to init arglist"
        self.wait_start = datetime.strptime(arglist['wait_start'], "%Y-%m-%d %H:%M:%S")  # 开始等待
        self.arglist = arglist
        print
        "work arglist is:", self.arglist, " time at:", datetime.now()
        # self.logger.debug('work arglist is ' + str(self.arglist))
        # self.max_size = 4194304  # 4M
        self._can_create = False
        if self.arglist is None:
            print
            "arg is NULL ?"
            #  self.logger.warning('arg is NULL!')
            return
        if self.arglist.has_key('task_id'):
            self.task_id = self.arglist['task_id']
        self.statetable_id = ""


        self.arglist=arglist
        return


    def do_mount(self):
        self.mount_dir = "/mnt/del/%s" % self.arglist['threadId']
        self.vol=self.arglist['destination_vol']
        n=len(self.arglist['ip'])
        while n>0:
            self.glusterip=self.arglist['ip'][n-1]
            try:
                cmd = ("mount.glusterfs %s:/%s %s" % (self.glusterip, self.vol, self.mount_dir))
                ret = os.system(cmd)
                print "do mount succeed"
                return ret
            except:
                print "do mount failed"
            n=n-1



    def do_mkdir(self):
        self.vfile = self.arglist['destination_address'] + self.arglist['name'] + "_" + self.wait_start.strftime('%Y%m%d%H%M') + "/"  # 添加时间戳
        if os.path.exists('%s/%s'%(self.mount_dir, self.vfile)):
            return 0
        else:
            try:
                cmd = ("mkdir -p %s/%s" % (self.mount_dir, self.vfile))
                ret = os.system(cmd)
                print "do mkidr succeed"
                return ret
            except:
                return -1




    def do_write(self):
        self.pfile = self.arglist['source_address']
        self.proctotal=self.get_file_size(self.pfile)
        write_all = 0
        write_old = 0
        write_now = 0
        try:
            cmd = ('rsync -avlP %s %s/%s' % (self.pfile, self.mount_dir, self.vfile))
            fp=open(self.mount_dir+"/1",'w+')
            process = subprocess.Popen(cmd, shell=True, stdout=fp)
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
                        print 'the size of file is %d' % (int((write_all * 100) / self.proctotal))
                    else:
                        write_old = 0
                        write_now = 0
                if process.poll() == 0:
                    break
            fp.close()
            os.system('rm -rf %s' % (self.mount_dir+"/1"))
            print 'finished'
        except:
            return -1


    def do_close(self):
        try:
            cmd = ('umount %s' % (self.mount_dir))
            ret = os.system(cmd)
            print "do close succeed"
            return ret
        except Exception,e:
            print e
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
        if self.op == 'write':
            ret = self.do_mount()
            if ret != 0:
                print
                "do mount failed"
            ret = self.do_mkdir()
            if ret != 0:
                print
                "do mkdir failed"
            ret = self.do_write()
            if ret != 0:
                print
                "do write failed"
            ret = self.do_close()
            if ret != 0:
                print
                "do close failed"
        else:
            pass