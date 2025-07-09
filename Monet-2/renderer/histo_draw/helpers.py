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
import json
import logging
from math import log

import numpy as np
import ROOT
from bokeh.models import CustomJSTickFormatter, FixedTicker, Legend, LegendItem
from colorhash import ColorHash


def read_hoverfile(file):
    with open(file) as f:
        hdata = json.load(f)
    labels = set()
    hover_x = []
    hover_y = []
    for i in hdata:
        bin_center = i["bin_center"]
        hover_x.append(bin_center[0])
        hover_y.append(bin_center[1])
        for j in i["hover_label"]:
            labels.add(j)
    result = {}
    for i in labels:
        result[i] = [k["hover_label"][i] for k in hdata]
    return labels, result, hover_x, hover_y


def safe_list_get(the_list, idx, default):
    """Return element from list at position idx. If idx does not exist, returns default"""
    try:
        return the_list[idx]
    except IndexError:
        return default


def bin_edge_ticker(binning):
    """Returns edge tick from binning array"""
    return FixedTicker(ticks=[b[1] for b in binning])


def generate_tick_and_formatter(bin_labels, binning):
    """Generate ticks with correct format"""
    bin_mids = [(b[0] + b[1]) / 2.0 for b in binning]
    formatter_lut = {
        f"{mid:1.5f}": safe_list_get(bin_labels, i, "")
        for i, mid in enumerate(bin_mids)
    }

    js_code = """
    const data = new Map();
    """
    for k, v in formatter_lut.items():
        js_code += f"""
    data.set(\'{k}\',\'{v}\');"""

    js_code += """
    return data.get(String(tick.toFixed(5)));
    """

    ticker = FixedTicker(ticks=bin_mids)
    formatter = CustomJSTickFormatter(code=js_code)

    return ticker, formatter


def convert_color(color_root_int, name=""):
    """Convert color into ROOT color"""
    if color_root_int == 0:
        color_root_int = 1
    if color_root_int == "auto":
        c = ColorHash(name).rgb
        return tuple([c[0], c[1], c[2]])
    try:
        col = ROOT.gROOT.GetColor(int(color_root_int))
        col = (col.GetRed(), col.GetGreen(), col.GetBlue())
    except ReferenceError:
        logging.error(f"Unknown color {color_root_int}")
        col = (1, 1, 1)
    return tuple(int(c * 255) for c in col)


def isclose(a, b, eps=1e-14):
    """Check if value is close to another one with given precision eps"""
    if not a:
        a = 0.0
    if not b:
        b = 0.0
    return abs(a - b) < eps


def linear_color_maker(values, min_val, max_val, pallete):
    """Make color pallette for linear plots"""
    rng = abs(max_val - min_val)
    a_pallete = np.array(pallete)
    colors = np.where(
        np.abs(values) < 1e-14,
        "#FFFFFF",
        a_pallete[
            np.minimum(
                len(pallete) - 1, np.int_(np.abs(values - min_val) / rng * len(pallete))
            )
        ],
    )
    del a_pallete
    return colors


def log_color_maker(values, min_val, max_val, pallete):
    """Make color pallete for log scale"""
    colors = []
    if len(values) == 0:
        return colors

    if isclose(min_val, 0.0):
        min_val = min(values)

    try:
        log_min = log(min_val)
    except ValueError:
        log_min = -6

    try:
        log_max = log(max_val)
    except ValueError:
        log_max = 0

    for value in values:
        if isclose(max_val, min_val) or isclose(value, 0.0):
            colors.append("#FFFFFF")
            continue

        log_val = log(value)
        p = abs(log_val - log_min) / abs(log_max - log_min)
        idx = min(len(pallete) - 1, int(p * len(pallete)))
        colors.append(pallete[idx])

    return colors


def legend_draw(
    data, draw_params, plot, merged_hist, is2d=False, ref_data=None, ref_renderer=None
):
    """Draw legend"""
    if draw_params.get("stats", None) is None:
        return False

    ref_stats = []
    rdata = None
    if merged_hist:
        stats = []
    else:
        # Empty squares, only for legend entry
        stats = [
            ("Name", data.get("title")),
            ("Entries", data.get("numberEntries")),
            ("Mean", data.get("mean")),
            ("RMS", data.get("RMS")),
            ("Underflow", data.get("underflow")),
            ("Overflow", data.get("overflow")),
            ("Integral", data.get("integral")),
            ("Skewness", data.get("skewness")),
            ("Kurtosis", data.get("kurtosis")),
        ]
        if ref_data and not ref_data["not_found"]:
            rdata = ref_data["data"]["key_data"]
            ref_stats = [
                ("Name", rdata.get("title")),
                ("Entries", rdata.get("numberEntries")),
                ("Mean", rdata.get("mean")),
                ("RMS", rdata.get("RMS")),
                ("Underflow", rdata.get("underflow")),
                ("Overflow", rdata.get("overflow")),
                ("Integral", rdata.get("integral")),
                ("Skewness", rdata.get("skewness")),
                ("Kurtosis", rdata.get("kurtosis")),
            ]

    stats_str = str(draw_params.get("stats", None))[::-1]

    legend_items = []
    if stats_str == "0":
        stats_str = "10"[::-1]

    j = 0
    for i, (name, val) in enumerate(stats):
        j = j + 1
        if i > len(stats_str) - 1:
            break

        if stats_str[i] == "1":
            if is2d and name in ["Mean", "RMS"]:
                if name == "Mean":
                    valx = data.get("mean_x")
                    valy = data.get("mean_y")
                else:
                    valx = data.get("RMS_x")
                    valy = data.get("RMS_y")
                legend_items.append(LegendItem(label=f"{name}_x: {valx}"))
                legend_items.append(LegendItem(label=f"{name}_y: {valy}"))
            else:
                legend_items.append(LegendItem(label=f"{name}: {val}"))

    if data.get("results") and draw_params.get("analysisresults", None) == "legend":
        results = data.get("results")
        if isinstance(results, dict):
            for key in results:
                label = f"{key}: {results[key]}"
                legend_items.append(LegendItem(label=label))
                j = j + 1
        else:
            label = str(results)
            legend_items.append(LegendItem(label=label))

    if ref_data and not ref_data["not_found"]:
        j = 0
        for i, (name, val) in enumerate(ref_stats):
            j = j + 1
            if i > len(stats_str) - 1:
                break

            if stats_str[i] == "1":
                if is2d and name in ["Mean", "RMS"]:
                    if name == "Mean":
                        valx = rdata.get("mean_x")
                        valy = rdata.get("mean_y")
                    else:
                        valx = rdata.get("RMS_x")
                        valy = rdata.get("RMS_y")
                    legend_items.append(
                        LegendItem(label=f"{name}_x: {valx}", renderers=[ref_renderer])
                    )
                    legend_items.append(
                        LegendItem(label=f"{name}_y: {valy}", renderers=[ref_renderer])
                    )
                else:
                    legend_items.append(
                        LegendItem(label=f"{name}: {val}", renderers=[ref_renderer])
                    )
        if rdata:
            if (
                rdata.get("results")
                and draw_params.get("analysisresults", None) == "legend"
            ):
                results = rdata.get("results")
                if isinstance(results, dict):
                    for key in results:
                        label = "{key}: {results[key]}"
                        legend_items.append(
                            LegendItem(label=label, renderers=[ref_renderer])
                        )
                        j = j + 1
                else:
                    label = str(results)
                    legend_items.append(
                        LegendItem(label=label, renderers=[ref_renderer])
                    )

    legend = Legend(items=legend_items)
    legend.background_fill_alpha = draw_params.get("legendalpha", 0.5)
    plot.add_layout(legend)

    return True


def set_grids(plot, draw_params, data, one_dim=False):
    """Set grids"""
    if draw_params.get("gridx", None):
        plot.xgrid.grid_line_color = "#AAAAAA"
        plot.xgrid.grid_line_alpha = 0.7
        plot.xgrid.ticker = bin_edge_ticker(data["binning" if one_dim else "xbinning"])
    else:
        plot.xgrid.visible = False

    if draw_params.get("gridy", None):
        plot.ygrid.grid_line_color = "#AAAAAA"
        plot.ygrid.grid_line_alpha = 0.7
        plot.ygrid.visible = True
        if not one_dim:
            plot.ygrid.ticker = bin_edge_ticker(data["ybinning"])
    else:
        plot.ygrid.visible = False
