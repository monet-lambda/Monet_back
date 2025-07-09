import traceback
import time
import datetime

import ROOT
import numpy as np
## from Gaucho import HistTaskWrapper

from .helpers import *
import logging

PARTITION = 'LHCb'
DIM_DNS_NAME = 'mon01'

from builtins import object
import ROOT

# ROOT "typedefs"
StdString = ROOT.std.string
VectorOfString = ROOT.vector('string')
VectorOfTObjectPtr = ROOT.vector('TObject*')

class HistTaskWrapper:
    """ This class wraps around the HistTask C++ class from Gaucho.
    It exposes all of the methods in a pythonic way.
    """
    @classmethod
    def _task_list(cls, dns):
        """ Obtains a task list from DIM as `std::vector<std::string>`.
        This is only internally by the classmethod `task_list` which returns a
        Python list of Python strings.
        """
        locations = VectorOfString()
        err = ROOT.Online.HistTask.TaskList(dns, locations)
        if err != 0:
            raise Exception('Could not obtain task list from DIM.')
        return locations

    @classmethod
    def task_list(cls, dns):
        """ Obtains task list from DIM. """
        return [t for t in cls._task_list(dns)]

    def __init__(self, task_name, dns):
        """ Sets up a new wrapper object for a given task name and dns that can
        then obtain the histograms associated with the task.
        """
        self._dns = dns
        self._task_name = task_name
        self._hist_task = ROOT.Online.HistTask(task_name, dns)
        # These need to be set, otherwise movefromdim segfaults
        ROOT.TH1D.SetDefaultSumw2()
        ROOT.TH2D.SetDefaultSumw2()
        ROOT.TProfile.SetDefaultSumw2()

    def _directory(self):
        """ Obtains the histogram names for the task associated with this
        instance from DIM and returns a `std::vector<std::string>`.
        This is used internally by the `directory` method which unwraps the
        result in a Python list of Python strings.
        """
        dir_ = VectorOfString()
        err = self._hist_task.Directory(dir_)
        if err != 0:
            raise Exception('Could not obtain directory from DIM.')
        return dir_

    def directory(self):
        """ Obtains the histogram names for the task associated with this
        instance.
        """
        return [n for n in self._directory()]

    def _histograms(self, histogram_names=None):
        """ Obtains histograms of given names for task associated with this
        instance as a `std::vector<TObject*>`.
        This is used internally by the `histograms` method which unwraps the
        result into a Python list of the correct type (`TH1D`, `TH2D`, `TH3D`,
        or `TProfile`).
        """ 
        if histogram_names is None:
            histogram_names = self._directory()
        hists = VectorOfTObjectPtr()
        err = self._hist_task.Histos(histogram_names, hists)
        for h in hists:
            ROOT.SetOwnership(h,True)
        res = [ t for t in hists ]

        if err != 0:
            raise Exception('Could not obtain histograms from DIM.')
        return res

    def histograms(self, histogram_names=None):
        """ Obtains histograms of given names for task associated with this
        instance.

        Input is a Python list of Python strings.
        """
        hist_names_vec = None
        if histogram_names is not None:
            # Convert list of strings to std::vector<std::string>
            hist_names_vec = VectorOfString()
            for hn in histogram_names:
                hist_names_vec.push_back(StdString(hn))
        hlist = self._histograms(hist_names_vec)
        return hlist

def get_histogram(histo, partition=PARTITION, dns=DIM_DNS_NAME):
    try:
        task = histo['taskname']
        name = histo['name']
        ts = to_dict(
            filter_partition(
                convert_task_list(
                    HistTaskWrapper.task_list(dns)
                ),
                partition
            )
        )
        logging.debug(f"For {dns} found HistTask ts is {ts}")
        tname = ts.get(task)
        logging.debug(f"For {name} found HistTask tname is {tname}")
        if tname is None:
            raise TaskNotFoundException()
        ht = HistTaskWrapper(to_dim_location(tname), dns)
        logging.debug(f"For {name} found HistTask {ht}")
        hs = ht.histograms([name])
        logging.debug(f"For {name} found histograms {hs}")
        if len(hs) != 1:
            raise HistNotFoundException()
        return hs[0]
    except BaseException as e:
        logging.error("Got exception loading {} from partition={} and dns={}: {}".format(name, partition, dns, e))
        return None

def tree():
    return defaultdict(tree)

def directory_tree(paths):
    """Return a tree, as a dictionary, from a list of paths.

    Example usage:
        folder_tree(['/a/b', '/a/f', '/foo/bar'])
        {'a': {'b': {}, 'f': {}}, 'foo': {'bar': {}}}
        folder_tree(['/a/b', '/a/f', '/foo/bar'], True)
        {'a': {'b': {}, 'f': {}}, 'foo': {'bar': {}}}
    Keyword arguments:
    paths -- List of paths as strings, with preceeding slash
    """
    t = tree()
    for path in paths:
        branch = t
        for folder in path[1:].split('/'):
            branch = branch[folder]
    return t


def extract_name_and_tag_from_path(path):
    pat = re.compile(r'TrendHistograms/([\ \w\d]+)/([\ \d\w:-]+)')
    mat = pat.match(path)
    if not mat:
        return None
    else:
        return mat.groups()

def resolve_analysis_histogram(histogram):
    """Execute the analysis task associated with this histogram."""
    alg_sources = ROOT.vector('TH1*')()
    alg_param_vals = ROOT.vector('float')()
    for source in histogram.analysis_source_histograms:
        alg_sources.push_back(get_histogram(source.identifier))
    for param in histogram.analysis_parameter_values:
        alg_param_vals.push_back(param)
    out_name = ROOT.string()
    out_title = ROOT.string()
    omalib, alg = histogram._hdb.omalib_algorithm(histogram.analysis_algorithm)
    # `exec` is a reserved word in Python so we can't use obj.exec directly
    robj = getattr(alg, 'exec')(
        alg_sources,
        alg_param_vals,
        out_name,
        out_title
    )
    del omalib
    return robj


def data_for_object(obj,filename):
    """Return a dictionary representing the data inside the object."""
    obj_class = obj.ClassName()
    d = {}
    d['type'] = obj_class[1:]
    d['numberEntries'] = obj.GetEntries()
    d['integral'] = obj.Integral()
    d['mean'] = "{:.4g}".format(obj.GetMean())
    d['RMS'] = "{:.4g}".format(obj.GetRMS())
    d['skewness'] = "{:.4g}".format(obj.GetSkewness())
    d['values'] = list()
    d['uncertainties'] = list()
    d['nbins'] = ""
    MyDisplayName = obj.GetName().split("/")[-1]
    d['key_name'] = MyDisplayName
    xaxis = obj.GetXaxis()
    yaxis = obj.GetYaxis()
    d['axis_titles'] = (xaxis.GetTitle(), yaxis.GetTitle())
    d['run_number'] = filename#.split("-")[1]
    if obj_class[0:3] == 'TH1' or obj_class[0:3] == 'TPr':
        d['binning'] =  list()
        nbins = xaxis.GetNbins()
        d['nbins'] = nbins
        for i in range(nbins):
            d['values'].append(obj.GetBinContent(i))
            d['binning'].append((xaxis.GetBinLowEdge(i), xaxis.GetBinUpEdge(i)))
            d['uncertainties'].append((obj.GetBinErrorLow(i), obj.GetBinErrorUp(i)))
    if obj_class[0:3] == 'TH2':
       #Same logic for 2D Histograms
        xnbins = xaxis.GetNbins()
        ynbins = yaxis.GetNbins()
        d['xbinning'] = np.array( [[xaxis.GetBinLowEdge(i), xaxis.GetBinUpEdge(i)]
                         for i in range(xnbins)] )
        d['ybinning'] = np.array( [[yaxis.GetBinLowEdge(i), yaxis.GetBinUpEdge(i)]
                         for i in range(ynbins)] )
        for i in range(xnbins):
            for j in range(ynbins):
                d['values'].append(obj.GetBinContent(i,j))
                d['uncertainties'].append((obj.GetBinErrorLow(i,j), obj.GetBinErrorUp(i,j)))
    return d


def histogram_data_generator(result):
    """ Dispatch on the type of the histogram and obtain the corresponding
    data.

    vh: VisibleHistogram
    h:  Histogram
    hs: HistogramSet
    """
    tho = TrendHistogramObtainer()
    for h in result:
        vh = h.visible_histogram
        hid = h.identifier
        pd = vh.pad_dimensions
        do = vh.display_options
        if vh.parent is not None:
            parent_pad_id = vh.parent.pad_id
        else:
            parent_pad_id = None
        hist = {
            'name': h.name,
            'task': h.task,
            'algorithm': h.algorithm,
            'description': h.description,
            'documentation': h.documentation,
            'identifier': hid,
            'pad': vh.pad_id,
            'parent_pad': parent_pad_id,
            # Pad (width, height)
            'size': (pd.x.max - pd.x.min, pd.y.max - pd.y.min),
            # Bottom left corner of pad
            'center': (pd.x.min, pd.y.min),
            # Use dict.get to protect against missing attributes
            'axis_titles': (
                do.get('label_x', ''),
                do.get('label_y', ''),
                do.get('label_z', '')
            ),
            # log{x,y,z} are stored as '1' in the DB, so convert to a boolean
            'log': (
                bool(do.get('logx', False)),
                bool(do.get('logy', False)),
                bool(do.get('logz', False))
            ),
        }
        if h.task == 'TrendHistograms':
            # TODO Use correct start and end time, and support partitions
            hist['type'] = 'trend'
            hist['axis_titles'] = ('', 'Rate', '')
            two_days_ago = datetime.datetime.now() - datetime.timedelta(days=2)
            # Get the trend from two days ago until now
            hist['data'] = tho.get_trend_histogram(
                hid,
                start_time=int(time.mktime(two_days_ago.timetuple()))
            )
        elif h.task.endswith('_ANALYSIS'):
            obj = data_for_object(resolve_analysis_histogram(h), 'f.root')
            hist.update(obj)
        else:
            try:
                obj = data_for_object(get_histogram(hid), 'f.root')
                hist.update(obj)
            except Exception as e:
                traceback.print_exc()
                continue

        yield hist


def get_histogram_object(onlinehist, partition="LHCb"):
    try:
        if onlinehist["taskname"] == 'TrendHistograms':
            raise Exception("Could not handle trend histograms yet!")
        elif onlinehist["taskname"].endswith('_ANALYSIS'):
            raise Exception("Could not handle analysis histograms yet!") # TODO resolve it (put data in HistoYML)
            # return resolve_analysis_histogram(onlinehist)
        else:
            logging.debug("Trying to load {} from mon01".format(onlinehist['name']))
            result = get_histogram(onlinehist, partition=partition, dns="mon01")

            if not result:
                logging.debug("Got nil result for mon01, retrying cald07; hid={}".format(onlinehist['name']))
                result = get_histogram(onlinehist, partition=partition, dns="cald07")

            return result
    except BaseException as e:
        logging.error(f"Got exception loading {onlinehist['name']}: {e}")
        return None

