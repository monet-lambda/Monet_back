"""Utility functions to draw histograms"""


from .draw_1d import render1d
from .draw_2d import render2d
from .draw_bars import render_bars
from .draw_none import render_none
from .draw_table import renderTable, renderCountersTable


def histo_draw(*args, **kwargs):
    """Draw the various types of histograms"""
    histo_data = kwargs["histo_data"]
    if not histo_data["success"]:
        raise TypeError(f"Data obtaining error: {histo_data}")
    if histo_data["not_found"]:
        return render_none(*args, **kwargs)

    if histo_data["data"]["key_class"] in set(
        [
            "TH1D",
            "TProfile",
            "TH1F",
            "TEfficiency",
            "MonetTrend",
            "TGraph",
            "TGraphErrors",
            "TrendDQ",
        ]
    ):
        if histo_data["data"]["key_class"] in set(["MonetTrend"]):
            kwargs["trend"] = True
            kwargs["ref_data"] = None
            kwargs["comparison_data"] = None
        if histo_data["data"]["key_class"] in set(["TrendDQ"]):
            kwargs["trenddq"] = True
            kwargs["ref_data"] = None
            kwargs["comparison_data"] = None
        return render1d(*args, **kwargs)

    if histo_data["data"]["key_class"] in set(
        ["TH2D", "TH2F", "TProfile2D", "MonetTrend2D"]
    ):
        return render2d(*args, **kwargs)
    if histo_data["data"]["key_class"] == "MonetCounter":
        if kwargs["draw_params"].get("bars", None):
            return render_bars(*args, **kwargs)
        return renderTable(*args, **kwargs)

    if (histo_data['data']['key_class'] == 'CountersValues' and\
        histo_data['data']['key_title'] == 'CountersHistogram'):
        return renderCountersTable(*args, **kwargs)

    return render_none(*args, **kwargs)
