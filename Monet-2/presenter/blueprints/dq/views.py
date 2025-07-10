"""Bokeh views module"""


import traceback

from flask import (
    Flask,
    current_app,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask.wrappers import Response

import interfaces.dqdb as dqdb
import interfaces.rundb
import interfaces.simproddb
from interfaces.logbook import (
    cleanup_image_pathes,
    construct_elog_link,
    elog_flag_submission,
    save_images_to_temp_files,
    send_to_elog,
)
from interfaces.monitoringhub import (
    monitoringhub_get_online_partitions,
    monitoringhub_get_saveset_partitions,
)
from presenter.blueprints._auth import get_info, requires_auth
from presenter.blueprints._user_settings import UserSettings

app = Flask(__name__)
settings = UserSettings()


@requires_auth
def offline_dq() -> str:
    """Offline DQ page

    Returns:
        str: HTML page
    """
    g.active_page = "offline_dq"
    settings.set_options_file(get_info("cern_uid"))
    page = render_template(
        "dq.html",
        LOAD_FROM_DB_FLAG="false",
        RUN_NMBR=settings.get_property("run_number:offline"),
        DQ_FLAG=dqdb.get_dq_flag(settings.get_property("run_number:offline"))[0],
        REFERENCE_STATE=settings.get_property("reference_state"),
        USERNAME=get_info("preferred_username"),
        FULLNAME=get_info("name"),
        PROJECTNAME="Offline DQM",
        run_problem_status={"status": "primary"},
        asset_name="js_offline_dq_modules",
    )
    return page


@requires_auth
def trends() -> str:
    """Trends page

    Returns:
        str: HTML string
    """
    g.active_page = "trends"
    settings.set_options_file(get_info("cern_uid"))
    page = render_template(
        "dq.html",
        LOAD_FROM_DB_FLAG="false",
        RUN_NMBR_FROM=settings.get_property("run_number_from:trends"),
        RUN_NMBR_TO=settings.get_property("run_number_to:trends"),
        USERNAME=get_info("preferred_username"),
        FULLNAME=get_info("name"),
        PROJECTNAME="DQ Trends",
        run_problem_status={"status": "primary"},
        DISPLAYFILLS_STATE=settings.get_property("displayfills_state"),
        asset_name="js_trend_dq_modules",
    )
    return page


def _get_run_number_context() -> str:
    """Get run number context

    Returns:
        str: run number context
    """
    if "offline_dq" in request.url or "history_dq" in request.url:
        return "run_number:offline"
    elif "sim_dq" in request.url:
        return "run_number:simulation"
    return "run_number:unknown_context"


def create_run_switcher(blueprint_name: str) -> Response:
    """Switch run

    Args:
        blueprint_name (str): name of the blueprint

    Returns:
        Response: HTML response
    """

    @requires_auth
    def switch_run():
        run_number = request.args.get("run_number")
        procpass = request.args.get("procpass")
        reference_state = request.args.get("reference_state")
        selected_page = request.args.get("selected_page")
        partition = request.args.get("partition")
        interval_begin = request.args.get("interval_begin")
        interval_size = request.args.get("interval_size")
        prev_event_type = request.args.get("prev_event_type")
        prev_sim_hist_file = request.args.get("prev_sim_hist_file")
        data_source = request.args.get("data_source", False)
        settings.set_options_file(get_info("cern_uid"))
        settings.set_property(_get_run_number_context(), run_number)
        if reference_state:
            settings.set_property("reference_state", reference_state)
        if interval_size:
            settings.set_property("interval_size", interval_size)
        if interval_begin:
            settings.set_property("interval_begin", interval_begin)
        if prev_event_type:
            settings.set_property("prev_event_type", prev_event_type)
        if prev_sim_hist_file:
            settings.set_property("prev_sim_hist_file", prev_sim_hist_file)

        return redirect(
            url_for(
                blueprint_name,
                run_number=run_number,
                procpass=procpass,
                reference_state=reference_state,
                selected_page=selected_page,
                partition=partition,
                interval_size=interval_size,
                interval_begin=interval_begin,
                prev_event_type=prev_event_type,
                prev_sim_hist_file=prev_sim_hist_file,
                data_source=data_source,
            )
        )

    return switch_run


@requires_auth
def online_dq() -> str:
    """Online DQ mode

    Returns:
        str: HTML string
    """
    g.active_page = "online_dq"
    try:
        settings.set_options_file(get_info("cern_uid"))
    except KeyError:
        pass
    partitions = []
    try:
        monhub_config = current_app.config["MONHUB_CONFIG"]
        dim_dns_node = current_app.config["DIM_DNS_NODE"]
        partitions = monitoringhub_get_online_partitions(monhub_config, dim_dns_node)
    except KeyError:
        partitions = []
    page = render_template(
        "dq.html",
        LOAD_FROM_DB_FLAG="false",
        REFERENCE_STATE=settings.get_property("reference_state"),
        USERNAME=get_info("preferred_username"),
        FULLNAME=get_info("name"),
        PROJECTNAME="Online DQM",
        partitions=partitions,
        selected_partition=request.args.get("partition", "LHCb"),
        run_problem_status=current_app.config["PROBLEMDB"].get_run_status(
            online=True,
            run_id=interfaces.rundb.get_latest_run_number(
                False, request.args.get("partition", "LHCb")
            ),
        ),
        asset_name="js_online_dq_modules",
    )
    return page


@requires_auth
def history_dq() -> str:
    """Page for history mode

    Returns:
        str: HTML string
    """
    g.active_page = "history_dq"
    settings.set_options_file(get_info("cern_uid"))
    monhub_config = current_app.config["MONHUB_CONFIG"]
    the_path = current_app.config["PATH_HISTOS"]
    partitions = monitoringhub_get_saveset_partitions(monhub_config, the_path)

    # get partition from rundb
    try:
        rn = int(settings.get_property("run_number:offline"))
    except KeyError:
        rn = 0
    except ValueError:
        rn = 0
    if request.args.get("data_source", "") == "history_interval":
        part = request.args.get("partition", "LHCb")
    else:
        dbinf = interfaces.rundb.get_rundb_info(rn)
        part = dbinf.get("partitionname", request.args.get("partition", "LHCb"))

    page = render_template(
        "dq.html",
        LOAD_FROM_DB_FLAG="false",
        RUN_NMBR=settings.get_property("run_number:offline"),
        REFERENCE_STATE=settings.get_property("reference_state"),
        INTERVAL_BEGIN=settings.get_property("interval_begin"),
        INTERVAL_SIZE=settings.get_property("interval_size"),
        USERNAME=get_info("preferred_username"),
        FULLNAME=get_info("name"),
        PROJECTNAME="History Mode",
        partitions=partitions,
        selected_partition=part,
        run_problem_status=current_app.config["PROBLEMDB"].get_run_status(
            online=False, run_id=settings.get_property("run_number:offline")
        ),
        asset_name="js_history_dq_modules",
    )
    return page


@requires_auth
def sim_dq() -> str:
    """Sim DQ page

    Returns:
        str: HTML string
    """
    settings.set_options_file(get_info("cern_uid"))
    page = render_template(
        "dq.html",
        LOAD_FROM_DB_FLAG="false",
        RUN_NMBR=settings.get_property("run_number:simulation"),
        REFERENCE_STATE=settings.get_property("reference_state"),
        USERNAME=get_info("preferred_username"),
        FULLNAME=get_info("name"),
        PROJECTNAME="SimDQ",
        asset_name="js_sim_dq_modules",
    )
    return page


@requires_auth
def get_next_runnumber_rundb() -> Response:
    """Get next run number information from Run DB

    Returns:
        Response: HTML response
    """
    unchecked_only = request.args.get(
        "unchecked_only", default=False, type=lambda v: v.lower() == "true"
    )
    migrated_only = request.args.get(
        "migrated_only", default=False, type=lambda v: v.lower() == "true"
    )
    run_number = int(request.args.get("runnumber"))
    while True:
        info = interfaces.rundb.get_rundb_info(run_number)
        if not isinstance(info, dict):
            return jsonify(
                {
                    "success": False,
                    "data": {
                        "message": "Error obtaining next run: seems like RunDB"
                        " does not have one."
                    },
                }
            )
        if "next_runid" not in info:
            return jsonify(
                {
                    "success": False,
                    "data": {
                        "message": "Error obtaining next run: seems like RunDB"
                        " does not have one."
                    },
                }
            )

        if unchecked_only:
            next_run_number = info["next_runid"]
            flag = dqdb.get_dq_flag(next_run_number)[0]
            if flag == "UNCHECKED":
                if migrated_only:
                    info_next = interfaces.rundb.get_rundb_info(next_run_number)
                    dest = info_next["destination"]
                    state = info_next["state"]
                    if dest == "OFFLINE" and state in ["MIGRATED"]:
                        return jsonify(
                            {"success": True, "data": {"runnumber": next_run_number}}
                        )
                else:
                    return jsonify(
                        {"success": True, "data": {"runnumber": next_run_number}}
                    )
            run_number = info["next_runid"]
        else:
            if migrated_only:
                next_run_number = info["next_runid"]
                info_next = interfaces.rundb.get_rundb_info(next_run_number)
                dest = info_next["destination"]
                state = info_next["state"]
                if dest == "OFFLINE" and state in ["MIGRATED"]:
                    return jsonify(
                        {"success": True, "data": {"runnumber": next_run_number}}
                    )
            return jsonify(
                {"success": True, "data": {"runnumber": info.get("next_runid", 0)}}
            )
        run_number = next_run_number


@requires_auth
def save_run_flag() -> Response:
    """Save run flag

    Returns:
        Response: HTML response
    """
    # set current option file
    settings.set_options_file(get_info("cern_uid"))

    try:
        run_number = int(request.form["run_number"])
    except KeyError as f:
        return jsonify(
            {
                "saved_flag": "Unknown",
                "error": [str(f)],
                "explanation": str(f),
            }
        )
    new_flag = str(request.form["flag"])
    new_smog_flag = str(request.form["smog_flag"])
    elog_comment = str(request.form["elog_comment"])

    app.logger.debug(f"Setting flag {new_flag} for run {run_number}")

    previous_flag, previous_system_flags = dqdb.get_dq_flag(run_number)
    dqdb_submitted = False

    try:
        app.logger.debug("Setting DQDB flag")
        ext_flags = []
        if new_smog_flag == "OK":
            ext_flags.append("SMOG2")
        ext_flags.sort()
        ret = dqdb.set_dq_flag(run_number, new_flag, extra_flags=ext_flags)
        assert ret, "Could not save to DQDB"
        dqdb_submitted = True

        app.logger.debug("Submitting to elog")
        elog_flag_submission(run_number, new_flag, elog_comment)
        return jsonify(
            {
                "saved_flag": new_flag,
                "explanation": "Success! Flag saved to bookkeeping. "
                "We also created an ELOG entry about it.",
            }
        )
    except NameError as e:
        return jsonify(
            {
                "saved_flag": "unknown",
                "error": str(e),
                "explanation": str(e),
            }
        )
    except IOError as e:
        try:
            if dqdb_submitted:
                return jsonify(
                    {
                        "saved_flag": new_flag,
                        "error": "Error submitting to elog",
                        "traceback": str(traceback.format_exc()),
                        "stderr": getattr(e, "stderr", ""),
                        "stdout": getattr(e, "stdout", ""),
                        "explanation": "Error submitting to ELOG. Flag was set in Dirac"
                        f"to `{new_flag}`.",
                    }
                )

            ret = dqdb.set_dq_flag(
                run_number, previous_flag, extra_flags=previous_system_flags
            )
            assert ret, "DQDB flag revert failed"

            traceback.print_exc()
            app.logger.error(e)

            return jsonify(
                {
                    "saved_flag": previous_flag,
                    "error": str(e),
                    "traceback": str(traceback.format_exc()),
                    "stderr": getattr(e, "stderr", ""),
                    "stdout": getattr(e, "stdout", ""),
                    "explanation": "Error occured. DQDB flag reverted"
                    f" to `{previous_flag}`",
                }
            )
        except KeyError as f:
            return jsonify(
                {
                    "saved_flag": "Unknown",
                    "error": [str(e), str(f)],
                    "explanation": str(e) + "\n" + str(f),
                }
            )


@requires_auth
def elog_submit() -> Response:
    """Submit message to ELOG

    Returns:
        Response: HTML response
    """
    app.logger.warning("Message received for ELOG")
    data = request.get_json()
    image_path_list = []
    ok = False
    ret_msg = None
    try:
        image_path_list = save_images_to_temp_files(data["images"])
        the_system = data["subsystem"]
        if data["logbook"] == "Shift":
            if "RTA-HLT1" in data["subsystem"]:
                the_system = "HLT1"
            elif "RTA-HLT2" in data["subsystem"]:
                the_system = "HLT2"
            elif "RTA-AC" in data["subsystem"]:
                the_system = "ALIGNMENT"

        app.logger.debug(f"Submitting to elog with attachements: {image_path_list}")
        result = send_to_elog(
            logbook=data["logbook"],
            author=data["author"],
            system=the_system,
            subject=data["subject"],
            run_number=data.get("run_number", ""),
            text=data["text"],
            level=data["level"],
            attachements=image_path_list,
        )

        if data["submit_to_problemdb"] != "yes":
            ok = True
            return jsonify({"ok": ok, "message": ret_msg})

        ret_msg = "Submitted to ELOG, but failed to submit to ProblemDB"

        link = construct_elog_link(result, data["logbook"])

        problemdb = current_app.config["PROBLEMDB"]
        problemdb.submit_problem(
            username=data["author"],
            system=data["subsystem"],
            title=data["subject"],
            message=data["text"],
            link=link,
            run_number=data.get("run_number", ""),
        )

        ok = True
    except KeyError as e:
        ok = False
        tb = traceback.format_exc()
        ret_msg = str(e)
        app.logger.error(str(e))
        app.logger.error(tb)
    finally:
        cleanup_image_pathes(image_path_list)
    return jsonify({"ok": ok, "message": ret_msg})


@requires_auth
def change_reference_state() -> Response:
    """Toggle reference plot

    Returns:
        Response: HTML response
    """
    state = request.args.get("state")

    settings.set_property("reference_state", state)

    d = dict(success=True, data=dict(message="Set State:" + str(state)))
    return jsonify(d)


@requires_auth
def get_previous_runnumber() -> Response:
    """Get previous run information

    Returns:
        Response: HTML response
    """
    rn = int(request.args.get("runnumber"))
    unchecked_only = request.args.get("unchecked_only", "false") == "true"

    # set database reference
    dataqualitydb = current_app.config["DQDB"]
    if not dataqualitydb:
        return jsonify(
            {
                "success": False,
                "data": {"runnumber": -1, "message": "no dataquality db defined"},
            }
        )
    if unchecked_only:
        prn = dataqualitydb.prevOnlineDQRunUnchecked(rn)
    else:
        prn = dataqualitydb.prevOnlineDQRun(rn)

    if prn:
        return jsonify({"success": True, "data": {"runnumber": prn}})
    if unchecked_only:
        info = interfaces.rundb.get_rundb_info(rn)
        next_run_number = info["next_runid"]
        flag = dqdb.get_dq_flag(next_run_number)[0]
        if flag == "UNCHECKED":
            return jsonify({"success": True, "data": {"runnumber": next_run_number}})
    else:
        return jsonify({"success": True, "data": {"runnumber": info["next_runid"]}})


@requires_auth
def get_latest_runnumber_rundb() -> Response:
    """Get latest run information

    Returns:
        Response: HTML response
    """
    return jsonify(
        {
            "success": True,
            "data": {"runnumber": interfaces.rundb.get_latest_run_number()},
        }
    )


@requires_auth
def get_previous_runnumber_rundb() -> Response:
    """Get previous run information from Run DB

    Returns:
        Response: HTML response
    """
    unchecked_only = request.args.get(
        "unchecked_only", default=False, type=lambda v: v.lower() == "true"
    )
    migrated_only = request.args.get(
        "migrated_only", default=False, type=lambda v: v.lower() == "true"
    )
    run_number = int(request.args.get("runnumber"))
    while True:
        info = interfaces.rundb.get_rundb_info(run_number)
        assert isinstance(info, dict)
        if unchecked_only:
            prev_run_number = info["prev_runid"]
            flag = dqdb.get_dq_flag(prev_run_number)[0]
            if flag == "UNCHECKED":
                if migrated_only:
                    info_prev = interfaces.rundb.get_rundb_info(prev_run_number)
                    dest = info_prev["destination"]
                    state = info_prev["state"]
                    if dest == "OFFLINE" and state in ["MIGRATED"]:
                        return jsonify(
                            {"success": True, "data": {"runnumber": prev_run_number}}
                        )
                else:
                    return jsonify(
                        {"success": True, "data": {"runnumber": prev_run_number}}
                    )
            run_number = info["prev_runid"]
        else:
            if migrated_only:
                prev_run_number = info["prev_runid"]
                info_prev = interfaces.rundb.get_rundb_info(prev_run_number)
                dest = info_prev["destination"]
                state = info_prev["state"]
                if dest == "OFFLINE" and state in ["MIGRATED"]:
                    return jsonify(
                        {"success": True, "data": {"runnumber": prev_run_number}}
                    )
            return jsonify(
                {"success": True, "data": {"runnumber": info.get("prev_runid", 0)}}
            )
        run_number = prev_run_number


@requires_auth
def set_request_id() -> Response:
    """Set request ID for simulation DQ

    Returns:
        Response: HTML response
    """
    req_id = request.args.get("reqid", type=str).rjust(8, "0")
    if req_id not in current_app.config["SIMPRODDB"].valid_request_ids:
        return jsonify({"success": False, "data": "Invalid request ID"})
    settings.set_property(_get_run_number_context(), int(req_id))
    settings.set_property("prev_event_type", request.args.get("prev_event_type"))
    settings.set_property("sim_hist_file", request.args.get("sim_hist_file"))
    evt_types = current_app.config["SIMPRODDB"].get_event_types(req_id)
    sim_hist_files = {}
    for evt in evt_types:
        sim_hist_files[evt] = current_app.config["SIMPRODDB"].get_filenames(req_id, evt)

    return jsonify({"success": True, "data": sim_hist_files})


@requires_auth
def get_next_request_id() -> Response:
    """Get next request ID for simulation DQ

    Returns:
        Response: HTML Response
    """
    req_id = request.args.get("reqid", type=str).rjust(8, "0")
    # Lookup list of request ids, move onto the next one
    req_ids = current_app.config["SIMPRODDB"].get_request_ids()
    req_id_index = req_ids.index(req_id)
    if req_id_index + 1 > len(req_ids) - 1:
        return jsonify({"success": False, "data": "No more request IDs"})
    return jsonify({"success": True, "data": {"reqid": int(req_ids[req_id_index + 1])}})


@requires_auth
def get_previous_request_id() -> Response:
    """Get next request ID for simulation DQ

    Returns:
        Response: HTML response
    """
    req_id = request.args.get("reqid", type=str).rjust(8, "0")
    # Lookup list of request ids, move onto the previous one
    req_ids = current_app.config["SIMPRODDB"].get_request_ids()
    req_id_index = req_ids.index(req_id)
    if req_id_index - 1 < 0:
        return jsonify({"success": False, "data": "No more request IDs"})
    return jsonify({"success": True, "data": {"reqid": int(req_ids[req_id_index - 1])}})


@requires_auth
def get_latest_request_id() -> Response:
    """Get next latest ID for simulation DQ

    Returns:
        Response: HTML response
    """
    req_id = int(current_app.config["SIMPRODDB"].get_request_ids()[-1])
    return jsonify({"success": True, "data": {"reqid": req_id}})


@requires_auth
def get_oldest_request_id() -> Response:
    """Get oldest latest ID for simulation DQ

    Returns:
        Response: HTML response
    """
    req_id = int(current_app.config["SIMPRODDB"].get_request_ids()[0])
    return jsonify({"success": True, "data": {"reqid": req_id}})


@requires_auth
def get_req_info() -> dict[str, any]:
    """Get request info

    Returns:
        dict[str, any]: dictionnary with informations on the production request
    """
    prod_info = current_app.config["SIMPRODDB"].get_prod_info(
        request.args.get("reqid"),
        request.args.get("eventType"),
        request.args.get("simHistFile"),
    )
    prod_info["success"] = True
    return prod_info


@requires_auth
def change_displayfills_state() -> Response:
    """Toggle fills boundaries

    Returns:
        Response: HTML response
    """
    state = request.args.get("state")

    settings.set_property("displayfills_state", state)

    d = dict(success=True, data=dict(message="Set State:" + str(state)))
    return jsonify(d)

@requires_auth
def page_documentation() -> str:
    """Page documentation page

    Returns:
        str: HTML string
    """
    settings.set_options_file(get_info("cern_uid"))
    page = render_template(
        "dq.html",
        LOAD_FROM_DB_FLAG="false",
        RUN_NMBR=settings.get_property("run_number:simulation"),
        REFERENCE_STATE=settings.get_property("reference_state"),
        USERNAME=get_info("preferred_username"),
        FULLNAME=get_info("name"),
        PROJECTNAME="Page Documentation",
        asset_name="js_page_documentation_modules",
    )
    return page
