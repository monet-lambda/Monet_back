"""Base class for histogram data obtainers"""


from flask import request


class MonetDataObtainerBase:
    """Base class for data obtainers"""

    def __init__(self):
        self.dqdb = None
        self.path = request.args.get("path")

    def get_histo_values(self, key_list):
        """returns the histogram with data"""
        raise NotImplementedError

    def get_ref_values(self, key_list, **kwargs):
        """returns the reference histograms"""
        raise NotImplementedError
