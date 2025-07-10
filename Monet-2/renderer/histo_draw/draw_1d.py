"""Functions to plot 1D histograms"""


import logging
from datetime import datetime
from math import pi

import ROOT
import numpy as np
from bokeh.events import DoubleTap
from bokeh.models import ColumnDataSource, CustomJS, HoverTool, Range1d, Whisker
from bokeh.models.formatters import BasicTickFormatter, DatetimeTickFormatter
from bokeh.plotting import figure

from .helpers import (
    convert_color,
    generate_tick_and_formatter,
    isclose,
    legend_draw,
    set_grids,
)


def get_bounds_and_nonzero(values, uncertainties):
    """get max and min of values"""
    try:
        min_x = values[0]
    except IndexError:
        min_x = 0
    min_x_error = 0.0
    if len(uncertainties) > 0:
        min_x_error = uncertainties[0][0]

    try:
        max_x = values[0]
    except IndexError:
        max_x = 0
    max_x_error = 0.0
    if len(uncertainties) > 0:
        max_x_error = uncertainties[0][1]

    nonzero_data = []

    for i, x in enumerate(values):
        if x < min_x:
            min_x = x
            if i < len(uncertainties) - 1:
                min_x_error = uncertainties[i][0]
        elif x > max_x:
            max_x = x
            if i < len(uncertainties) - 1:
                max_x_error = uncertainties[i][1]

        if x > 0.0:
            nonzero_data.append(x)

    return min_x, min_x_error, max_x, max_x_error, nonzero_data


def set_proper_range(plot, data, draw_params, is_trend, is_trenddq):
    """Set range of plot"""
    if is_trend or is_trenddq:
        if not draw_params.get("ymin", None) and not draw_params.get("ymax", None):
            return

    # handle correctly logx, logy
    if draw_params.get("rotate_axes", False):
        logx = draw_params.get("logy", None)
        logy = draw_params.get("logx", None)
    else:
        logx = draw_params.get("logx", None)
        logy = draw_params.get("logy", None)

    if not is_trend and not is_trenddq:
        min_val, min_val_error, max_val, max_val_error, nonzero_data = (
            get_bounds_and_nonzero(data["values"], data["uncertainties"])
        )
    else:
        min_val, min_val_error, max_val, max_val_error, nonzero_data = (
            get_bounds_and_nonzero(
                [v[1] for v in data["values"]], data["uncertainties"]
            )
        )

    if logy and len(nonzero_data) > 0:
        max_data_value = max(nonzero_data) * 2
        min_data_value = min(nonzero_data) * 1e-2
        if draw_params.get("rotate_axes", False):
            plot.x_range = Range1d(min_data_value, max_data_value)
        else:
            plot.y_range = Range1d(min_data_value, max_data_value)
    elif not logy and not is_trend and not is_trenddq:
        if min_val_error and not isclose(min_val_error, 0):
            if draw_params.get("rotate_axes", False):
                plot.x_range.start = min_val - 3 * min_val_error
            else:
                plot.y_range.start = min_val - 3 * min_val_error
        else:
            if draw_params.get("rotate_axes", False):
                plot.x_range.start = 0.85 * min_val
            else:
                plot.y_range.start = 0.85 * min_val

        if max_val_error and not isclose(max_val_error, 0):
            if draw_params.get("rotate_axes", False):
                plot.x_range.end = (max_val + 3 * max_val_error) * 1.1
            else:
                plot.y_range.end = (max_val + 3 * max_val_error) * 1.1
        else:
            if draw_params.get("rotate_axes", False):
                plot.x_range.end = max_val * 1.2
            else:
                plot.y_range.end = max_val * 1.2

        if isclose(min_val, max_val) and isclose(min_val, 0):
            if draw_params.get("rotate_axes", False):
                plot.x_range.start = 0.0
                plot.x_range.end = 1.0
            else:
                plot.y_range.start = 0.0
                plot.y_range.end = 1.0
    if logx and isclose(data["binning"][0][0], 0.0):
        if draw_params.get("rotate_axes", False):
            plot.y_range.start = data["binning"][0][1] / 100
        else:
            plot.x_range.start = data["binning"][0][1] / 100

    if draw_params.get("ymin", None) or (0 == draw_params.get("ymin", None)):
        plot.y_range.start = float(draw_params.get("ymin"))
    if draw_params.get("ymax", None) or (0 == draw_params.get("ymax", None)):
        plot.y_range.end = float(draw_params.get("ymax"))
    if draw_params.get("xmin", None) or (0 == draw_params.get("xmin", None)):
        plot.x_range.start = float(draw_params.get("xmin"))
    if draw_params.get("xmax", None) or (0 == draw_params.get("xmax", None)):
        plot.x_range.end = float(draw_params.get("xmax"))
    if is_trend or is_trenddq:
        if isclose(min_val, max_val) and isclose(min_val, 0):
            plot.y_range.start = -1.0
            plot.y_range.end = 1.0


def draw_1d_histogram_with_errorbars(
    plot,
    data,
    color,
    draw_params,
    legend="",
    motherplot=None,
    is_mother=False,
    is_ref=False,
    is_trenddq=False,
):
    """draw 1D histograms with error bars"""
    r = None
    if motherplot or is_mother:
        legend = (
            draw_params.get("legendtext", None)
            or draw_params.get("showtitle", None)
            or data.get("title", None)
        )

    nonzero_ixs = []
    if (not is_ref) and (draw_params.get("drawopts", None) == "e0"):
        nonzero_ixs = [i for i, v in enumerate(data["values"])]
    elif (is_ref) and (draw_params.get("refdrawopts", None) == "e0"):
        nonzero_ixs = [i for i, v in enumerate(data["values"])]
    else:
        nonzero_ixs = [i for i, v in enumerate(data["values"]) if not isclose(v, 0)]
    values, bins, uncertainties = [], [], []
    no_uncertainty = False
    draw_method = draw_params.get("drawopts", None) or ""
    if "marker" in draw_method.lower():
        no_uncertainty = True

    for ix in nonzero_ixs:
        values.append(data["values"][ix])
        bins.append(data["binning"][ix])
        if no_uncertainty:
            uncertainties.append((0.0, 0.0))
        else:
            try:
                uncertainties.append(data["uncertainties"][ix])
            except IndexError:
                uncertainties.append((0.0, 0.0))

    bin_mids = [(b[0] + b[1]) / 2.0 for b in bins]
    draw_color = convert_color(color)
    try:
        r = plot.scatter(
            bin_mids,
            values,
            color=draw_color,
            size=4,
            line_alpha=0.5,
            legend_label=legend,
        )
    except RuntimeError:
        pass
    plot.legend.visible = legend != ""

    err_xs = []
    err_ys = []

    for x, y, abin, yerr in zip(bin_mids, values, bins, uncertainties):
        # x error bar
        if draw_params.get("logx", None) and isclose(abin[0], 0.0):
            err_xs.append((1e-10, abin[1]))
        else:
            err_xs.append((abin[0], abin[1]))
        err_ys.append((y, y))

        # y error bar
        err_xs.append((x, x))
        err_ys.append((y - yerr[0], y + yerr[1]))

    plot.multi_line(err_xs, err_ys, color=draw_color)

    if draw_params.get("fillcolor", None) and not is_ref:
        try:
            col = convert_color(
                draw_params.get("fillcolor", None), data.get("title", "")
            )
        except IndexError:
            return
        left = [b[0] for b in bins]
        right = [b[1] for b in bins]
        top = values
        if draw_params.get("logy", None):
            bottom = [1e-10] * len(values)
        else:
            bottom = [0] * len(values)

        r = plot.quad(
            left, right, bottom, top, fill_alpha=0.6, fill_color=col, line_alpha=0.0
        )
    if not r:
        logging.error("Histo not defined: {legend} ")
    return r


def draw_1d_histogram_as_hist(
    plot,
    data,
    color,
    draw_params,
    legend="",
    motherplot=None,
    is_mother=False,
    is_ref=False,
    is_trenddq=False,
):
    """draw 1D hitogram as histogram"""
    if motherplot or is_mother:
        legend = draw_params.get("showtitle", None) or data.get("title", None)

    # handle correctly logx, logy
    if draw_params.get("rotate_axes", False):
        logx = draw_params.get("logy", None)
        logy = draw_params.get("logx", None)
    else:
        logx = draw_params.get("logx", None)
        logy = draw_params.get("logy", None)

    if draw_params.get("rotate_axes", False):
        min_y = plot.x_range.start
    else:
        min_y = plot.y_range.start

    xs = []
    ys = []

    xs.append((data["binning"][0][0], data["binning"][0][0]))

    ys.append((min_y, data["values"][0]))

    for i in range(len(data["values"])):
        x = data["binning"][i]
        y = data["values"][i]

        if i == len(data["values"]) - 1:
            next_y = min_y
        else:
            next_y = data["values"][i + 1]

        if logy:
            if isclose(next_y, 0):
                next_y = min_y
            if isclose(y, 0):
                y = min_y

        # horizontal bar
        if logx and isclose(x[0], 0.0):
            if draw_params.get("rotate_axes", False):
                xs.append((plot.y_range.start, x[1]))
            else:
                xs.append((plot.x_range.start, x[1]))
        else:
            xs.append((x[0], x[1]))
        ys.append((y, y))

        # vertical bar
        xs.append((x[1], x[1]))
        ys.append((y, next_y))

    line_kwargs = dict(
        color=convert_color(color),
        line_width=2,
    )

    if not draw_params.get("stats", None):
        line_kwargs["legend_label"] = legend

    if is_ref:
        line_kwargs["line_dash"] = "dotted"
        line_kwargs["line_width"] = 2

    if draw_params.get("rotate_axes", False):
        xs, ys = ys, xs

    r = plot.multi_line(xs, ys, **line_kwargs)

    if is_ref:
        return r

    if draw_params.get("fillcolor", None) and draw_params.get("fillstyle", None):
        p_xs = [item for sublist in xs for item in sublist]
        p_ys = [item for sublist in ys for item in sublist]

        col = convert_color(draw_params.get("fillcolor", None), data.get("title", ""))
        plot.patch(p_xs, p_ys, alpha=0.6, line_width=0, fill_color=col)

        max_data_value = max(data["values"]) * 1.2

        if draw_params.get("rotate_axes", False):
            if plot.x_range.end:
                if max_data_value > plot.x_range.end and float(max_data_value) > 1.0:
                    plot.x_range = Range1d(min_y, max_data_value)
        else:
            if plot.y_range.end:
                if max_data_value > plot.y_range.end and float(max_data_value) > 1.0:
                    plot.y_range = Range1d(min_y, max_data_value)
    return r


def draw_1d_histogram_as_trend(
    plot,
    data,
    color,
    draw_params,
    legend="",
    motherplot=None,
    is_mother=False,
    is_ref=False,
    is_trenddq=False,
):
    """draw 1D histogram as trend plot"""
    data_source = ColumnDataSource(
        data={
            "x": [v[0] for v in data["values"]],
            "y": [v[1] for v in data["values"]],
            "index": [str(v[0]) for v in data["values"]],
        }
    )

    try:
        legend_text = (
            f"{data.get('titlelegend', '')}: {data['values'][-1][1]:.2g}"
            if not is_trenddq
            else f"{data.get('titlelegend', '')}"
        )
        if draw_params.get("drawopts", "line") == "line":
            plot.line(
                x="x",
                y="y",
                source=data_source,
                line_color=convert_color(color, data.get("titlelegend", "")),
                line_width=2,
                legend_label=legend_text,
            )
        elif draw_params.get("drawopts", "line") == "marker":
            plot.scatter(
                x="x",
                y="y",
                source=data_source,
                line_color=convert_color(color, data.get("titlelegend", "")),
                legend_label=legend_text,
            )
        elif draw_params.get("drawopts", "line") == "marker_with_errors":
            source_error = ColumnDataSource(
                data={
                    "base": [v[0] for v in data["values"]],
                    "lower": [
                        v[1] - w[0]
                        for v, w in zip(data["values"], data["uncertainties"])
                    ],
                    "upper": [
                        v[1] + w[1]
                        for v, w in zip(data["values"], data["uncertainties"])
                    ],
                }
            )
            plot.add_layout(
                Whisker(
                    source=source_error,
                    base="base",
                    upper="upper",
                    lower="lower",
                    line_color=convert_color(color, data.get("titlelegend", "")),
                    line_width=2,
                    upper_head=None,
                    lower_head=None,
                )
            )
            plot.scatter(
                x="x",
                y="y",
                source=data_source,
                line_color=convert_color(color, data.get("titlelegend", "")),
                legend_label=legend_text,
            )
        elif draw_params.get("drawopts", "line") == "skip_missing":
            source_error = ColumnDataSource(
                data={
                    "base": [str(v[0]) for v in data["values"]],
                    "lower": [
                        v[1] - w[0]
                        for v, w in zip(data["values"], data["uncertainties"])
                    ],
                    "upper": [
                        v[1] + w[1]
                        for v, w in zip(data["values"], data["uncertainties"])
                    ],
                }
            )
            plot.add_layout(
                Whisker(
                    source=source_error,
                    base="base",
                    upper="upper",
                    lower="lower",
                    line_color=convert_color(color, data.get("titlelegend", "")),
                    line_width=2,
                    upper_head=None,
                    lower_head=None,
                )
            )
            plot.scatter(
                x="index",
                y="y",
                source=data_source,
                line_color=convert_color(color, data.get("titlelegend", "")),
                legend_label=legend_text,
            )
    except IndexError:
        if draw_params.get("drawopts", "line") == "line":
            plot.line(
                x="x",
                y="y",
                source=data_source,
                line_color=convert_color(color, data.get("titlelegend", "")),
                line_width=2,
                legend_label=f"{data.get('titlelegend', '')}",
            )
        else:
            plot.scatter(
                x="x",
                y="y",
                source=data_source,
                line_color=convert_color(color, data.get("titlelegend", "")),
                legend_label=f"{data.get('titlelegend', '')}",
            )
    if not is_trenddq:
        plot.add_tools(
            HoverTool(
                tooltips=[("Date", "$x{%d-%m %H:%M:%S}"), ("Value", "@y")],
                formatters={"$x": "datetime"},
                mode="vline",
            )
        )
    else:
        plot.add_tools(
            HoverTool(tooltips=[("Run", "@x"), ("Value", "@y")], mode="vline")
        )

    return


def render1d(
    histodb_hist,
    histo_data,
    draw_params,
    ref_data=None,
    highlight=None,
    motherplot=None,
    trend=False,
    trenddq=False,
    is_mother=False,
    extratext="",
    comparison_data=None
):
    """Main function to draw 1D histograms"""
    data = histo_data["data"]["key_data"]
    axis_titles_x = data["axis_titles"][0]
    axis_titles_y = data["axis_titles"][1]
    if draw_params.get("rotate_axes", False):
        draw_params["label_x"], draw_params["label_y"] = (
            draw_params.get("label_y", None),
            draw_params.get("label_x", None),
        )
        draw_params["logx"], draw_params["logy"] = (
            draw_params.get("logy", None),
            draw_params.get("logx", None),
        )
        draw_params["xmin"], draw_params["ymin"] = (
            draw_params.get("ymin", None),
            draw_params.get("xmin", None),
        )
        draw_params["xmax"], draw_params["ymax"] = (
            draw_params.get("ymax", None),
            draw_params.get("xmax", None),
        )
        axis_titles_y, axis_titles_x = axis_titles_x, axis_titles_y

    data["titlelegend"] = draw_params.get(
        "legendtext", draw_params.get("showtitle", data.get("title", ""))
    )
    title = draw_params.get("showtitle", "") or data.get("title", "")
    if not motherplot or isinstance(motherplot, Exception):
        try:
            plot = figure(
                x_axis_label=draw_params.get("label_x", None) or axis_titles_x,
                y_axis_label=draw_params.get("label_y", None) or axis_titles_y,
                sizing_mode="stretch_both",
                x_range=(data["binning"][0][0], data["binning"][-1][-1])
                if not trend and not trenddq
                else (
                    datetime.fromtimestamp(data["start_time"]),
                    datetime.fromtimestamp(data["end_time"]),
                )
                if not trenddq
                else (data["binning"][0], data["binning"][-1])
                if not draw_params.get("drawopts", "") == "skip_missing"
                else [str(v[0]) for v in data["values"]],
                title=title + extratext,
                tools="pan,wheel_zoom,box_zoom,save,reset",
                active_drag="box_zoom",
                toolbar_location="right",
                x_axis_type="log"
                if draw_params.get("logx", None)
                else "datetime"
                if trend
                else "auto",
                y_axis_type="log" if draw_params.get("logy", None) else "auto",
            )
        except ValueError:
            logging.error("Error validating plot %s", title)
            return None
        if not draw_params.get("showxaxismarks", True):
            plot.xaxis.major_tick_line_color = None
            plot.xaxis.minor_tick_line_color = None
        if not draw_params.get("showyaxismarks", True):
            plot.yaxis.major_tick_line_color = None
            plot.yaxis.minor_tick_line_color = None
        plot.xaxis.visible = draw_params.get("showxaxislabels", True)
        plot.yaxis.visible = draw_params.get("showyaxislabels", True)

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
    else:
        plot = motherplot

    set_proper_range(plot, data, draw_params, trend, trenddq)

    def not_empty(label):
        return label != ""

    bin_labels_o = draw_params.get("bin_labelsX", None)

    bin_labels_h = data.get("bin_labelsX", [])
    bin_labels_h = bin_labels_h if list(filter(not_empty, bin_labels_h)) else None
    bin_labels = bin_labels_o if bin_labels_o else bin_labels_h
    if bin_labels:
        if draw_params.get("rotate_axes", False):
            plot.yaxis[0].ticker, plot.yaxis[0].formatter = generate_tick_and_formatter(
                bin_labels, data["binning"]
            )
            plot.yaxis.major_label_orientation = pi / 6
        else:
            plot.xaxis[0].ticker, plot.xaxis[0].formatter = generate_tick_and_formatter(
                bin_labels, data["binning"]
            )
            plot.xaxis.major_label_orientation = pi / 6

    elif trend:
        plot.xaxis[0].formatter = DatetimeTickFormatter(
            minutes="%H:%M",
            minsec="%H:%M:%S",
            hourmin="%H:%M",
            hours="%d-%m %H:%M",
            days="%d-%m-%Y",
            months="%m-%Y",
        )
    elif trenddq and draw_params.get("drawopts", "") != "skip_missing":
        plot.xaxis[0].formatter = BasicTickFormatter(use_scientific=False)

    if draw_params.get("rotate_axes", False):
        if draw_params.get("rotate_labelsX", False):
            plot.yaxis.major_label_orientation = draw_params.get("angle_labelsX", 1.2)
    else:
        if draw_params.get("rotate_labelsX", False):
            plot.xaxis.major_label_orientation = draw_params.get("angle_labelsX", 1.2)

    plot.toolbar.logo = None
    if highlight and highlight == data.get("title", ""):
        plot.border_fill_color = "pink"

    draw_histogram = draw_1d_histogram_with_errorbars
    draw_ref_histogram = draw_1d_histogram_with_errorbars
    draw_method = draw_params.get("drawopts", None) or ""
    draw_ref_method = draw_params.get("refdrawopts", None) or ""

    if trend or trenddq:
        draw_histogram = draw_1d_histogram_as_trend
    else:
        if "hist" in draw_method.lower():
            draw_histogram = draw_1d_histogram_as_hist
        if "hist" in draw_ref_method.lower():
            draw_ref_histogram = draw_1d_histogram_as_hist

    set_grids(plot, draw_params, data, one_dim=True)
    try:
        draw_histogram(
            plot,
            data,
            draw_params.get("linecolor", None) or ROOT.kBlue,
            draw_params,
            motherplot=motherplot,
            is_mother=is_mother,
            is_trenddq=trenddq,
        )
    except RuntimeError:
        logging.error("Error with plot %s", title)
    ref_renderer = None
    if ref_data and not ref_data["not_found"]:
        rdata = ref_data["data"]["key_data"]
        ref_renderer = draw_ref_histogram(
            plot, rdata, ROOT.kRed, draw_params, is_ref=True
        )

    if comparison_data and not comparison_data["not_found"]:
        if not draw_params.get("ref", "area"):
            ref_norm = None
        else:
            ref_norm = draw_params.get("ref", "area").lower()
        cdata = comparison_data["data"]["key_data"]
        c_in = np.array(cdata["values"])
        cu_in = np.array(cdata["uncertainties"])
        d_in = np.array(data["values"])
        if ref_norm == "area":
            c_in_n = c_in/c_in.sum()*d_in.sum()
        elif ref_norm == "entr":
            c_in_n = c_in/c_in.sum()*d_in.sum()
        else:
            c_in_n = c_in
        cdata["values"]=c_in_n.tolist()
        if c_in.sum()!=0: 
            if ref_norm == "area":
                cu_in_n = cu_in/c_in.sum()*d_in.sum()
            elif ref_norm == "entr":
                cu_in_n = cu_in/c_in.sum()*d_in.sum()
            else:
                cu_in_n = cu_in
            cdata["uncertainties"]=cu_in_n.tolist()
        comparison_renderer = draw_ref_histogram(
            plot, cdata, ROOT.kBlack, draw_params, is_ref=True
        )

    has_legend = legend_draw(
        data,
        draw_params,
        plot,
        is_mother or motherplot,
        ref_data=ref_data,
        ref_renderer=ref_renderer,
    )
    if trend:
        has_legend = True
    if has_legend and (trend or is_mother or not motherplot):
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
    if draw_params.get("hidelegend", False):
        plot.legend.visible = False
        plot.legend.click_policy = "none"
    return plot
