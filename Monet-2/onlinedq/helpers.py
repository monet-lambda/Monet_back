import re
from collections import defaultdict, namedtuple

Task = namedtuple('Task', ['partition', 'machine', 'name'])


class TaskNotFoundException(Exception):
    pass


class HistNotFoundException(Exception):
    pass


def match_task(t):
    return re.match(r'(\w+)_([\w\d]+)_(\w+)', t)


def match_task_list(ts):
    return [match_task(str(t)) for t in ts]


def convert_task_list(ts):
    return [Task(*m.groups()) for m in match_task_list(ts) if m]


def filter_partition(ts, partition='LHCb'):
    return [t for t in ts if t.partition == partition]


def to_dict(ts):
    return {t.name: t for t in ts}


def to_dim_location(t):
    return '{}_{}_{}'.format(*t)


def path_to_task_and_name(path):
    parts = path.split('/')
    task = parts[0]
    name = '/'.join(parts[1:])
    return task, name
