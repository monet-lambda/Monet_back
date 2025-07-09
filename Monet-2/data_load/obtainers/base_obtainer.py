"""Base class for histogram data obtainers"""

###############################################################################
# (c) Copyright 2000-2020 CERN for the benefit of the LHCb Collaboration      #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
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
