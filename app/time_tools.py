from calendar import timegm
from datetime import datetime, timedelta
import pytz
import dateutil.parser


def get_current_time():
    return datetime.now(tz=pytz.utc)


def get_current_time_second():
    return timegm(get_current_time().utctimetuple())


def is_expired(date_second):
    return datetime.fromtimestamp(date_second, tz=pytz.utc) < get_current_time()


def get_days_before_current(num_of_days):
    days = timedelta(days=num_of_days)
    return get_current_time() - days


def to_second(date):
    return timegm(date.utctimetuple())


def get_remaining_time_in_second(start, duration):
    end = to_second(start) + duration
    if duration == -1:
        return duration
    if is_expired(end):
        return 0
    else:
        return end - get_current_time_second()
