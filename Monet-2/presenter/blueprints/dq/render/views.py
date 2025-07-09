"""Renderer modules"""
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
import traceback
from datetime import datetime

from flask import abort, current_app, jsonify, request

import interfaces.rundb
import renderer.logic
from presenter.blueprints._auth import requires_auth
from interfaces.monitoringhub import monitoringhub_prepare_file


def local_renderer():
    """Local renderers"""

    def render(**kwargs):
        kwargs["need_reference"] = kwargs["reference"] == "activated"
        del kwargs["reference"]

        result = renderer.logic.render_page(**kwargs)

        result["histo_number"] = kwargs["histo_number"]
        return jsonify(result)

    return render


@requires_auth
def histos_list_for_path():
    path = request.args.get("path")
    data_source = request.args.get("data_source")

    if data_source == "trends":
        if not path.startswith("Trends"):
            abort(404, description="This is not a trend plot page")

    try:
        histos_contained, key_list, page_doc = renderer.logic.get_histograms(path)
    except IOError:
        abort(404, description=traceback.format_exc())
    except RuntimeError as e:
        abort(404, description=str(e))
    return jsonify(
        {
            "histo_list": histos_contained,
            "key_list": key_list,
            "pagedoc": renderer.logic.create_initial_page_doc(page_doc),
        }
    )

@requires_auth
def prepare_files():
    tasks = list(set(request.form.getlist("tasks[]")))
    number_of_tasks = len(tasks)
    missing_tasks = []
    if not tasks:
        abort(404, description="Empty list")
    for t in tasks:
        mt = monitoringhub_prepare_file(
            partition = request.form.get("partition"), 
            task = t, 
            history_type = request.form.get("history_type"), 
            run_number = request.form.get("run_number"), 
            interval_begin = request.form.get("interval_begin"), 
            interval_size = request.form.get("interval_size"),
            number_of_tasks = number_of_tasks )
        if mt: 
            missing_tasks.append(mt)

    if len(missing_tasks) != 0:
        text_missing = "" 
        for i in missing_tasks:
            text_missing = text_missing + ", " + i
        return jsonify({"message": "Savesets do not exist for that run for tasks " + text_missing})
    return jsonify({"message": "all files are ready"})


@requires_auth
def single_histo():
    renderers = {
        # data source -> renderer
        "online": local_renderer(),
        "offline": local_renderer(),
        "history": local_renderer(),
        "history_interval": local_renderer(),
        "alarm": local_renderer(),
        "sim_dq": local_renderer(),
        "trends": local_renderer(),
    }

    try:
        key_list = json.loads(request.form["key_list"])
    except (json.JSONDecodeError, KeyError):
        key_list = None

    try:
        histos_contained = json.loads(request.form["histos_contained"])
    except (json.JSONDecodeError, KeyError):
        histos_contained = None

    datasource = request.form.get("data_source")
    the_renderer = renderers[datasource]

    the_run_number = 0
    try:
        the_run_number = int(request.form.get("run_number", 0))
    except IOError:
        the_run_number = 0
    except ValueError:
        the_run_number = 0

    compare_with_run = -1
    try: 
        compare_with_run = int( request.form["compare_with_run"] )
    except (IOError, ValueError):
        logging.error("Bad comparison run number given")
        compare_with_run = -1

    compare_with_fill = -1
    try: 
        compare_with_fill = int( request.form["compare_with_fill"] )
    except (IOError, ValueError):
        logging.error("Bad comparison fill number given")
        compare_with_fill = -1

    try:
        result = the_renderer(
            data_source=datasource,
            run_number=the_run_number,
            path=None,
            highlight_histo=request.form.get("highlight_histo"),
            reference=request.form.get("reference"),
            interval_begin=request.form.get("interval_begin", 0),
            interval_size=request.form.get("interval_size", 0),
            trend_duration=request.form.get("trend_duration", 600),
            run_number_min=request.form.get("run_number_min", -1),
            run_number_max=request.form.get("run_number_max", -1),
            fill_number_min=request.form.get("fill_number_min", -1),
            fill_number_max=request.form.get("fill_number_max", -1),
            history_type=request.form.get("history_type", "Run"),
            histos_contained=histos_contained,
            key_list=key_list,
            histo_number=request.form.get("histo_number"),
            compare_with_run=compare_with_run,
            compare_with_fill=compare_with_fill,
        )
    except KeyError as e:
        abort(404, description=request.form.get("histo_number") + ":" + str(e))
    return result


@requires_auth
def histos_for_path():
    """Get renderer for histos"""
    renderers = {
        # data source -> renderer
        "online": local_renderer(),
        "offline": local_renderer(),
        "history": local_renderer(),
        "history_interval": local_renderer(),
        "alarm": local_renderer(),
        "sim_dq": local_renderer(),
        "trends": local_renderer(),
    }

    datasource = request.args.get("data_source")
    the_renderer = renderers[datasource]

    the_run_number = 0
    try:
        the_run_number = int(request.args.get("run_number", 0))
    except IOError:
        the_run_number = 0

    return the_renderer(
        data_source=datasource,
        run_number=the_run_number,
        path=request.args.get("path"),
        highlight_histo=request.args.get("highlight_histo"),
        reference=request.args.get("reference"),
        interval_begin=request.args.get("interval_begin", 0),
        interval_size=request.args.get("interval_size", 0),
        trend_duration=request.args.get("trend_duration", 600),
        run_number_min=request.args.get("run_number_min", -1),
        run_number_max=request.args.get("run_number_max", -1),
        fill_number_min=request.args.get("fill_number_min", -1),
        fill_number_max=request.args.get("fill_number_max", -1),
        history_type=request.args.get("history_type", "Run"),
    )
