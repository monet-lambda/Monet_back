"""Rendered functions to draw histograms as bars"""
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

from math import ceil

from bokeh.models import ColumnDataSource, Range1d
from bokeh.models.tools import HoverTool
from bokeh.plotting import figure


def render_bars(
    histodb_hist,
    histo_data,
    draw_params,
    ref_data=None,
    highlight=None,
    motherplot=None,
    is_mother=False,
    extratext="",
):
    """Draw histograms as bars"""
    data = histo_data["data"]["key_data"]
    title = (
        draw_params.get("legendtext", "")
        or draw_params.get("showtitle", "")
        or data.get("title", "")
    )
    to_print = 0

    try:
        to_print = data["values"][-1][1]
    except IndexError:
        pass

    if not motherplot:
        title = (
            draw_params.get("legendtext", "")
            or draw_params.get("showtitle", "")
            or data.get("title", "")
        )
        ymax = 1 if to_print == 0 else ceil(to_print + 0.1 * to_print)
        datas = {"Counter": [title], "Value": [to_print]}
        source = ColumnDataSource(datas)
        plot = figure(
            x_range=[title],
            y_range=(0, ymax),
            sizing_mode="stretch_both",
            title=title + extratext,
            tools="pan,wheel_zoom,box_zoom,save,reset",
            active_drag="box_zoom",
            toolbar_location="right",
        )
        plot.vbar(x="Counter", top="Value", source=source, width=0.9)
        plot.add_tools(HoverTool(tooltips="@Value"))
        plot.xaxis.major_label_orientation = draw_params.get("angle_labelsX", 1.2)

        plot.toolbar.logo = None
    else:
        ymax = max(
            motherplot.y_range.end,
            1 if to_print == 0 else ceil(to_print + 0.1 * to_print),
        )
        new_datas = {"Counter": [title], "Value": [to_print]}
        motherplot.x_range.factors.append(title)
        motherplot.renderers[0].data_source.stream(new_datas)
        motherplot.y_range = Range1d(0, ymax)
        plot = motherplot
    return plot
