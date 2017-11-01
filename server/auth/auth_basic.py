import sys
import binascii
import cherrypy
from cherrypy._cpcompat import base64_decode

sys.path.append('../')

from db.sqlalchemy import api as db_api

def check_password(user, password):
    user_info = db_api.get_user_by_name(user)
    p = user_info.password
    return p and p == password or False

def basic_auth(req):
    if req.method == 'POST':
        raise cherrypy.HTTPRedirect('/')
    elif req.method == 'GET':
        auth_header = req.headers.get('authorization')
        scheme, params = auth_header.split(' ', 1)
        if scheme.lower() == 'basic':
            username, password = base64_decode(params).split(':', 1)
            print cherrypy.request.method, username, password
        raise cherrypy.HTTPRedirect('/')

