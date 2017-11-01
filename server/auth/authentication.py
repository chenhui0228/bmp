import sys

import auth_basic
import token

import logging
logger = logging.getLogger('backup')

def check_login(f):
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)
    return wrapper


def auth(request):
    return auth_basic.basic_auth()

def check_token(token, user):
    pass


