import sys
import six
sys.path.append('../')

from pattern import Singleton

def check_permission(userinfo):
    pass



@six.add_metaclass(Singleton)
class APIManager(object):
    def __init__(self):
        pass




def add_api(collection):
    def wrapper(f):
        func_name = f.__name__

    return wrapper