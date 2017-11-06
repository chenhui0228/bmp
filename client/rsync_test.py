#!/usr/bin/env python

import os
import time
import subprocess
size=4189598250
write_all=0
write_old=0
write_now=0
#f = os.popen("rsync -avlP /usr/include /mnt/sdb 2>&1")
cmd="rsync -avlP /zyt/test /data/"
fp=open('/tmp/1','w+')
process = subprocess.Popen(cmd, shell=True,stdout = fp)
while True:
        lines = fp.readlines()
        for line in lines:
            s=line
            if len(s)<=1:
                continue
            list=s.split()
            if list[0].isdigit():
                write_old=write_now
                write_now=int(list[0])
                write_all=write_all+(write_now-write_old)
                print 'the size of file is %d'%(int((write_all*100)/size))
            else:
                write_old = 0
                write_now = 0
        if process.poll()==0:
            break
        #fp.truncate()
fp.close()
print 'finished'

