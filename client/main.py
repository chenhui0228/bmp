#!/usr/bin/env python
# coding:utf-8
import sys
import os
import time
from daemon import Daemon
from  log import MyLogging
import ConfigParser


def create_dir( path ):
    """
    Create a working directory
    """
    cp = ConfigParser.ConfigParser()
    cp.read('/etc/fbmp/client.conf')
    workpool_size = int(cp.get('client', 'workpool_size'))
    immediate_workpool_size = int(cp.get('client', 'immediate_workpool_size'))
    if not os.path.exists(path):  # 创建挂载的目录
        os.makedirs(path)
    for i in range(workpool_size + immediate_workpool_size):
        new_path = os.path.join(path, str(i))
        if not os.path.exists(new_path):
            try:
                os.mkdir(new_path)
            except:
                pass

    del_path = os.path.join(path, 'delete')
    if not os.path.exists(del_path):
        try:
            os.mkdir(del_path)
        except:
            pass

    recover_path = os.path.join(path, 'recover')
    if not os.path.exists(recover_path):
        try:
            os.mkdir(recover_path)
        except:
            pass


def get_version():
    file = os.path.dirname(os.path.realpath(__file__)) + '/version'
    openfile = open(file, 'r')
    version = openfile.readline()
    openfile.close()
    return version.strip()


if __name__ == '__main__':
    conf_dir = '/etc/fbmp/client.conf'
    if not os.path.exists(conf_dir):
        print "conf is lose, you should copy the client.conf to /etc/fbmp"
        sys.exit(1)
    cp = ConfigParser.ConfigParser()
    cp.read('/etc/fbmp/client.conf')
    log_level = cp.get('client', 'log_level')
    log_file_dir = cp.get('client', 'log_file_dir')
    log_save_time = cp.get('client', 'log_save_time')
    work_dir = cp.get('client', 'work_dir')
    pid_dir = cp.get('client', 'pid_dir')
    pid_file = pid_dir + 'client.pid'
    create_dir(work_dir)
    if not os.path.exists(log_file_dir):
        os.makedirs(log_file_dir)
    log_file_name = log_file_dir + 'client.log'
    mylogger = MyLogging(log_level, log_file_name, log_file_dir, log_save_time)  # 初始化log
    version = get_version()
    if not os.path.exists(pid_dir):
        os.mkdir(pid_dir)
    if 'start' == sys.argv[1]:
        daemon = Daemon(pid_file, mylogger, version)
        daemon.start()
    elif 'stop' == sys.argv[1]:
        daemon = Daemon(pid_file, mylogger, version)
        daemon.stop()
    elif 'version' == sys.argv[1]:
        print version
    else:
        usage_tip = '''
        Usage:
            python main.py <command> 
        Commands:
            start:start client
                        
            stop: stop client

            version: get client's version

            help: get help info
        '''
        print usage_tip
    sys.exit(0)
