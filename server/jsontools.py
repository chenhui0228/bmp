import cherrypy
import sys
import json
import exception
import datetime
from cherrypy._cpcompat import  json_encode
import six
import six.moves.xmlrpc_client as xmlrpclib
import warnings
import functools
import itertools
import inspect
import uuid
import ipaddress

import logging
logger = logging.getLogger('backup')

def safe_decode(text, incoming=None, errors='strict'):
    """Decodes incoming text/bytes string using `incoming` if they're not
       already unicode.
    :param incoming: Text's current encoding
    :param errors: Errors handling policy. See here for valid
        values http://docs.python.org/2/library/codecs.html
    :returns: text or a unicode `incoming` encoded
                representation of it.
    :raises TypeError: If text is not an instance of str
    """
    if not isinstance(text, (six.string_types, six.binary_type)):
        raise TypeError("%s can't be decoded" % type(text))

    if isinstance(text, six.text_type):
        return text

    if not incoming:
        incoming = (sys.stdin.encoding or
                    sys.getdefaultencoding())

    try:
        return text.decode(incoming, errors)
    except UnicodeDecodeError:
        # Note(flaper87) If we get here, it means that
        # sys.stdin.encoding / sys.getdefaultencoding
        # didn't return a suitable encoding to decode
        # text. This happens mostly when global LANG
        # var is not set correctly and there's no
        # default encoding. In this case, most likely
        # python will use ASCII or ANSI encoders as
        # default encodings but they won't be capable
        # of decoding non-ASCII characters.
        #
        # Also, UTF-8 is being used since it's an ASCII
        # extension.
        return text.decode('utf-8', errors)


def json_out(data, content_type='application/json', debug=False):

    if content_type is not None:
        if debug:
            logger.debug('Setting Content-Type to %s' %
                         content_type, 'TOOLS.JSON_OUT')
        cherrypy.response.headers['Content-Type'] = content_type

    return json_encode(data)

def json_out_decrator(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        v = f(*args, **kwargs)
        return json_out(v)
    return wrapper



_nasty_type_tests = [inspect.ismodule, inspect.isclass, inspect.ismethod,
                     inspect.isfunction, inspect.isgeneratorfunction,
                     inspect.isgenerator, inspect.istraceback, inspect.isframe,
                     inspect.iscode, inspect.isbuiltin, inspect.isroutine,
                     inspect.isabstract]

_simple_types = ((six.text_type,) + six.integer_types
                 + (type(None), bool, float))

_ISO8601_TIME_FORMAT_SUBSECOND = '%Y-%m-%dT%H:%M:%S.%f'
_ISO8601_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'
PERFECT_TIME_FORMAT = _ISO8601_TIME_FORMAT_SUBSECOND

_MAX_DATETIME_SEC = 59

def to_primitive(value, convert_instances=False, convert_datetime=True,
                 level=0, max_depth=3, encoding='utf-8',
                 fallback=None):
    """Convert a complex object into primitives.
    Handy for JSON serialization. We can optionally handle instances,
    but since this is a recursive function, we could have cyclical
    data structures.
    To handle cyclical data structures we could track the actual objects
    visited in a set, but not all objects are hashable. Instead we just
    track the depth of the object inspections and don't go too deep.
    Therefore, ``convert_instances=True`` is lossy ... be aware.
    If the object cannot be converted to primitive, it is returned unchanged
    if fallback is not set, return fallback(value) otherwise.
    .. versionchanged:: 2.22
       Added *fallback* parameter.
    .. versionchanged:: 1.3
       Support UUID encoding.
    .. versionchanged:: 1.6
       Dictionary keys are now also encoded.
    """
    orig_fallback = fallback
    if fallback is None:
        fallback = six.text_type

    # handle obvious types first - order of basic types determined by running
    # full tests on nova project, resulting in the following counts:
    # 572754 <type 'NoneType'>
    # 460353 <type 'int'>
    # 379632 <type 'unicode'>
    # 274610 <type 'str'>
    # 199918 <type 'dict'>
    # 114200 <type 'datetime.datetime'>
    #  51817 <type 'bool'>
    #  26164 <type 'list'>
    #   6491 <type 'float'>
    #    283 <type 'tuple'>
    #     19 <type 'long'>
    if isinstance(value, _simple_types):
        return value

    if isinstance(value, six.binary_type):
        if six.PY3:
            value = value.decode(encoding=encoding)
        return value

    # It's not clear why xmlrpclib created their own DateTime type, but
    # for our purposes, make it a datetime type which is explicitly
    # handled
    if isinstance(value, xmlrpclib.DateTime):
        value = datetime.datetime(*tuple(value.timetuple())[:6])

    if isinstance(value, datetime.datetime):
        if convert_datetime:
            return value.strftime(PERFECT_TIME_FORMAT)
        else:
            return value

    if isinstance(value, uuid.UUID):
        return six.text_type(value)

    if ipaddress and isinstance(value,
                                (ipaddress.IPv4Address,
                                 ipaddress.IPv6Address)):
        return six.text_type(value)

    # For exceptions, return the 'repr' of the exception object
    if isinstance(value, Exception):
        return repr(value)

    # value of itertools.count doesn't get caught by nasty_type_tests
    # and results in infinite loop when list(value) is called.
    if type(value) == itertools.count:
        return fallback(value)

    if any(test(value) for test in _nasty_type_tests):
        return fallback(value)

    # FIXME(vish): Workaround for LP bug 852095. Without this workaround,
    #              tests that raise an exception in a mocked method that
    #              has a @wrap_exception with a notifier will fail. If
    #              we up the dependency to 0.5.4 (when it is released) we
    #              can remove this workaround.
    if getattr(value, '__module__', None) == 'mox':
        return 'mock'

    if level > max_depth:
        return None

    # The try block may not be necessary after the class check above,
    # but just in case ...
    try:
        recursive = functools.partial(to_primitive,
                                      convert_instances=convert_instances,
                                      convert_datetime=convert_datetime,
                                      level=level,
                                      max_depth=max_depth,
                                      encoding=encoding,
                                      fallback=orig_fallback)
        if isinstance(value, dict):
            return {recursive(k): recursive(v)
                    for k, v in value.items()}
        elif hasattr(value, 'iteritems'):
            return recursive(dict(value.iteritems()), level=level + 1)
        # Python 3 does not have iteritems
        elif hasattr(value, 'items'):
            return recursive(dict(value.items()), level=level + 1)
        elif hasattr(value, '__iter__'):
            return list(map(recursive, value))
        elif convert_instances and hasattr(value, '__dict__'):
            # Likely an instance of something. Watch for cycles.
            # Ignore class member vars.
            return recursive(value.__dict__, level=level + 1)
    except TypeError:
        # Class objects are tricky since they may define something like
        # __iter__ defined but it isn't callable as list().
        return fallback(value)

    if orig_fallback is not None:
        return orig_fallback(value)

    # TODO(gcb) raise ValueError in version 3.0
    warnings.warn("Cannot convert %r to primitive, will raise ValueError "
                  "instead of warning in version 3.0" % (value,))
    return value

def loads(s, encoding='utf-8', **kwargs):
    """Deserialize ``s`` (a ``str`` or ``unicode`` instance containing a JSON
    :param s: string to deserialize
    :param encoding: encoding used to interpret the string
    :param kwargs: extra named parameters, please see documentation \
    of `json.loads <https://docs.python.org/2/library/json.html#basic-usage>`_
    :returns: python object
    """
    return json.loads(safe_decode(s, encoding), **kwargs)

def dumps(obj, default=to_primitive, **kwargs):
    """Serialize ``obj`` to a JSON formatted ``str``.
    :param obj: object to be serialized
    :param default: function that returns a serializable version of an object,
                    :func:`to_primitive` is used by default.
    :param kwargs: extra named parameters, please see documentation \
    of `json.dumps <https://docs.python.org/2/library/json.html#basic-usage>`_
    :returns: json formatted string
    Use dump_as_bytes() to ensure that the result type is ``bytes`` on Python 2
    and Python 3.
    """
    return json.dumps(obj, default=default, **kwargs)



def action_peek_json(body):
    """Determine action to invoke."""

    try:
        decoded = loads(body)
    except ValueError:
        msg = "cannot understand JSON"
        raise exception.MalformedRequestBody(reason=msg)
    # Make sure there's exactly one key...
    if len(decoded) != 1:
        msg = "too many body keys"
        raise exception.MalformedRequestBody(reason=msg)
    # Return the action and the decoded body...
    return list(decoded.keys())[0]