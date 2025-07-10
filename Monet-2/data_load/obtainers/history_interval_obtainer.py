"""functions to load data for the history interval mode"""


from datetime import datetime, timedelta
from time import mktime

from flask import request

from interfaces.monitoringhub import monitoringhub_get_histogram_in_savesets

from .history_obtainer import MonetHistoryDataObtainer


class MonetHistoryIntervalDataObtainer(MonetHistoryDataObtainer):
    def __init__(self):
        super(MonetHistoryIntervalDataObtainer, self).__init__()
        self.interval_begin = request.form.get("interval_begin")
        self.interval_size = request.form.get("interval_size")
        self.partition = request.form.get("partition")
        self.data_files_used = []
        self.reference_files_used = []

    @property
    def time_range(self):
        return list(int(mktime(dt.timetuple())) for dt in self.time_range_datetime)

    @property
    def time_range_datetime(self):
        if hasattr(self, "_time_range_datetime"):
            return self._time_range_datetime
        start_time = datetime.strptime(self.interval_begin, "%m/%d/%Y %H:%M")
        diff = datetime.strptime(self.interval_size, "%H:%M") - datetime(1900, 1, 1)
        end_time = start_time + diff
        self._time_range_datetime = (
            start_time,
            end_time,
        )

        return self._time_range_datetime

    def get_histo_values(self, key_list, db_histos):
        return super(MonetHistoryIntervalDataObtainer, self).get_histo_values(
            key_list, db_histos
        )


    def _get_obj_savesets(self, db_hist, json_file=""):
        return monitoringhub_get_histogram_in_savesets(
            db_hist,
            partition=self.partition,
            history_type=self.history_type,
            run_number=-1,
            run_list=[],
            run_starttime=self.time_range_datetime[0],
            run_endtime=self.time_range_datetime[1],
            task=db_hist["taskname"],
            key=db_hist["name"],
            fallback_key=db_hist.get("name_fallback", None),
            json_file=json_file)
