import uuid


def generate_uuid(dashed=True):
    """Creates a random uuid string.
    :param dashed: Generate uuid with dashes or not
    :type dashed: bool
    :returns: string
    """
    if dashed:
        return str(uuid.uuid4())
    return uuid.uuid4().hex


def _format_uuid_string(string):
    return (string.replace('urn:', '')
                  .replace('uuid:', '')
                  .strip('{}')
                  .replace('-', '')
                  .lower())


def is_uuid_like(val):
    """Returns validation of a value as a UUID.
    :param val: Value to verify
    :type val: string
    :returns: bool
    .. versionchanged:: 1.1.1
       Support non-lowercase UUIDs.
    """
    try:
        return str(uuid.UUID(val)).replace('-', '') == _format_uuid_string(val)
    except (TypeError, ValueError, AttributeError):
        return False