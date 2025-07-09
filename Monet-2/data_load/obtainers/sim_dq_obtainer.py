"""functions to load data for the SimDQ mode"""

###############################################################################
# (c) Copyright 2000-2022 CERN for the benefit of the LHCb Collaboration      #
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
import ROOT
import yaml
from flask import current_app, request
from MonitoringHub.api import default_api

from data_load.libhistograms import get_dict_from_object, get_batch_from_file
from .utilities import rand_str
from .base_obtainer import MonetDataObtainerBase


def get_PFN_Yml(yml):
    """
    Given a yml file returns PFN
    """
    with open(yml, "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        PFN = data["PFN"]
    return PFN


def event_type_path(repository, request_id, event_type):
    path = "/".join(
        [
            repository,
            request_id,
            event_type.rjust(8, "0"),
        ]
    )
    return path


class MonetSimDQDataObtainer(MonetDataObtainerBase):
    def __init__(self):
        super(MonetSimDQDataObtainer, self).__init__()
        if request.method == "GET":
            self.request_id = request.args.get("run_number", type=str).rjust(8, "0")
            self.event_type = request.args.get("event_type", type=str).rjust(8, "0")
            self.filename = request.args.get("sim_hist_file", type=str)
            self.histo_contained = None
        else:
            self.request_id = request.form.get("run_number", type=str).rjust(8, "0")
            self.event_type = request.form.get("event_type", type=str).rjust(8, "0")
            self.filename = request.form.get("sim_hist_file", type=str)
            self.histo_contained = json.loads(request.form["histos_contained"])
        if not self.valid_input:
            self.default_to_latest()
        self.data_files_used = []
        self.reference_files_used = []

    @property
    def valid_input(self):
        spdb = current_app.config["SIMPRODDB"]
        return (
            self.request_id in spdb.get_request_ids()
            and self.event_type in spdb.get_event_types(self.request_id)
            and self.filename in spdb.get_filenames(self.request_id, self.event_type)
        )

    def default_to_latest(self):
        spdb = current_app.config["SIMPRODDB"]
        self.request_id = spdb.get_request_ids()[-1]
        self.event_type = spdb.get_event_types(self.request_id)[0]
        self.filename = spdb.get_filenames(self.request_id, self.event_type)[0]

    @property
    def prod_info(self):
        spdb = current_app.config["SIMPRODDB"]
        return spdb.get_prod_info(self.request_id, self.event_type, self.filename)

    @staticmethod
    def tokenify(url):
        token = current_app.config["EOS_TOKEN"]
        return f"{url}?xrd.wantprot=unix&authz={token}"

    def get_histo_values(self, key_list, db_histos):
        filename = self.prod_info["PFN"]
        url = self.tokenify(filename)

        if self.path:
            hdb = current_app.config["HISTODB"]
            db_histos, _ = hdb.get_histos_in_path(self.path)
        else:
            db_histos = self.histo_contained

        # just to reduce calls to MonitoringHub
        non_analysis_keys = []
        ret = {}
        for h in db_histos:
            self.data_files_used.append(filename)

            if "analysis" not in h:
                key = (
                    h["name"],
                    h["taskname"],
                    h["display_options"],
                )  # as in renderer.logic.get_histograms
                non_analysis_keys += [key]
                logging.debug("No analysis to perform on " + h["name"])
                continue
            logging.debug("Performing analysis on " + h["name"])
            norm = h["display_options"].get("norm")
            prof = h["display_options"].get("prof")
            obj = self.get_analysis(h)
            ret[h["taskname"] + "/" + h["name"]] = get_dict_from_object(
                obj,
                objname=h["name"],
                onlinehist=h,
                scale_to_integral=norm,
                profile=prof,
            )

        ret.update(get_batch_from_file(url, non_analysis_keys))
        return ret, self.data_files_used

    def get_ref_values(self, key_list, db_histos, **kwargs):
        filename = self.prod_info["refPFN"]
        url = self.tokenify(filename)
        return get_batch_from_file(url, key_list, **kwargs), [filename]

    def get_analysis(self, onlinehist):
        entity, task = (onlinehist["name"], onlinehist["taskname"])
        partition = self.prod_info["PFN"]

        with MonitoringHub.ApiClient(
            current_app.config.get("MONHUB_CONFIG", None)
        ) as api_client:
            api_instance = default_api.DefaultApi(api_client)
            source = "simulation"

            analysis_type = ""
            analysis_inputs = []
            hist_index = -1
            """
            this section defines the parameters that are read in from the yml file in histoYML and are passed to Monitoring hub. There in the
            api/automaticanalysis.py the parameters are passed to the AutomaticAnalysis repository through the call_aaserver function. The
            endpoint of this function is defined in AutomaticAnalysis/openapi/aa_api.yml.
            """
            if onlinehist.get("analysis", None):
                analysis_type = "{0}/{1}".format(
                    "analyze", onlinehist["analysis"].get("type", "")
                )
                if analysis_type == "":
                    print("Error: no analysis type defined")
                    self.reference_files_used.append("No reference")
                    return None
                analysis_inputs = [
                    n["name"] for n in onlinehist["analysis"].get("inputs", [])
                ]
                if not analysis_inputs:
                    print("Error: no input histogram defined")
                    self.reference_files_used.append("No reference")
                    return None
                """
                In case more analysis_parameters are needed for future analysis they could be added to the ymls and passed in the following manner:
                onlinehist.get("analysis").pop("type")
                onlinehist.get("analysis").pop("inputs")
                o_map = onlinehist.get("analysis")
                for k in o_map.keys():
                    analysis_parameters.append("{0}:{1}".format(k, o_map[k]))
                """
            # insert case elif onlinehist.get("compare_to_ref", None):

            api_response = api_instance.api_hub_get_data(
                source,
                partition.replace("/", ","),
                task,
                entity,
                analysis_type=analysis_type,
                analysis_inputs=analysis_inputs,
                hist_index=hist_index,
                # more arguments can be set by modifying default_api.py (see https://gitlab.cern.ch/lhcb-monitoring/MonitoringHubClient/-/blob/master/MonitoringHub/api/default_api.py)
            )
            res = api_response  # .get()
            file_to_write = rand_str(n=2) + ".json"
            filename = (
                current_app.config.get("JSON_FILES_PATH", "/hist/Monet/ROOT/")
                + file_to_write
            )
            if res["hub_type"] == "ROOT_JSON":
                if analysis_type == "":
                    try:
                        with open(filename, "wb") as outfile:
                            outfile.write(bz2.decompress(b64decode(res["hub_data"])))
                    except Exception:
                        file_to_write = "_"

                    obj = (
                        ROOT.TBufferJSON.ConvertFromJSON(
                            bz2.decompress(b64decode(res["hub_data"]))
                        ),
                        file_to_write,
                    )
                    with ROOT.TFile( filename.replace('.json','.root'), 'RECREATE' ) as root_file:
                        root_file.WriteObject(obj[0], "MonetHisto")
                else:
                    try:
                        with open(filename, "wb") as outfile:
                            outfile.write(
                                bz2.decompress(b64decode(res["hub_data"]["histo"]))
                            )
                    except Exception:
                        file_to_write = "_"

                    obj = (
                        (
                            ROOT.TBufferJSON.ConvertFromJSON(
                                bz2.decompress(b64decode(res["hub_data"]["histo"]))
                            ),
                            res["hub_data"]["results"],
                        ),
                        file_to_write,
                    )
            if not obj:
                print("Error in converting ROOT JSON to ROOT object")
            return obj
