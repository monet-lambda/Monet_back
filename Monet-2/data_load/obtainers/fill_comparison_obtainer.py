"""functions to load data for the comparison mode"""


from flask import request

from .history_obtainer import MonetHistoryDataObtainer

class FillComparisonDataObtainer(MonetHistoryDataObtainer):
    """get comparison data from a given run number"""

    def __init__(self):
        super().__init__()
        self.history_type = "Fill"
        try:
            if request.method == "GET":
                self.run_number = int(request.form["compare_with_fill"])
            else:
                self.run_number = int(request.form["compare_with_fill"])
        except TypeError:
            self.run_number = 0
        except ValueError:
            self.run_number = 0
