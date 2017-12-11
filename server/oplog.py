import six
import logging
logger = logging.getLogger('backup')

from db.sqlalchemy import api as db_api
from pattern import Singleton


six.add_metaclass(Singleton)
class EventManager(object):
    def __init__(self, conf):
        self.conf = conf
        self.db = db_api.get_database(conf)

    def log_event(self, context, message):
        oplog = {
            'user_id': context.get('user_id') if context.get('user_id') else 'system',
            'group_id': context.get('group_id') if context.get('group_id') else 'system',
            'username': context.get('username') if context.get('username') else 'system',
            'message': message,
        }
        self.db.oplog_create(context, oplog)


