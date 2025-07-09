"""functions to load data for the history mode"""

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

from .history_obtainer import MonetHistoryDataObtainer

class RunComparisonDataObtainer(MonetHistoryDataObtainer):
    """get comparison data from a given run number"""

    def __init__(self):
        super().__init__()
        self.history_type = "Run"
        try:
            if request.method == "GET":
                self.run_number = int(request.form["compare_with_run"])
            else:
                self.run_number = int(request.form["compare_with_run"])
        except TypeError:
            self.run_number = 0
        except ValueError:
            self.run_number = 0
