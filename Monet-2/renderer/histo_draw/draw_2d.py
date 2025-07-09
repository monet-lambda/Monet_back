"""Functions to draw 2D histograms"""
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

import numpy as np
from bokeh.events import DoubleTap
from bokeh.models import (
    ColorBar,
    ColumnDataSource,
    CustomJS,
    HoverTool,
    Label,
    LinearColorMapper,
    LogColorMapper,
    LogTicker,
)
from bokeh.plotting import figure

from .helpers import (
    generate_tick_and_formatter,
    isclose,
    legend_draw,
    linear_color_maker,
    log_color_maker,
    read_hoverfile,
    set_grids,
)
from .palette import get_root_palette


def draw_graph(
    histodb_hist,
    histo_data,
    draw_params,
    ref_data=None,
    highlight=None,
    motherplot=None,
    is_mother=False,
    extratext="",
):
    """Draw graph"""
    data = histo_data["data"]["key_data"]
    values_x = [x[0] for x in data["values"]]
    values_y = [x[1] for x in data["values"]]

    x_range = []
    y_range = []

    if draw_params.get("ymin", None) is not None:
        y_range.append(draw_params["ymin"])
    else:
        y_range.append(min(values_y))

    if draw_params.get("ymax", None) is not None:
        y_range.append(draw_params["ymax"])
    else:
        y_range.append(max(values_y))

    if draw_params.get("xmin", None) is not None:
        x_range.append(draw_params["xmin"])
    else:
        x_range.append(min(values_x))

    if draw_params.get("xmax", None) is not None:
        x_range.append(draw_params["xmax"])
    else:
        x_range.append(max(values_x))

    title = draw_params.get("showtitle", "") or data.get("title", "")

    plot = figure(
        x_axis_label=draw_params.get("label_x", None) or data["axis_titles"][0],
        y_axis_label=draw_params.get("label_y", None) or data["axis_titles"][1],
        x_range=x_range,
        y_range=y_range,
        sizing_mode="stretch_both",
        title=title.replace("^{2}", "²") + extratext,
        tools="pan,wheel_zoom,box_zoom,save,reset",
        active_drag="box_zoom",
        toolbar_location="above",
        x_axis_type="log" if draw_params.get("logx", None) else "auto",
        y_axis_type="log" if draw_params.get("logy", None) else "auto",
    )
    if histo_data["json_name"]:
        url = (
            "https://root.cern/js/latest/?nobrowser&interactive=1&"
            + "json=https://lbwebmonet.cern.ch/ROOT/"
            + histo_data["json_name"]
        )
        plot.js_on_event(
            DoubleTap,
            CustomJS(code='window.open("' + url + '","_blank","menubar=yes");'),
        )

    plot.scatter(values_x, values_y)
    plot.toolbar.logo = None
    return plot


def render2d(
    histodb_hist,
    histo_data,
    draw_params,
    ref_data=None,
    highlight=None,
    motherplot=None,
    is_mother=False,
    extratext="",
    comparison_data=None
):
    """Render 2D plots"""
    data = histo_data["data"]["key_data"]

    if histo_data["data"]["key_class"] == "MonetTrend2D":
        return draw_graph(
            histodb_hist,
            histo_data,
            draw_params,
            ref_data,
            highlight,
            motherplot,
            is_mother,
            extratext,
        )

    def not_empty(label):
        return label != ""

    bin_labelsx_o = draw_params.get("bin_labelsX", None)

    bin_labelsx_h = data.get("bin_labelsX", [])
    bin_labelsx_h = bin_labelsx_h if list(filter(not_empty, bin_labelsx_h)) else None
    bin_labelsx = bin_labelsx_o if bin_labelsx_o else bin_labelsx_h

    bin_labelsy_o = draw_params.get("bin_labelsY", None)

    bin_labelsy_h = data.get("bin_labelsY", [])
    bin_labelsy_h = bin_labelsy_h if list(filter(not_empty, bin_labelsy_h)) else None
    bin_labelsy = bin_labelsy_o if bin_labelsy_o else bin_labelsy_h

    x_range = []
    y_range = []

    if draw_params.get("ymin", None) is not None:
        y_range.append(draw_params["ymin"])
    else:
        if draw_params.get("logy", None) and (
            isclose(data["ybinning"][0][0], 0) or data["ybinning"][0][0] < 0
        ):
            y_range.append(0.01)
        else:
            y_range.append(data["ybinning"][0][0])

    if draw_params.get("ymax", None) is not None:
        y_range.append(draw_params["ymax"])
    else:
        y_range.append(data["ybinning"][-1][1])

    if draw_params.get("xmin", None) is not None:
        x_range.append(draw_params["xmin"])
    else:
        if draw_params.get("logx", None) and (
            isclose(data["xbinning"][0][0], 0) or data["xbinning"][0][0] < 0
        ):
            x_range.append(0.01)
        else:
            x_range.append(data["xbinning"][0][0])

    if draw_params.get("xmax", None) is not None:
        x_range.append(draw_params["xmax"])
    else:
        x_range.append(data["xbinning"][-1][1])

    title = draw_params.get("showtitle", "") or data.get("title", "")

    # Create plot
    plot = figure(
        x_axis_label=draw_params.get("label_x", None) or data["axis_titles"][0],
        y_axis_label=draw_params.get("label_y", None) or data["axis_titles"][1],
        x_range=x_range,
        y_range=y_range,
        sizing_mode="stretch_both",
        title=title.replace("^{2}", "²") + extratext,
        tools="pan,wheel_zoom,box_zoom,save,reset",
        active_drag="box_zoom",
        toolbar_location="above",
        x_axis_type="log" if draw_params.get("logx", None) else "auto",
        y_axis_type="log" if draw_params.get("logy", None) else "auto",
    )

    if histo_data["json_name"]:
        url = (
            "https://root.cern/js/latest/?nobrowser&interactive=1&"
            + "json=https://lbwebmonet.cern.ch/ROOT/"
            + histo_data["json_name"]
        )
        plot.js_on_event(
            DoubleTap,
            CustomJS(code='window.open("' + url + '","_blank","menubar=yes");'),
        )

    if bin_labelsx:
        plot.xaxis[0].ticker, plot.xaxis[0].formatter = generate_tick_and_formatter(
            bin_labelsx, data["xbinning"]
        )
    if bin_labelsy:
        plot.yaxis[0].ticker, plot.yaxis[0].formatter = generate_tick_and_formatter(
            bin_labelsy, data["ybinning"]
        )
    if draw_params.get("rotate_labelsX", False):
        plot.xaxis.major_label_orientation = draw_params.get("angle_labelsX", 1.2)
    if draw_params.get("rotate_labelsY", False):
        plot.yaxis.major_label_orientation = draw_params.get("angle_labelsY", 1.2)

    if draw_params.get("lab_x_size", None) == 0:
        plot.xaxis.visible = False
    if draw_params.get("lab_y_size", None) == 0:
        plot.yaxis.visible = False

    if highlight == plot.title:
        plot.border_fill_color = "pink"

    max_dataval = data["values"].max()
    min_val = draw_params.get("zmin") or data["values"].min()
    max_val = draw_params.get("zmax") or max_dataval

    draw_method = draw_params.get("drawopts", None) or ""
    draw_bin_values = False
    if "COLTEXTZ" in draw_method:
        draw_bin_values = True

    values = data["values"].flatten()
    binxlow = data["xbinning"].take(0, axis=1)
    binxhigh = data["xbinning"].take(1, axis=1)
    binxcenter = (binxlow + binxhigh) / 2.0
    binylow = data["ybinning"].take(0, axis=1)
    binyhigh = data["ybinning"].take(1, axis=1)
    binycenter = (binylow + binyhigh) / 2.0

    xcenter = np.repeat(binxcenter, binyhigh.size)
    ycenter = np.tile(binycenter, binxlow.size)

    effective_minz = 1.0e-14
    if draw_params.get("zmin_fraction", False):
        effective_minz = float(draw_params.get("zmin_fraction")) * max_dataval
    elif draw_params.get("zmin", False):
        effective_minz = draw_params.get("zmin")

    remove_blank = np.logical_and(
        np.abs(values) > effective_minz,
        np.abs(values) < draw_params.get("zmax", np.inf),
    )

    if not draw_params.get("showxaxismarks", True):
        plot.xaxis.major_tick_line_color = None
        plot.xaxis.minor_tick_line_color = None
    if not draw_params.get("showyaxismarks", True):
        plot.yaxis.major_tick_line_color = None
        plot.yaxis.minor_tick_line_color = None
    plot.xaxis.visible = draw_params.get("showxaxislabels", True)
    plot.yaxis.visible = draw_params.get("showyaxislabels", True)

    if draw_bin_values:
        data_idx = 0
        for left, right in zip(binxlow, binxhigh):
            for bottom, top in zip(binylow, binyhigh):
                value = values[data_idx]
                if not isclose(value, 0.0):
                    plot.add_layout(
                        Label(
                            x=(left + right) / 2.0,
                            y=(top + bottom) / 2.0,
                            text=str(value),
                            text_font_size="8pt",
                            render_mode="css",
                        )
                    )
            data_idx += 1

    colorbar_kwargs = dict(
        major_label_text_font_size="8pt",
        location=(0, 0),
    )

    palette = get_root_palette(draw_params.get("palette", None))

    if draw_params.get("logz", None):
        mapper = LogColorMapper(
            palette=palette,
            low=max(1, min_val),
            high=max_val if (min_val != 0 or max_val != 1) else 2,
        )
        colors = log_color_maker(
            values[remove_blank],
            min_val,
            max_val if (min_val != 0 or max_val != 1) else 2,
            palette,
        )

        colorbar_kwargs["ticker"] = LogTicker()
    else:
        if min_val == max_val:
            max_val += 1
        colors = linear_color_maker(values[remove_blank], min_val, max_val, palette)
        mapper = LinearColorMapper(palette=palette, low=min_val, high=max_val)

    colorbar_kwargs["color_mapper"] = mapper

    set_grids(plot, draw_params, data)

    extra_height = draw_params.get("extraheight", 0.0)
    extra_width = draw_params.get("extrawidth", 0.0)

    source_data = ColumnDataSource(
        data={"x": xcenter[remove_blank], "y": ycenter[remove_blank], "color": colors}
    )

    if draw_params.get("hoverfile", None):
        labels, h_data, hover_x, hover_y = read_hoverfile(
            f"/hist/Reference/{histodb_hist['taskname']}/{draw_params['hoverfile']}"
        )
        the_data = {"x": hover_x, "y": hover_y}
        the_data.update(h_data)
        tooltips = []
        for label in labels:
            tooltips.append((label, f"@{label}"))
        source_data_hover = ColumnDataSource(data=the_data)
        rect_renderer = plot.rect(
            x="x",
            y="y",
            source=source_data_hover,
            fill_color="white",
            height=binyhigh[0] - binylow[0] + extra_height,
            width=binxhigh[0] - binxlow[0] + extra_width,
            line_width=0,
            syncable=False,
        )
        hover = HoverTool(tooltips=tooltips, renderers=[rect_renderer])
        plot.add_tools(hover)

    plot.rect(
        x="x",
        y="y",
        source=source_data,
        fill_color="color",
        height=binyhigh[0] - binylow[0] + extra_height,
        width=binxhigh[0] - binxlow[0] + extra_width,
        line_width=0,
        syncable=False,
    )

    color_bar = ColorBar(**colorbar_kwargs)
    plot.add_layout(color_bar, "right")
    plot.toolbar.logo = None

    has_legend = legend_draw(data, draw_params, plot, False, is2d=True)
    if has_legend and (is_mother or not motherplot):
        if draw_params.get("legendlocation", None):
            plot.legend.location = draw_params.get("legendlocation")
        elif draw_params.get("legendlocation_x", None) and draw_params.get(
            "legendlocation_y", None
        ):
            plot.legend.location = (
                float(draw_params.get("legendlocation_x")),
                float(draw_params.get("legendlocation_y")),
            )
        else:
            plot.legend.location = "top_right"
        plot.legend.label_text_font_size = draw_params.get("legendfontsize", "13px")
        plot.legend.click_policy = "hide"

    return plot
