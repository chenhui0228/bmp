#!/usr/bin/env python
# coding:utf-8
import sys
import os
import time
from daemon import Daemon
from  log import MyLogging
import ConfigParser

def create_dir(path):
    cp = ConfigParser.ConfigParser()
    cp.read('/etc/SFbackup/client.conf')
    usually_concurrent=int(cp.get('client', 'usually_concurrent'))
    immediately_concurrent = int(cp.get('client', 'immediately_concurrent'))
    if not os.path.exists(path):  # 创建挂载的目录
        os.makedirs(path)
    for i in range(usually_concurrent+immediately_concurrent):
        new_path=os.path.join(path,str(i))
        if not os.path.exists(new_path):
            try:
                os.mkdir(new_path)
            except:
                pass

    del_path=os.path.join(path,'del')
    if not os.path.exists(del_path):
        try:
            os.mkdir(del_path)
        except:
            pass

    recover_path=os.path.join(path,'recover')
    if not os.path.exists(recover_path):
        try:
            os.mkdir(recover_path)
        except:
            pass

if __name__ == '__main__':
    if not os.path.exists('/etc/SFbackup/client.conf'):
        print "conf is lose"
        sys.exit(1)
    cp = ConfigParser.ConfigParser()
    cp.read('/etc/SFbackup/client.conf')
    log_level = cp.get('client', 'log_level')
    log_file_dir = cp.get('client', 'log_file_dir')
    work_dir=cp.get('client', 'mount_dir')
    create_dir(work_dir)
    if not os.path.exists(log_file_dir):
        os.makedirs(log_file_dir)
    log_file_name=log_file_dir+'client.log'
    mylogger = MyLogging(log_level,log_file_name)   # 初始化log
    ip = ''
    cip = ''
    if not os.path.exists('/var/run/bak/'):
        os.mkdir('/var/run/bak/')
    if 'start' == sys.argv[1]:
        #print cip
        daemon = Daemon('/var/run/bak/watch_process.pid',  mylogger, ip, cip)
        daemon.start()
    elif  'restart' == sys.argv[1]:

        daemon = Daemon('/var/run/bak/watch_process.pid', mylogger, ip, cip)
        daemon.restart()
    elif 'stop' == sys.argv[1]:

        daemon = Daemon('/var/run/bak/watch_process.pid',  mylogger, ip, cip,)
        time.sleep(0.2)
        daemon.stop()
        sys.exit(1)
    sys.exit(0)