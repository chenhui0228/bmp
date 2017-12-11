import six
import re

class BackupException(Exception):
    message = "An unknown exception occurred."
    def __init__(self, message=None, **kwargs):
        if not message:
            message = self.message % kwargs
        elif isinstance(message, Exception):
            message = six.text_type(message)

        if re.match('.*[^\.]\.\.$', message):
            message = message[:-1]
        self.msg = message
        super(BackupException, self).__init__(message)


class MalformedRequestBody(Exception):
    message = "Could not find config at %(path)s."



class Duplicated(Exception):
    pass