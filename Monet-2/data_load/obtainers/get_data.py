""" "Init module for data obtainers"""

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
import logging

from .alarm_obtainer import MonetAlarmDataObtainer
from .history_interval_obtainer import MonetHistoryIntervalDataObtainer
from .history_obtainer import MonetHistoryDataObtainer
from .offline_obtainer import MonetOfflineDataObtainer
from .online_obtainer import MonetOnlineDataObtainerBase
from .sim_dq_obtainer import MonetSimDQDataObtainer
from .trend_obtainer import MonetTrendDataObtainer
from .run_comparison_obtainer import RunComparisonDataObtainer
from .fill_comparison_obtainer import FillComparisonDataObtainer

OBTAINERS = {
    "sim_dq": MonetSimDQDataObtainer,
    "offline": MonetOfflineDataObtainer,
    "online": MonetOnlineDataObtainerBase,
    "history": MonetHistoryDataObtainer,
    "history_interval": MonetHistoryIntervalDataObtainer,
    "alarm": MonetAlarmDataObtainer,
    "trends": MonetTrendDataObtainer,
    "custom": None,
}


def get_data_for_request(
    key_list, histos_contained, need_reference, datasource, trend_duration, compare_with_run, compare_with_fill
):
    """returns data depending on the mode"""
    assert datasource in list(OBTAINERS), "Unknown data source"
    logging.debug("Data source: " + datasource)

    obtainer_class = OBTAINERS[datasource]
    if datasource == "online":
        obtainer = obtainer_class(trend_duration=trend_duration)
    else:
        obtainer = obtainer_class()

    data_files, ref_files, comparison_files = [], [], []
    data, reference, comparison = {}, {}, {}
    data, data_files = obtainer.get_histo_values(key_list, histos_contained)
    if need_reference:
        reference, ref_files = obtainer.get_ref_values(
            key_list, histos_contained, scale_dict=data
        )

    if (compare_with_run!=-1):
        comparison, comparison_files = RunComparisonDataObtainer().get_histo_values(key_list, histos_contained)
    elif (compare_with_fill!=-1):
        comparison, comparison_files = FillComparisonDataObtainer().get_histo_values(key_list, histos_contained)

    return data, reference, comparison, data_files, ref_files, comparison_files
