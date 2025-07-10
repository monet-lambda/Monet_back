"""Module with utility functions"""


import random
import string
from datetime import datetime
from time import mktime
from typing import Any


def rand_str(chars=string.ascii_lowercase, n=10):
    """returns a random file name of n characters"""
    return "".join(random.choice(chars) for _ in range(n))

def convert_time(time_str):
    """Converts "2015-11-21T09:45:58" to timestamp"""
    if not time_str:
        return 0

    try:
        dt_format = "%Y-%m-%dT%H:%M:%S%z"
        dt = datetime.strptime(time_str, dt_format)
    except ValueError:
        # try another format
        dt_format = "%Y-%m-%dT%H:%M:%S"
        dt = datetime.strptime(time_str, dt_format)
    return int(mktime(dt.timetuple()))
