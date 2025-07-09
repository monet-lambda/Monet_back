"""Class to obtain data for trends"""

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
import bz2
import json
import logging
import random
import string
from base64 import b64decode

import MonitoringHub
import urllib3
from flask import current_app, request
from MonitoringHub.api import default_api

from .base_obtainer import MonetDataObtainerBase


class MonetTrendDataObtainer(MonetDataObtainerBase):
    """Class to read data for the trend DQ mode"""

    def __init__(self):
        super().__init__()
        try:
            if request.method == "GET":
                self.run_number_min = int(request.args.get("run_number_min"))
            else:
                self.run_number_min = int(request.form.get("run_number_min"))
            self.type = "Run number"
        except (TypeError, ValueError):
            self.run_number_min = None
        try:
            if request.method == "GET":
                self.run_number_max = int(request.args.get("run_number_max"))
            else:
                self.run_number_max = int(request.form.get("run_number_max"))
            self.type = "Run number"
        except (TypeError, ValueError):
            self.run_number_max = None
        try:
            if request.method == "GET":
                self.fill_number_min = int(request.args.get("fill_number_min"))
            else:
                self.fill_number_min = int(request.form.get("fill_number_min"))
            self.type = "Fill number"
        except (TypeError, ValueError):
            self.fill_number_min = None
        try:
            if request.method == "GET":
                self.fill_number_max = int(request.args.get("fill_number_max"))
            else:
                self.fill_number_max = int(request.form.get("fill_number_max"))
            self.type = "Fill number"
        except (TypeError, ValueError):
            self.fill_number_max = None

    def get_histo_values(self, key_list, db_histos):
        ret = {}
        for h in db_histos:
            with MonitoringHub.ApiClient(
                current_app.config.get("MONHUB_CONFIG", None)
            ) as api_client:
                api_instance = default_api.DefaultApi(api_client)
                source = "trends"
                run_min = self.run_number_min if self.run_number_min else -1
                run_max = self.run_number_max if self.run_number_max else -1
                fill_min = self.fill_number_min if self.fill_number_min else -1
                fill_max = self.fill_number_max if self.fill_number_max else -1
                bad_runs_set = h.get("badrun_file", [])
                try:
                    api_response = api_instance.api_hub_get_data(
                        source,
                        "LHCb",
                        h["taskname"],
                        h["name"] + "::::" + h["value"],
                        run=run_min,
                        run_max=run_max,
                        fill=fill_min,
                        fill_max=fill_max,
                        _request_timeout=30,
                    )
                    the_data = json.loads(
                        bz2.decompress(b64decode(api_response.to_dict()))
                    )
                    ret[h["taskname"] + "/" + h["name"]] = {
                        "success": True,
                        "not_found": False,
                        "json_name": None,
                        "data": {
                            "key_data": {
                                "title": h.get("title", h["name"]),
                                "axis_titles": [self.type, h["value"]],
                                "binning": [
                                    i[0]
                                    for i in the_data
                                    if str(i[0]) not in bad_runs_set
                                ],
                                "values": [
                                    i for i in the_data if str(i[0]) not in bad_runs_set
                                ],
                                "uncertainties": [
                                    (0, 0)
                                    for i in the_data
                                    if str(i[0]) not in bad_runs_set
                                ],
                            },
                            "key_class": "TrendDQ",
                        },
                    }
                    if len(the_data) == 0:
                        ret[h["taskname"] + "/" + h["name"]]["data"]["key_data"][
                            "binning"
                        ] = [0, 1]
                        ret[h["taskname"] + "/" + h["name"]]["data"]["key_data"][
                            "title"
                        ] = "NO DATA FOUND IN THAT RANGE"
                    ## Now get the errors
                    if h.get("error", None):
                        api_response = api_instance.api_hub_get_data(
                            source,
                            "LHCb",
                            h["taskname"],
                            h["name"] + "::::" + h["error"],
                            run=run_min,
                            run_max=run_max,
                            fill=fill_min,
                            fill_max=fill_max,
                            _request_timeout=30,
                        )
                        the_data = json.loads(
                            bz2.decompress(b64decode(api_response.to_dict()))
                        )
                        ret[h["taskname"] + "/" + h["name"]]["data"]["key_data"][
                            "uncertainties"
                        ] = [
                            (i[1], i[1])
                            for i in the_data
                            if str(i[0]) not in bad_runs_set
                        ]

                except MonitoringHub.ApiException as e:
                    if e.status == 404:
                        print("Trend not found")
                    else:
                        print(
                            f"Exception when calling DefaultApi->api_hub_get_data: {e}"
                        )
                    ret[h["taskname"] + "/" + h["name"]] = {
                        "not_found": True,
                        "success": False,
                        "data": {"key_data": {"title": h.get("title", h["name"])}},
                    }
                except urllib3.exceptions.MaxRetryError:
                    logging.error("Max retry error: %s, %s, %s, %s", source)
                    return None
                except TypeError:
                    logging.error("Bad data received for trend plots")
                    ret[h["taskname"] + "/" + h["name"]] = {
                        "success": True,
                        "not_found": True,
                        "json_name": None,
                        "data": {
                            "key_data": {
                                "title": h.get("title", h["name"]),
                                "axis_titles": ["not found", "not found"],
                                "binning": [],
                                "values": [],
                                "uncertainties": [],
                            },
                            "key_class": "TrendDQ",
                        },
                    }
                    return ret, "None"
                except:
                    logging.error("Timeout")
                    raise
        return ret, ["Trend"]
