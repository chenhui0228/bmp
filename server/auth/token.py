import jwt
import  six
import  sys
from jwt import exceptions as jwtexc
sys.path.append('../')

from pattern import Singleton
from db.sqlalchemy import timeutils


import logging
logger = logging.getLogger('backup')


def genarate_token(payload, secret, headers=None):
    token = jwt.encode(payload, secret, algorithm='HS256', headers=headers)
    return token

def decode_token(token, secret, **kwargs):
    return jwt.decode(token, secret, **kwargs)

six.add_metaclass(Singleton)
class TokenManager(object):
    def __init__(self, conf={}):
        self.iss = conf.get('iss', 'SFBACKUP')
        self.exp = conf.get('exp', 3600)

    def build_payload(self, user):
        now = timeutils.utcnow_ts()
        exp = now + self.exp
        payload = {
            'iss': self.iss,
            'exp': exp,
            'aud': str(user)
        }
        return payload

    def check_token(self, tok, user_info):
        try:
            payload = decode_token(tok, user_info.key, audience=user_info.get('name'))
            iss = payload.get('iss')
            if iss != self.iss:
                logger.error('token is not issued by me')
                return False
            exp = payload.get('exp')
            now = timeutils.utcnow_ts()
            if now > exp:
                logger.error('token is expired')
                return False
            if user_info.name != payload.get('aud'):
                logger.error('token is for this user')
                return False
            return True
        except jwtexc.DecodeError as e:
            logger.error(e.message)
            return False
        except  jwtexc.ExpiredSignatureError as e:
            logger.error(e.message)
            return False