from calendar import timegm
from datetime import datetime
import pytz
import dateutil.parser


def get_current_time():
    return datetime.now(tz=pytz.utc)


def get_current_time_iso():
    return get_current_time().isoformat()


def get_current_time_second():
    return timegm(get_current_time().utctimetuple())


def is_expired(date_second):
    return datetime.fromtimestamp(date_second, tz=pytz.utc) < get_current_time()


def to_second(date_iso):
    return timegm(dateutil.parser.parse(date_iso).utctimetuple())


def get_remaining_time_in_second(start_iso, duration):
    end = to_second(start_iso) + duration
    if duration == -1:
        return duration
    if is_expired(end):
        return 0
    else:
        return end - get_current_time_second()
