#!/usr/bin/env python
# coding:utf-8
from datetime import *
from SocketServer import BaseRequestHandler, ThreadingTCPServer, ThreadingUDPServer
import threading
import socket  # 套接字
import Queue
import ConfigParser



version = "1.0.0"
up_time = datetime.now()
local_host = socket.gethostname
local_ip = socket.gethostbyname(socket.gethostname())
q = Queue.Queue()
con=threading.Condition()


def do_put(info):
    global q
    con.acquire()
    q.put_nowait(info)
    con.notify()
    con.release()



class Performance:
    def __init__(self):
        print "Performance init"
        self.perfs = {}
        self.worklist = []
        self.hashmap = {}

    def register(self, worker):
        self.worklist.append(worker)
        # self.

    def unregist(self, worker):
        hashid = worker.hashid
        self.hashmap['hashid'] = worker


class TCPServer(BaseRequestHandler):
    def handle(self):
        #address, pid = self.client_address
        # while True:
        if True:
            # data = self.request.recv(4096)
            data = self.request.recv(4096)
            if len(data) > 0:
                #print "address=", address, "pid",pid,"recv data:", data
                cur_thread = threading.current_thread()
                response = '{}:{}'.format(cur_thread.ident, data)
                # self.request.sendall('server response!')
                do_put(response)
                #self.request.sendto(response, self.client_address)
                #print "address=", address, "recv data:", data
                self.finish()


class UDPServer(BaseRequestHandler):
    def handle(self):
        address, pid = self.client_address
        # while True:
        if True:
            # data = self.request.recv(4096)
            data = self.request[0]
            if len(data) > 0:
                #print "address=", address, "recv data:", data
                cur_thread = threading.current_thread()
                response = '{}:{}'.format(cur_thread.ident, data)
                # self.request.sendall('server response!')
                self.request[1].sendto(response, self.client_address)
                self.finish()


class Message:
    def __init__(self, ms_type,port):
        global q
        # self.locahost=socket.gethostname
        #mylogger = MyLogging()
        hostname = str(socket.gethostname())
        ip = socket.gethostbyname(hostname)
        self.local_ip = ip
        self.port = int(port)
        self.send_ip=ip
        self.recv_state = "stop"
        self.send_status = "stop"
        self.ms_type = ms_type
        self.updserver = ''
        self.udpclient = ''
        self.tcpclient = ''
        self.server_thread = []
        self.q = q
        #self.log =mylogger

    def get_queue(self):
        #self.log.logger.info('get msg from queue')
        return self.q.get_nowait()

    def start_server(self):   # 监听
        global con
        self.con=con
        ADDR = (self.local_ip, self.port)
        #self.log.logger.info('start TCP listen server')
        # init server:
        if self.ms_type == "tcp":
            try:
                self.tcpserver = ThreadingTCPServer(ADDR, TCPServer)
                # init client:
                # self.updclient =socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                server_thread = threading.Thread(target=self.tcpserver.serve_forever)
                server_thread.daemon = True
                server_thread.start()
                self.server_thread.append(server_thread)
            except Exception ,e:
                #self.log.logger.error('start TCP listen server failed %s'%e)
                pass
        # start server
        self.send_status = "start"
        # self.udpserver.serve_forever()


        # self.state="start"

    def udpsend(self, info):
        if not info:
            return
        if info.has_key('data'):
            # ms=info['data']
            if info.has_key('addr'):
                address = info['addr']
                try:
                    self.tcpclient = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.tcpclient.sendto(info['data'], address)
                except Exception, e:
                    #self.log.logger.error('UDP send failed %s'%e)
                    return e
            else:
                #print "error:data or address not exist ?"
                #self.log.logger.error("error:data or address not exist!")
                return "error:data or address not exist!"
        else:
            #print "error:data or address not exist ?"
            #self.log.logger.error("error:data or address not exist!")
            return "error:data or address not exist!"
        return 0

    def tcpsend(self, info):
        if not info:
            return
        ms = ''
        address = ''
        #print 'use TCP send %s'%str(info)
        #self.log.logger.info('use TCP send %s'%str(info))
        if info.has_key('data'):
            ms = info['data']
            if info.has_key('addr'):
                #print info
                try:
                    self.tcpclient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.tcpclient.connect(info['addr'])
                    self.tcpclient.send(ms)
                    #server_reply = self.tcpclient.recv(1024)
                    #print server_reply
                    self.tcpclient.close()
                except Exception, e:
                    #self.log.logger.error('UDP send failed %s' % e)
                    return e
            else:
                #print "error:data or address not exist ?"
                #self.log.logger.error("error:data or address not exist!")
                return "error:data or address not exist!"
        else:
            #print "error:data or address not exist ?"
            #self.log.logger.error("error:data or address not exist!")
            return "error:data or address not exist!"
        return 0

    def issued(self,info):    # server发给client
        if self.ms_type == "tcp":
            ret=self.tcpsend(info)
        if self.ms_type == "udp":
            ret=self.udpsend(info)
        return ret

    def send(self, data):       # client发给server
        if self.ms_type == "tcp":
            info={}
            info['data']=str(data)
            info['addr']=(self.send_ip,self.port)
            ret=self.tcpsend(info)
        if self.ms_type == "udp":
            ret=self.udpsend(info)
        return ret

    def closeall(self):
        if self.tcpclient:
            #self.log.logger.info('tcpclient close')
            self.tcpclient.close()

            # server.shutdown()



