"""Utility functions for MONET"""


import copy
import logging
import os
import traceback
from datetime import datetime, timedelta

import markdown
import ROOT
from bokeh.embed import components
from flask import current_app

from data_load.obtainers.get_data import get_data_for_request
from presenter.cache import cache
from renderer.histo_draw.draw import histo_draw

from .root_canvas import draw_root_canvas_on_plot, find_pattern_path


def create_initial_page_doc(page_doc: str) -> str:
    """Create page documentation


    Args:
        page_doc (str): documentation in markown format from
        the histoyml file

    Returns:
        str: the documentation in html format
    """
    if (not page_doc) or page_doc.isspace():
        page_doc = "No information is available in HistoYML"

    html = markdown.markdown(page_doc, extensions=["footnotes"])
    page_doc = html

    return page_doc


def create_description_histo(histos: list, histo_values: dict, files_used: list[str], ref_used: list[str] ) -> str:
    """Create html with the description of the histograms take from the
    histoyml file

    Args:
        histos (list): list of histograms
        histo_values (dict): values of the histograms

    Returns:
        str: HTML with the description
    """
    page_doc = ""
    if ref_used:
        descr_tmplt = """
            <li>
                <a href="#" onclick="
                var dWnd = window.open('', 'dWnd', 'width=480,height=640');
                dWnd.document.write(`<b>{}</b><hr/>{}`);
                ">{}</a>, <i>task:</i> {}, <i>file:</i> {}, <i>reference:</i> {}
            </li>
        """
    else:
        descr_tmplt = """
            <li>
                <a href="#" onclick="
                var dWnd = window.open('', 'dWnd', 'width=480,height=640');
                dWnd.document.write(`<b>{}</b><hr/>{}`);
                ">{}</a>, <i>task:</i> {}, <i>file:</i> {}
            </li>
        """

    histo_descriptions = []
    if ref_used:
        for h, file_used, r in zip(histos, files_used, ref_used):
            if h["taskname"] + "/" + h["name"] not in histo_values:
                continue
            histo_descr = h.get("description", "")

            data = histo_values[h["taskname"] + "/" + h["name"]]
            title = data.get("title", h["name"])
            histo_descr = histo_descr.replace("\n", "<br/>")

            histo_descriptions.append(
                descr_tmplt.format(title, histo_descr, title, h["taskname"], file_used, r)
            )
    else:
        for h, file_used in zip(histos, files_used):
            if h["taskname"] + "/" + h["name"] not in histo_values:
                continue
            histo_descr = h.get("description", "")

            data = histo_values[h["taskname"] + "/" + h["name"]]
            title = data.get("title", h["name"])
            histo_descr = histo_descr.replace("\n", "<br/>")

            histo_descriptions.append(
                descr_tmplt.format(title, histo_descr, title, h["taskname"], file_used)
            )        

    if len(histo_descriptions) == 0:
        return page_doc

    page_doc += "".join(histo_descriptions)
    return page_doc


def create_page_doc(histos: list, histo_values, page_doc: str) -> str:
    """Create page documentation

    Args:
        histos (list): list of histograms
        histo_values (_type_): values of the histograms
        page_doc (str): page description

    Returns:
        str: page documentation in HTML format
    """
    if (not page_doc) or page_doc.isspace():
        page_doc = "No information is available in HistoYML"

    html = markdown.markdown(page_doc, extensions=["footnotes"])
    page_doc = html

    results = []
    # analysis results
    for h in histos:
        draw_params = h["display_options"]
        if draw_params.get("analysisresults", "") == "page information":
            data = histo_values[f"{h['taskname']}/{h['name']}"]["data"]["key_data"]
            text_to_add = f"<li> {data.get('results', 'No results')} </li>"
            results.append(text_to_add)

    if len(results) != 0:
        page_doc += "<hr><p> <b>Results of the automatic analysis:</b>"
        page_doc += "<ul>"
        page_doc += "".join(results)
        page_doc += "</ul>"
        page_doc += "</p>"

    descr_tmplt = """
        <li>
            <a href="#" onclick="
            var dWnd = window.open('', 'dWnd', 'width=480,height=640');
            dWnd.document.write(`<b>{}</b><hr/>{}`);
            ">{}</a>, <i>task:</i> {}
        </li>
    """

    histo_descriptions = []
    for h in histos:
        if h["taskname"] + "/" + h["name"] not in histo_values:
            continue
        histo_descr = h.get("description", "")

        data = histo_values[h["taskname"] + "/" + h["name"]]
        title = data.get("title", h["name"])
        histo_descr = histo_descr.replace("\n", "<br/>")

        histo_descriptions.append(
            descr_tmplt.format(title, histo_descr, title, h["taskname"])
        )

    if len(histo_descriptions) == 0:
        return page_doc

    page_doc += "<hr><p> <b>Descriptions for histograms:</b>"
    page_doc += "<ul>"
    page_doc += "".join(histo_descriptions)
    page_doc += "</ul>"
    page_doc += "</p>"
    return page_doc


def get_histograms(path: str) -> tuple:
    """Get histograms in the page

    Args:
        path (str): path

    Returns:
        tuple: values, list of keys and page documentation
    """
    connection = current_app.config["HISTODB"]
    logging.debug(f"Getting histograms for: {path}")
    obtain_histos = connection.get_histos_in_path
    try:
        histos_contained, page_doc = obtain_histos(path)
    except RuntimeError:
        raise

    try:
        key_list = [
            (h["name"], h["taskname"], h["display_options"]) for h in histos_contained
        ]
    except KeyError:
        key_list = []

    return histos_contained, key_list, page_doc


def render(plotid: str, the_plot) -> tuple[str, str, float]:
    """Render the plot

    Args:
        plotid (str): plot id
        the_plot (_type_):

    Returns:
        tuple[str, str, float]: html div, script and size
    """
    plot, size = the_plot
    """Display plot"""
    if isinstance(plot, Exception):
        script, div = "", f'<div class="histo-err">{str(plot)}</div>'
    else:
        try:
            script, div = components(plot, wrap_script=False)
        except (IOError,ValueError):
            logging.error(f"Error in render: {plotid}")
            script, div = "", f'<div class="histo-err">{str(plot)}</div>'
    return div, script, size


def render_plots_html_and_js(plots: dict) -> tuple[list, str]:
    """Render plots

    Args:
        plots (dict): dictionary of plots

    Returns:
        tuple[ list, str ]: list of html and js script
    """
    results = [render(plotid, plots[plotid]) for plotid in list(plots.keys())]

    ret_html, ret_js = [], ""
    for div, script, size in results:
        ret_html.append({"code": div, "size": size})
        ret_js += script

    return ret_html, ret_js


@cache.memoize(timeout=600)
def find_canvas_in_file(img_path: str) -> ROOT.TCanvas | None:
    """Find ROOT Canvas in ROOT file

    Args:
        img_path (str): path of the ROOT file

    Returns:
        ROOT.TCanvas | None: canvas
    """
    if os.path.isfile(img_path):
        f = ROOT.TFile(img_path)
        for key in list(f.GetListOfKeys()):
            obj = key.ReadObj()
            if obj.InheritsFrom("TCanvas"):
                ret = copy.deepcopy(obj)
                f.Close()
                return ret
    logging.debug(f"File not found : {img_path}")
    return None


def load_image(img_path: str, plot) -> None:
    """Load a ROOT Canvas from a file and display on plot

    Args:
        img_path (str): path of the ROOT file
        plot (_type_): plot
    """
    try:
        canvas = find_canvas_in_file(img_path)
        if canvas:
            draw_root_canvas_on_plot(canvas, plot)
    except IOError as e:
        logging.debug(f"Got error {str(e)}")


def render_page(
    data_source: str,
    run_number: int,
    path: str,
    highlight_histo: bool,
    need_reference: bool = False,
    interval_size: int | None = None,
    interval_begin: datetime | None = None,
    trend_duration: int = 600,
    run_number_min: int = -1,
    run_number_max: int = -1,
    fill_number_min: int = -1,
    fill_number_max: int = -1,
    history_type: str = "Run",
    histos_contained: list | None = None,
    key_list: list[str] | None = None,
    histo_number: int | None = None,
    page_doc: str | None = None,
    compare_with_run: int = -1,
    compare_with_fill: int = -1,
) -> dict[str, any]:
    """Render page

    Args:
        data_source (str): data source
        run_number (int): run number
        path (str): path
        highlight_histo (bool): highlight histo
        need_reference (bool, optional): need a reference. Defaults to False.
        interval_size (int | None, optional): interval size. Defaults to None.
        interval_begin (datetime | None, optional): start of interval.
        Defaults to None.
        trend_duration (int, optional): trend duration in seconds.
        Defaults to 600.
        run_number_min (int, optional): minimum run number. Defaults to -1.
        run_number_max (int, optional): maximum run number. Defaults to -1.
        fill_number_min (int, optional): minimum fill number. Defaults to -1.
        fill_number_max (int, optional): maximum fill number. Defaults to -1.
        history_type (str, optional): history type. Defaults to 'Run'.
        histos_contained (list | None, optional): histo containes.
        Defaults to None.
        key_list (list[str] | None, optional): list of keys. Defaults to None.
        histo_number (int | None, optional): histo number. Defaults to None.
        page_doc (str | None, optional): page documentation. Defaults to None.
        compare_with_run (int, optional): run number to compare with. Defaults to -1.
        compare_with_fill (int, optional): fill number to compare with. Defaults to -1.

    Returns:
        dict[str, any]: information about histogram
    """
    if data_source == "trends":
        if path:
            if not path.startswith("Trends"):
                return {"error": "This is not a trend plot page"}

    try:
        if path:
            histos_contained, key_list, page_doc = get_histograms(path)
        # Put mother-less histograms at beginning
        histos_contained = sorted(
            histos_contained, key=lambda h: h.get("motherh", "") or ""
        )
        logging.debug("Got histograms, loading data")
        histo_values, ref_values, comparison_values, files_used, ref_used, comparison_used = get_data_for_request(
            key_list, histos_contained, need_reference, data_source, trend_duration,
            compare_with_run, compare_with_fill
        )
    except IOError:
        return {
            "success": False,
            "error": traceback.format_exc(),
        }
    except RuntimeError as e:
        return {
            "success": False,
            "error": str(e),
        }
    except TypeError as e:
        return {
            "success": False,
            "error": str(e),
        }

    plots = {}
    mothers = {
        histo["motherh"] for histo in histos_contained if histo.get("motherh", None)
    }

    for histo in histos_contained:
        if histo["taskname"] + "/" + histo["name"] not in histo_values:
            continue
        motherplot = None
        if histo.get("motherh", None):
            if histo.get("motherhinstance", "1") != "1":
                motherplot = plots[f"{histo['name']}/{histo['motherh']}"][0]
            else:
                motherplot = plots[histo["motherh"]][0]
        if history_type == "":
            history_type = "Run"
        extra_text = f" ({history_type} = {run_number})"
        if interval_begin:
            i_begin = datetime.strptime(interval_begin, "%m/%d/%Y %H:%M")
            i_dur = datetime.strptime(interval_size, "%H:%M")
            t_dur = timedelta(hours=i_dur.hour, minutes=i_dur.minute)
            extra_text = f" ({i_begin.strftime('%m/%d/%y %H:%M')} "
            f"to {(i_begin + t_dur).strftime('%m/%d/%y %H:%M')})"
        if data_source == "trends":
            if run_number_min != -1:
                extra_text = f" (Runs {run_number_min} to {run_number_max})"
            else:
                extra_text = f" (Fills {fill_number_min} to {fill_number_max})"
        try:
            rendered_plot = histo_draw(
                histodb_hist=histo,
                histo_data=histo_values[f"{histo['taskname']}/{histo['name']}"],
                draw_params=histo["display_options"],
                ref_data=ref_values.get(f"{histo['taskname']}/{histo['name']}")
                if need_reference
                else None,
                highlight=highlight_histo,
                motherplot=motherplot,
                is_mother=histo["name"] in mothers,
                extratext=extra_text,
                comparison_data=comparison_values.get(f"{histo['taskname']}/{histo['name']}",None) if (compare_with_run!=1 or compare_with_fill!=1) else None
            )
        except TypeError:
            rendered_plot = None

        if histo["display_options"].get("drawpattern", None):
            img_path = (
                f"/hist/Reference/{histo['taskname']}/"
                f"{histo['display_options'].get('drawpattern')}"
            )
            pattern_path = find_pattern_path(img_path, run_number)
            load_image(pattern_path, rendered_plot)

        if not motherplot:
            if data_source != "alarm":
                try:
                    size = (
                        histo["center_x"],
                        histo["center_y"],
                        histo["size_x"],
                        histo["size_y"],
                    )
                except KeyError:
                    return {
                        "success": False,
                        "error": "center_x, center_y, size_x or size_y not defined",
                    }
            else:
                size = (0.2, 0.2, 0.8, 1.0)
            if histo["name"] in plots:
                i = [*plots].count(histo["name"])
                plots[f"{histo['name']}/{i + 1}"] = (rendered_plot, size)
            else:
                plots[histo["name"]] = (rendered_plot, size)

    ret_divs, ret_script = render_plots_html_and_js(plots)

    return {
        "success": True,
        "divs": ret_divs,
        "script": ret_script,
        "files_used": files_used,
        "pagedoc": create_description_histo(histos_contained, histo_values, files_used, ref_used),
        "path": path,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
