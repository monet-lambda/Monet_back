import os

def get_online_partitions():
    print('ERROR: Use monitoring hub instead')
    return []

def get_saveset_partitions():
    s = "/hist/Savesets"
    pathes = [os.path.join(s,x) for x in os.listdir(s)]
    dirs = list(filter(os.path.isdir, pathes))
    dirs = [d for d in dirs if 'ByRun' not in d]
    partitions = set([])
    for subdirs in map(os.listdir, dirs):
        partitions = partitions.union(subdirs)

    return sorted(list(partitions))