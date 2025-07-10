"""Blueprint for Trend mode"""


import logging
from math import pi

from bokeh.embed import components
from bokeh.models import (
    BoxZoomTool,
    HoverTool,
    PrintfTickFormatter,
    ResetTool,
    SaveTool,
    WheelZoomTool,
)
from bokeh.plotting import figure
from flask import Blueprint, current_app, jsonify, render_template, request
from flask.wrappers import Response

from .._auth import get_info, requires_auth
from .._user_settings import UserSettings

settings = UserSettings()

FLAG_COLOR = [
    ("OK", "green"),
    ("BAD", "red"),
    ("UNCHECKED", "gray"),
    ("CONDITIONAL", "orange"),
]


@requires_auth
def index() -> str:
    """Main page

    Returns:
        str: HTML string
    """
    dqdb = current_app.config["DQDB"]
    settings.set_options_file(get_info("cern_uid"))

    return render_template(
        "trends.html",
        properties=dqdb.getDataProperties()[::-1],
        PROJECTNAME="DQ Trends",
        USERNAME=get_info("preferred_username"),
        FULLNAME=get_info("name"),
    )


def get_dqdb_fills_data(value_to_plot: str, min_fill: int, max_fill: int) -> dict:
    """Get per fill data from the DQDB

    Args:
        value_to_plot (str): name of the quantity to plot
        min_fill (int): lower edge of the fill interval
        max_fill (int): upper edge of the fill interval

    Returns:
        dict: data to plot
    """
    dqdb = current_app.config["DQDB"]
    dqdb_response = dqdb.getFillsPropertyValueWithErr(
        value_to_plot, fillLow=min_fill, fillHigh=max_fill
    )
    assert dqdb_response["OK"] == 0, "DQDB failure"

    return {
        "any": {
            "color": "blue",
            "values": dqdb_response["values"],
        }
    }


def get_dqdb_runs_data(
    value_to_plot: str, min_run: int, max_run: int, run_flag: str
) -> dict:
    """Get per run data from the DQDB

    Args:
        value_to_plot (str): name of the quantity to plot
        min_run (int): lower edge of the run interval
        max_run (int): upper edge of the run interval
        run_flag (str): keep only this DQ flag

    Returns:
        dict: values to plot
    """
    dqdb = current_app.config["DQDB"]

    if run_flag != "ANY":
        dqdb_response = dqdb.getRunsPropertyValueWithErr(
            value_to_plot, runLow=min_run, runHigh=max_run, dqFlag=run_flag
        )
        assert dqdb_response["OK"] == 0, "DQDB failure"

        return {
            run_flag: {
                "color": "blue",
                "values": dqdb_response["values"],
            }
        }

    ret = {}

    for flag, color in FLAG_COLOR:
        dqdb_response = dqdb.getRunsPropertyValueWithErr(
            value_to_plot, runLow=min_run, runHigh=max_run, dqFlag=flag
        )
        assert dqdb_response["OK"] == 0, "DQDB failure"

        ret[flag] = {
            "color": color,
            "values": dqdb_response["values"],
        }

    return ret


def draw_on_plot(plot, data: dict, flag: str) -> None:
    """Draw data on plot

    Args:
        plot (_type_): plot
        data (dict): data to plot
        flag (str): text for the legend
    """
    runs = []
    values = []
    errors = []

    for run, val in sorted(data["values"].items()):
        runs.append(run)
        value, error = val[0], val[1]

        values.append(value)
        errors.append(error)

    plot.square(runs, values, color=data["color"], size=7, line_alpha=0, legend=flag)

    # plot errors
    err_xs = []
    err_ys = []

    for x, y, yerr in zip(runs, values, errors):
        err_xs.append((x, x))
        err_ys.append((y - yerr, y + yerr))

    # plot them
    # plot.multi_line(err_xs, err_ys, color=data['color'])
    for i in range(len(err_xs)):
        plot.line(err_xs[i], err_ys[i], color=data["color"])


@requires_auth
def load_values() -> Response:
    """Load values from the DQDB.
    The arguments are taken from the HTTP request through the
    request.args variable
    """
    try:
        min_run = int(request.args.get("min_run"))
        max_run = int(request.args.get("max_run"))
        value_to_plot = str(request.args.get("dq_trend"))
        run_tag = str(request.args.get("run_tag"))
        use_fills = str(request.args.get("run_or_fill")) == "Fills"

        if use_fills:
            data = get_dqdb_fills_data(value_to_plot, min_run, max_run)
        else:
            data = get_dqdb_runs_data(value_to_plot, min_run, max_run, run_tag)

        print((value_to_plot, min_run, max_run, run_tag))
        print(data)

        runs = []
        for v in list(data.values()):
            runs.extend(list(v["values"].keys()))
        runs = sorted(runs)

        hover = HoverTool(
            tooltips=[("Fill Number" if use_fills else "Run Number", "$x")]
        )
        box_zoom = BoxZoomTool()
        plot = figure(
            x_axis_label="Fill Number" if use_fills else "Run Number",
            y_axis_label=value_to_plot,
            x_range=runs,
            tools=[hover, box_zoom, ResetTool(), WheelZoomTool(), SaveTool()],
        )
        plot.toolbar.active_drag = box_zoom
        plot.xaxis.major_label_orientation = pi / 3
        plot.xaxis[0].formatter = PrintfTickFormatter(format="%s")

        for run_flag, data_for_flag in list(data.items()):
            draw_on_plot(plot, data_for_flag, run_flag)

        script, div = components(plot, wrap_script=False)

        return jsonify({"script": script, "div": div})
    except Exception as e:
        logging.error(e)
        return jsonify({"error": str(e)}), 500


trends_bp = Blueprint(
    "trends_bp",
    __name__,
    template_folder="../../templates/trends",
    static_folder="../../static",
)

trends_bp.add_url_rule("/", "index", index)
trends_bp.add_url_rule("/values", "load_values", load_values)
