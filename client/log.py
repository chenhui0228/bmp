#!/usr/bin/env python
#coding:utf-8

import os
from datetime import *
import logging
import logging.handlers as handlers
import subprocess


class MyRotatingFileHandler(handlers.BaseRotatingHandler):

    def __init__(self, filename, filePath, saveTime, mode='a', maxBytes=0, encoding=None, delay=False):
        if maxBytes > 0:
            mode = 'a'
        handlers.BaseRotatingHandler.__init__(
            self, filename, mode, encoding, delay)
        self.maxBytes = maxBytes
        self.filePath = filePath
        self.saveTime = saveTime

    def emit(self, record):
        """
        Emit a record.

        Output the record to the file, catering for rollover as described
        in doRollover().
        """
        try:
            if self.shouldRollover(record):
                self.doRollover()
            self.removeLogBeforeSevenDays()
            logging.FileHandler.emit(self, record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    def cleanLogBeforeSevenDays(self):
        """
        clean log
        """
        files = list(os.listdir(self.filePath))
        for i in range(len(files)):
            file_date = os.path.getmtime(self.filePath + files[i])
            # time1 = datetime.datetime.fromtimestamp(file_date).strftime('%Y-%m-%d')
            curr_date = time.time()
            diff_date = (curr_date - file_date) / 60 / 60 / 24
            if diff_date >= int(self.saveTime):
                try:
                    os.remove(self.filePath + files[i])
                except Exception as e:
                    raise e
        pass

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        nowtime = datetime.now()
        dfn = self.baseFilename + "-" + nowtime.strftime("%Y%m%d%H%M")
        n = 0
        while os.path.exists(dfn):
            n += 1
            dfn = dfn + "-" + str(n)
        if os.path.exists(self.baseFilename):
            # os.rename(self.baseFilename, dfn)
            p = subprocess.Popen(
                'tar zcf ' + dfn + '.tar.gz ' + self.baseFilename,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            outdata, errdata = p.communicate()
            if len(errdata):
                raise RuntimeError('unable to get tar log file')
        self.stream = self._open()

    def shouldRollover(self, record):
        """
        Determine if rollover should occur.

        Basically, see if the supplied record would cause the file to exceed
        the size limit we have.
        """
        if self.stream is None:                 # delay was set...
            self.stream = self._open()
        if self.maxBytes > 0:                   # are we rolling over?
            msg = "%s\n" % self.format(record)
            # due to non-posix-compliant Windows feature
            self.stream.seek(0, 2)
            if self.stream.tell() + len(msg) >= self.maxBytes:
                return 1
        return 0


class MyLogging(object):
    """this class use to define some
     functions for our own to use"""

    def __init__(self, log_level, log_file_name, log_file_path, log_save_time, logger_name=__name__):
        self.level = int(log_level)
        self.log_file_name = log_file_name
        self.log_file_path = log_file_path
        self.log_save_time = log_save_time
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(self.level)
        self._formatter = logging.Formatter(
            '[%(asctime)s] [%(threadName)s.%(funcName)s] *%(levelname)s*: %(message)s')

        # logging.basicConfig(
        # level=self.level, format='[%(asctime)s] [%(name)s] [%(levelname)s]:
        # %(message)s')
        self.addRotatingFileHandler(self._logger, 100 * 1024 * 1024)

    @property
    def log_level(self):
        return self.level

    def set_loglevel(self, level=10):
        self.level = level
        self._logger.setLevel(level)
        return

    @property
    def logger(self):
        return self._logger

    def addRotatingFileHandler(self, log, maxBytes):
        rfh = MyRotatingFileHandler(
            self.log_file_name, self.log_file_name, self.log_save_time, maxBytes=maxBytes)
        rfh.setLevel(self.level)
        rfh.setFormatter(self._formatter)
        log.addHandler(rfh)
        return

    def addStreamHandle(self, log):
        ch = logging.StreamHandler()
        ch.setLevel(self.level)
        log.addHandler(ch)
        return