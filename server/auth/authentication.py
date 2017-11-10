import sys
from cherrypy import HTTPError
import cherrypy
import auth_basic
import token
from cherrypy import NotFound
sys.path.append('../')
from db.sqlalchemy import uuidutils
from db.sqlalchemy.api import get_database
import logging
logger = logging.getLogger('backup')

def generate_salt():
    return uuidutils.generate_uuid(False)

PY3 = sys.version_info[0] == 3
if PY3:
    text_type = str
    binary_type = bytes
else:
    text_type = unicode
    binary_type = str

string_types = (text_type, binary_type)
def check_token(auth_header, user):
    if not user:
        logger.error('user should not be none')
        raise HTTPError(401, 'user should not be none')

    if isinstance(user, list):
        user = user[0]

    if isinstance(user, string_types) :
        db = get_database(None)
        try:
            user = db.get_user_by_name(user)
        except NotFound:
            logger.error('user {0} is not found'.format(user))
            raise HTTPError(401, 'user {0} is not found'.format(user))

    username = user.name

    if not auth_header:
        logger.error('no token')
        raise HTTPError(401, 'token for user {0} is not found'.format(username))
    tm = token.TokenManager()
    scheme, tok = auth_header.split(' ', 1)
    if scheme == 'Bearer':
        valid = tm.check_token(tok, user)
        if not valid:
            logger.error('invalid token for user : {0}'.format(username))
            raise HTTPError(401, 'invalid token')

def check_login(f):
    def wrapper(*args, **kwargs):
        logger.debug('login args : %s'%kwargs)
        request = cherrypy.serving.request
        auth_header = request.headers.get('authorization')
        user = kwargs.get('user')
        check_token(auth_header, user)
        return f(*args, **kwargs)
    return wrapper

superrole = None
superuser = None

def init(conf):
    global superrole
    global superuser
    token_conf = conf.get('token')
    if not token_conf:
        token_conf = {'exp': 3600}
    token.TokenManager(token_conf)
    db = get_database(conf)
    superrole = db.role_get_by_name('superrole')
    if not superrole:
        role = {
            "name": 'superrole',
            "description": "this role has super power, take it carefully ! "
        }

        superrole = db.role_create(role)

    superuser = db.get_super_user(superrole.id)
    password = uuidutils.generate_uuid(False)
    if not superuser:
        user = {
            'name':'root',
            'password': password,
            'role_id': superrole.id
        }
        superuser = db.create_user(user)
        logger.error('root password is : {0}, you should change it at  the first time'.format(password))

def login(request, **kwargs):
    if request.method == 'POST':
        auth_header = request.headers.get('authorization')
        db = get_database(None)
        username = kwargs.get('user')
        if username:
            try:
                user_info = db.get_user_by_name(username)
            except NotFound:
                logger.error('user {0} is not found'.format(username))
                raise HTTPError(401, 'user {0} is not found'.format(username))
        else:
            logger.error('no username')
            raise HTTPError(400, 'please input the username')

        logger.info('user {0} is trying to log in'.format(username))
        if auth_header:
            try:
                check_token(auth_header, user_info)
            except HTTPError:
                raise
        else:
            tm = token.TokenManager()
            password = kwargs.get('password')
            valid = auth_basic.verify_user(user_info, username, password)
            if valid:
                logger.info('user {0} is logged in successful'.format(username))
                payload = tm.build_payload(username)
                tok = token.genarate_token(payload, user_info.key)
                role = user_info.role
                rolename = ''
                if role:
                    rolename = role.name
                return {'token': tok, 'role':rolename}
            raise HTTPError(401, 'user {0} password is not right'.format(username))


    elif cherrypy.request.method == 'OPTIONS':
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST, PUT, DELETE'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'content-type'
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        return
    else:
        raise HTTPError(400, 'Hey, do not do this! ')







