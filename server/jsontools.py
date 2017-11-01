import cherrypy
from cherrypy._cpcompat import  json_encode

import logging
logger = logging.getLogger('backup')


def json_out(data, content_type='application/json', debug=False):

    if content_type is not None:
        if debug:
            logger.debug('Setting Content-Type to %s' %
                         content_type, 'TOOLS.JSON_OUT')
        cherrypy.response.headers['Content-Type'] = content_type

    return json_encode(data)

def json_out_decrator(f):
    def wrapper(*args, **kwargs):
        v = f(*args, **kwargs)
        return json_out(v)
    return wrapper
