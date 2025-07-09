"""Obtainer class for data in online mode"""

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
from time import time

from flask import current_app, request

import interfaces.rundb
from data_load.libhistograms import get_dict_from_object, get_rootobj, get_scaling_kwargs

from .base_obtainer import MonetDataObtainerBase
from interfaces.monitoringhub import find_reference_file

from interfaces.monitoringhub import monitoringhub_get_histogram_object

class MonetOnlineDataObtainerBase(MonetDataObtainerBase):
    """Class to access online data"""

    def __init__(self, trend_duration=600):
        super(MonetOnlineDataObtainerBase, self).__init__()
        if request.method == "GET":
            self.partition = request.args.get("partition")
        else:
            self.partition = request.form.get("partition")
        self.data_files_used = []
        self.reference_files_used = []
        self.trend_duration = int(trend_duration)
        self._time_range = None
        self._rundb_info = None
        self._latest_run = ""
        self._latest_fill = ""

    @property
    def time_range(self):
        """Get time range for data request"""
        if not self._time_range:
            now = int(time())
            self._time_range = (now - self.trend_duration, now)
        return self._time_range

    @property
    def latest_rundb_info(self):
        """Get info about latest run from run db"""
        if not self._rundb_info:
            latest_run = interfaces.rundb.get_latest_run_number(
                offline=False, partition=self.partition
            )
            self._rundb_info = interfaces.rundb.get_rundb_info(latest_run)
            self._latest_run = latest_run
            if self._rundb_info:
                self._latest_fill = self._rundb_info.get("fillid", "")
        return self._rundb_info

    def get_histo_values(self, key_list, db_histos):
        monhub_config = current_app.config["MONHUB_CONFIG"]
        dim_dns_node  = current_app.config["DIM_DNS_NODE"] 
        def loader(h, json_file=""):
            res = monitoringhub_get_histogram_object(
                monhub_config,
                dim_dns_node,
                h,
                partition=self.partition,
                json_file=json_file,
                run=self._latest_run,
                fill=self._latest_fill,
                mu=-1,
            )
            logging.debug("Object for %s is %s", self.path, res)
            return res

        ret = {}

        for h in db_histos:
            obj, file_used = get_rootobj(h, loader, self.time_range)
            self.data_files_used.append(file_used)

            norm = h["display_options"].get("norm")
            prof = h["display_options"].get("prof")

            ret[h["taskname"] + "/" + h["name"]] = get_dict_from_object(
                obj,
                objname=h["name"],
                onlinehist=h,
                scale_to_integral=norm,
                profile=prof,
            )

        return ret, self.data_files_used

    def _load_reference_object(self, h, json_file=""):
        obj, path = find_reference_file(
            f"{h['taskname']}/{h['name']}",
            h,
            self.latest_rundb_info,
            json_file=json_file,
        )

        if not obj:
            self.reference_files_used.append("No reference")
            return None

        self.reference_files_used.append(path)
        return obj

    def get_ref_values(self, key_list, db_histos, **kwargs):
        ret = {}
        for h in db_histos:
            if "TH2D" in kwargs["scale_dict"][h["taskname"] + "/" + h["name"]][
                "data"
            ].get("key_class", ""):
                self.reference_files_used.append("No reference")
                continue

            if (
                h["taskname"].startswith("WinCC/")
                or h["taskname"].startswith("WinCCCounter/")
                or h["taskname"].startswith("prometheus")
                or h["taskname"].startswith("CounterPrometheus")
            ):
                self.reference_files_used.append("No reference")
                continue

            ref_norm = h["display_options"].get("ref")
            if "/" in h["name"]:
                hid = h["name"].split("/", 1)[1]
            else:
                hid = h["name"]

            obj = get_rootobj(
                h,
                self._load_reference_object,
                self.time_range,
                rundb_info=self.latest_rundb_info,
                json_file=kwargs["scale_dict"][h["taskname"] + "/" + h["name"]].get(
                    "json_name", "_"
                ),
            )

            scaling_kwargs = get_scaling_kwargs(
                h["taskname"] + "/" + h["name"], ref_norm, kwargs["scale_dict"]
            )

            ret[h["taskname"] + "/" + h["name"]] = get_dict_from_object(
                obj,
                objname=hid,
                onlinehist=h,
                profile=h["display_options"].get("prof", False),
                **scaling_kwargs,
            )
        return ret, self.reference_files_used
