import datetime
import calendar


def utcnow_ts(microsecond=True):
    now = utcnow()
    timestamp = calendar.timegm(now.timetuple())

    if microsecond:
        timestamp *= 1000
        timestamp += int(now.microsecond) / 1000

    return timestamp



def utcnow():
    return datetime.datetime.utcnow()
