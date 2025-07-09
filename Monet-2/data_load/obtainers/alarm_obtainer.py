"""Class to get data for alarms"""

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
import copy
import logging

import ROOT
from flask import current_app, request

from data_load.libhistograms import get_dict_from_object, try_get_object, get_rootobj, get_batch_from_file

from .offline_obtainer import MonetOfflineDataObtainer


class MonetAlarmDataObtainer(MonetOfflineDataObtainer):
    """Obtain data for histograms triggering alarms"""

    def __init__(self) -> None:
        super(MonetAlarmDataObtainer, self).__init__()
        self.aldb = current_app.config["ALARMS"]
        self.alarm = self.aldb.get_alarm(int(request.args.get("alarm_id")))
        self.filename = ""

    def get_histo_values(
        self, key_list: list[str]
    ) -> tuple[dict, list[str]]:
        """Returns the list of histograms affected by alarms

        Args:
            key_list (list[str]): list of keys

        Returns:
            tuple[dict, list[str]]: histograms affected
        """        
        self.filename = self.alarm["file"]

        logging.debug("Loading keys `%s` for alarm: %s", str(key_list), str(self.alarm))

        ana_hists, normal_hists = [], []
        for element in key_list:
            if element[1].endswith("_ANALYSIS"):
                ana_hists.append(element)
            else:
                normal_hists.append(element)

        ret = {}
        ret.update(get_batch_from_file(self.filename, normal_hists))
        ret.update(self._load_ana_hists(ana_hists))

        return ret, [self.filename]

    def _load_ana_hists(self, hists: list) -> dict[str,dict]:
        """Load histograms that triggered alarms

        Args:
            hists (list): list of histograms

        Returns:
            dict[str,dict]: histograms that triggered alarms
        """        
        hdb = current_app.config["ONLINE_HIST_DB"]()
        ret = {}

        for name, task, opts in hists:
            h = hdb.histogram_for_id(name)
            obj, omalib = get_rootobj(h, self._get_obj_alarm_file, (0, 0))

            ret[h.identifier] = get_dict_from_object(
                obj, objname=h.identifier, onlinehist=h
            )

        del hdb._hdb
        del hdb
        return ret

    def _get_obj_alarm_file(self, onlinehist):
        identifier = onlinehist.identifier
        task, key = identifier.split("/", 1)

        logging.debug("Trying to load key `%s` from file: `%s`", key, self.filename)
        f = ROOT.TFile(self.filename) if self.filename else ROOT.TFile()
        assert not f.IsZombie()
        obj = copy.deepcopy(try_get_object(f, key))
        f.Close()

        if obj:
            logging.debug("Loaded `%s`", obj)
            return obj
        return obj

    def get_ref_values(self, key_list, **kwargs):
        return {}, []
