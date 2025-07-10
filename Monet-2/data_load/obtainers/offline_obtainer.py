"""Class to obtain data for Offline DQ"""


from flask import request

import interfaces.rundb
from data_load.libhistograms import get_dict_from_object, get_rootobj, get_scaling_kwargs
from interfaces.monitoringhub import find_reference_file, monitoringhub_get_histogram_in_savesets

from .base_obtainer import MonetDataObtainerBase
from .utilities import (
    convert_time,
)


class MonetOfflineDataObtainer(MonetDataObtainerBase):
    """Class to read data for the offline DQ mode"""

    def __init__(self):
        super().__init__()
        try:
            if request.method == "GET":
                self.run_number = int(request.args.get("run_number"))
            else:
                self.run_number = int(request.form.get("run_number"))
        except TypeError:
            self.run_number = 0
        except ValueError:
            self.run_number = 0
        if request.method == "GET":
            self.partition = request.args.get("partition")
        else:
            self.partition = request.form.get("partition")
        self.data_files_used = []
        self.reference_files_used = []
        self._rundb_info = None
        self._time_range = None


    @property
    def rundb_info(self):
        """returns the rundb information"""
        if not self._rundb_info:
            self._rundb_info = interfaces.rundb.get_rundb_info(self.run_number)
        return self._rundb_info

    @property
    def time_range(self):
        """returns time range of the query"""
        if not self._time_range:
            self._time_range = (
                convert_time(self.rundb_info["starttime"]),
                convert_time(self.rundb_info["endtime"]),
            )
        return self._time_range


    def get_histo_values(self, key_list, db_histos):
        ret = {}
        for h in db_histos:
            norm = h["display_options"].get("norm")
            prof = h["display_options"].get("prof")

            obj, file_used = get_rootobj(
                h, self._get_obj_savesets, self.time_range, rundb_info=self.rundb_info
            )
            self.data_files_used.append(file_used)

            ret[h["taskname"] + "/" + h["name"]] = get_dict_from_object(
                obj,
                objname=h["name"],
                onlinehist=h,
                scale_to_integral=norm,
                profile=prof,
            )
        return ret, self.data_files_used


    def _get_obj_savesets(self, db_hist, json_file=""):
        if self.run_number == 0:
            return None

        return monitoringhub_get_histogram_in_savesets(
            db_hist,
            partition="LHCb",
            history_type="Run",
            run_number=self.run_number,
            run_list=self._rundb_info.get("runs",[]),
            run_starttime=self._rundb_info["starttime"],
            run_endtime=self._rundb_info["endtime"],
            task=db_hist["taskname"],
            key=db_hist["name"],
            fallback_key=db_hist.get("name_fallback", None),
            json_file=json_file)


    def _load_reference_object(self, h, json_file=""):
        obj, path = find_reference_file(
            f"{h['taskname']}/{h['name']}",
            h,
            self.rundb_info,
            "/hist/OfflineDQ",
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
                rundb_info=self.rundb_info,
                json_file=kwargs["scale_dict"][h["taskname"] + "/" + h["name"]].get(
                    "json_name", "_"
                ),
            )

            scaling_kwargs = get_scaling_kwargs(
                h["taskname"] + "/" + h["name"], ref_norm, kwargs["scale_dict"]
            )

            ret[h["taskname"] + "/" + h["name"]] = get_dict_from_object(
                obj, objname=hid, onlinehist=h, **scaling_kwargs
            )
        return ret, self.reference_files_used


