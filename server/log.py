import logging
from logging import config as logconfig

def setup(conf):
    configure_file = '/etc/backupserver/logging.conf'
    if isinstance(conf.get('log'), dict):
        logconf = conf.get('log')
        configure_file = logconf.get('conf')
    print configure_file
    logconfig.fileConfig(configure_file)


if __name__ == '__main__':

    loggger_root = logging.getLogger()
    logger = logging.getLogger('backup')

    loggger_root.debug('debug message')
    loggger_root.info('info message')
    loggger_root.warn('warn message')
    loggger_root.error('error message')
    loggger_root.critical('critical message')

    logger.debug('debug message')
    logger.info('info message')
    logger.warn('warn message')
    logger.error('error message')
    logger.critical('critical message')

