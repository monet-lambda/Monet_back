

from datetime import datetime

from pytz import timezone


class MonetTrend(object):
    def __init__(self, data, start_time, end_time):
        eur_tz = timezone("Europe/Paris")
        utc_tz = timezone("UTC")
        try:
            self.data = [
                (
                    datetime.strptime(d[0], "%Y-%m-%d %H:%M:%S")
                    .replace(tzinfo=utc_tz)
                    .astimezone(eur_tz),
                    d[1],
                )
                for d in data
            ]
        except Exception:
            self.data = []
        self.start_time = start_time
        self.end_time = end_time

    def ClassName(self):
        return "MonetTrend"

    def GetTitle(self):
        return ""

    def GetName(self):
        return ""


class MonetTrend2D(object):
    def __init__(self, data, start_time, end_time):
        self.data = data
        self.start_time = start_time
        self.end_time = end_time

    def ClassName(self):
        return "MonetTrend2D"

    def GetTitle(self):
        return ""

    def GetName(self):
        return ""


class MonetCounter(object):
    def __init__(self, data, time):
        self.data = data
        self.time = time

    def ClassName(self):
        return "MonetCounter"

    def GetTitle(self):
        return ""

    def GetName(self):
        return ""
