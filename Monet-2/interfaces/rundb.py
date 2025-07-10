"""Interface to run database web API"""


import logging

import requests
from dateutil import tz
from flask import jsonify, render_template, request
from flask.wrappers import Response

import interfaces.dqdb as dqdb
from interfaces.dirac import (
    get_dq_flag_range_from_bkk,
    set_dq_flag_extra_range_in_bkk,
    set_dq_flag_range_in_bkk,
)
from interfaces.logbook import elog_flag_submission
from presenter.cache import cache
from presenter.blueprints._auth import requires_auth

from_zone = tz.gettz("UTC")
to_zone = tz.gettz("Europe/Paris")


def check_response(resp: int) -> bool:
    """Check response in order to activate cache or not. If response is
    0 then do not store in cache

    Args:
        resp (int): response value to check

    Returns:
        bool: True if 0, False if not
    """
    if resp != 0:
        return False
    return True


@cache.memoize(timeout=60, response_filter=check_response)
def get_latest_run_number(offline: bool = True, partition: str = "LHCb") -> int:
    """Get latest run number from run database

    Args:
        offline (bool, optional): True for offline DQ mode, False otherwise.
        Defaults to True.
        partition (str, optional): Name of the partition. Defaults to 'LHCb'.

    Returns:
        int: latest run number
    """
    if offline:
        try:
            r = requests.get(
                "http://rundb-internal.lbdaq.cern.ch/api/run/latest_offline"
            )
        except Exception:
            return 0
        return r.json().get("runid", 0)
    try:
        r = requests.get(
            "http://rundb-internal.lbdaq.cern.ch/api/"
            f"search?partition={partition}&rows=1"
        )
    except Exception:
        return 0
    runs = r.json().get("runs", None)
    if not runs:
        return 0
    if len(runs) == 0:
        return 0
    return runs[0].get("runid", 0)


# TODO: invalidate the cache when the endtime is not defined and increase after
# that the cache time
@cache.memoize(timeout=60)
def get_rundb_info(run_number: int) -> dict[str, float | int | str]:
    """Get run database information for the given run

    Args:
        run_number (int): run number

    Returns:
        dict[str, float | int | str]: run database information
    """
    if not isinstance(run_number, int):
        logging.error("ERROR - Bad run number type in function get_rundb_info")
    try:
        r = requests.get(f"http://rundb-internal.lbdaq.cern.ch/api/run/{run_number}")
        the_json = r.json()
    except Exception:
        # try once more
        try:
            r = requests.get(
                f"http://rundb-internal.lbdaq.cern.ch/api/run/{run_number}"
            )
            the_json = r.json()
        except Exception:
            return {
                "beamenergy": 0.0,
                "fillid": 0,
                "prev_runid": int(run_number) - 1,
                "programVersion": "UNKNOWN",
                "runid": run_number,
                "veloPosition": "UNKNOWN",
                "destination": "UNKNOWN",
                "startlumi": 0.0,
                "endlumi": 0.0,
                "state": "UNKNOWN",
                "program": "UNKNOWN",
                "LHCState": "UNKNOWN",
                "starttime": "2000-01-01T01:00:00",
                "magnetCurrent": "UNKNOWN",
                "run_state": 0,
                "runtype": "UNKNOWN",
                "endtime": "2000-01-01T02:00:00",
                "magnetState": "UNKNOWN",
                "activity": "UNKNOWN",
                "next_runid": run_number + 1,
                "partitionname": "UNKNOWN",
                "tck": "UNKNOWN",
                "partitionid": "UNKNOWN",
                "SMOG": "UNKNOWN",
            }
    return the_json


@cache.memoize(timeout=60)
def get_rundb_info_range(
    run_number_from: int, run_number_to: int
) -> dict[str, float | int | str]:
    """Get run database information for the given run range

    Args:
        run_number_from (int): first run number
        run_number_to (int): last run number

    Returns:
        dict[str, float | int | str]: run database information
    """
    if not isinstance(run_number_from, int) or not isinstance(run_number_to, int):
        logging.error("ERROR - Bad run number type in function get_rundb_info_range")
    try:
        payload = {"rows": -1, "runid_min": run_number_from, "runid_max": run_number_to}
        r = requests.get(
            "http://rundb-internal.lbdaq.cern.ch/api/search", params=payload
        )
        the_json = r.json()
    except Exception:
        # try once more
        try:
            payload = {
                "rows": -1,
                "runid_min": run_number_from,
                "runid_max": run_number_to,
            }
            r = requests.get(
                "http://rundb-internal.lbdaq.cern.ch/api/search", params=payload
            )
            the_json = r.json()
        except Exception:
            return {}
    return the_json


@cache.memoize(timeout=600)
def get_rundb_info_fill(fill_number: int) -> dict[str, float | int | str]:
    """Get run database information for a fill

    Args:
        fill_number (int): fill number

    Returns:
        dict[str, float | int | str]: information for the fill
    """
    if not isinstance(fill_number, int):
        logging.error("Bad fill number type in function get_rundb_info_fill")

    r = requests.get(f"http://rundb-internal.lbdaq.cern.ch/api/fill/{fill_number}/")

    try:
        r.raise_for_status()
    except Exception:
        return {
            "beamEnergy": 0.0,
            "fill_id": 0,
            "prev_fill_id": int(fill_number) - 1,
            "lumi_logged": 0.0,
            "start_date": "2000-01-01T01:00:00",
            "timestamp": "2000-01-01T02:00:00",
            "magnetState": "UNKNOWN",
            "nCollidingBunches": 0,
            "runs": [],
        }
    json_r = r.json()

    r1 = requests.get(
        f"http://rundb-internal.lbdaq.cern.ch/api/runs_in_fill/{fill_number}/"
    )

    try:
        r1.raise_for_status()
    except Exception:
        json_r.update({"runs": []})
        return json_r

    json_r1 = r1.json()
    # Keep only runs in LHCb partition
    list_of_runs = []
    for r in json_r1:
        if r.get("partitionname", "") == "LHCb" and r.get("activity", "").startswith("PHYSICS") :
            list_of_runs.append(r.get("runid", 0))
    json_r.update({"runs": list_of_runs})
    return json_r


@cache.memoize(timeout=3600)
def get_missing_detectors(partid: int) -> list[str]:
    """Decode partition ID from the run database to a list of
    missing detectors in the partition

    Args:
        partid (int): run database partition id

    Returns:
        list[str]: list of missing detectors
    """
    result = []
    if not partid & 0b100:
        result.append("VELOA")
    if not partid & 0b1000:
        result.append("VELOC")
    if not partid & 0b10000:
        result.append("RICH1")
    if not partid & 0b100000:
        result.append("UTA")
    if not partid & 0b1000000:
        result.append("UTC")
    if not partid & 0b10000000:
        result.append("SCIFIA")
    if not partid & 0b100000000:
        result.append("SCIFIC")
    if not partid & 0b1000000000:
        result.append("RICH2")
    if not partid & 0b10000000000:
        result.append("PLUME")
    if not partid & 0b100000000000:
        result.append("ECAL")
    if not partid & 0b1000000000000:
        result.append("HCAL")
    if not partid & 0b10000000000000:
        result.append("MUONA")
    if not partid & 0b100000000000000:
        result.append("MUONC")
    return result


def get_rundb_info_html(
    run_number: int, fill_number: int, run_flag: str, system_flags: list[str]
) -> str:
    """Display the run database information in HTML format

    Args:
        run_number (int): run number
        fill_number (int): fill number
        run_flag (str): global dataquality flag for this run
        system_flags (list[str]): list of extra dataquality flags

    Returns:
        str: HTML string
    """
    if int(fill_number) == -1:
        info = get_rundb_info(int(run_number))
        assert isinstance(info, dict)

        if "avMu" not in info:
            info["avMu"] = 0.0

        # Prepare
        info["avMu"] = float(info["avMu"])
        info["flag"] = run_flag
        info["system_flags"] = system_flags

        try:
            info["endlumi"] = float(info["endlumi"]) / 1000000.0
        except Exception:
            pass
        if info["starttime"] == info["endtime"]:
            info["endtime"] = ""

        partid = info["partitionid"]
        if partid == 32764:
            info["partitionid"] = "complete"
        else:
            missing = get_missing_detectors(partid)
            r = "all but "
            for d in missing:
                r += d + " "
            info["partitionid"] = r
        return render_template("run-info.html", **info)
    else:
        info = get_rundb_info_fill(int(fill_number))
        return render_template("fill-info.html", **info)


@requires_auth
def rundb_info_view() -> Response:
    """Returns the run database information
    Parameters are taken from the HTTP request, from the request.args variable

    Returns:
        Response: HTML response
    """
    mode = True if request.args.get("mode") == "offline" else False
    is_online = True if request.args.get("mode") == "online" else False
    partition = request.args.get("partition")
    rn = (
        request.args.get("run")
        or request.args.get("runnumber")
        or get_latest_run_number(mode, partition)
    )
    fill = request.args.get("fill", -1)

    flag, rundb_info = "Not specified", "Not specified"
    system_flags = {}
    if fill == -1:
        if not is_online:
            try:
                info = get_rundb_info(int(rn))
                assert isinstance(info, dict)
                if info.get("state","MIGRATED") in ["MIGRATED"] and info.get("destination","OFFLINE")=="OFFLINE":
                    flag, system_flags = dqdb.get_dq_flag(rn)
            except Exception:
                flag = "Not specified"
                system_flags = {}
    try:
        rundb_info = get_rundb_info_html(rn, fill, flag, system_flags)
    except BaseException:
        pass

    return jsonify(
        {
            "success": True,
            "rundb_info": rundb_info,
            "run_flag": flag,
            "run_system_flags": system_flags,
        }
    )


@requires_auth
def rundb_info_range() -> Response:
    """Returns the run database information for a given range
    Parameters are taken from the HTTP request, from the request.args variable

    Returns:
        Response: HTML response
    """
    run_start = int(request.args.get("run_start"))
    run_end = int(request.args.get("run_end"))

    try:
        rundb_info = get_rundb_info_range(run_start, run_end)
    except BaseException:
        pass

    if rundb_info.get("totalResults", 0) == 0:
        return jsonify({"successs": False})

    runs = [r.get("runid", 0) for r in rundb_info["runs"] if r.get("partitionname","LHCb") == "LHCb" and r.get("destination","OFFLINE") == "OFFLINE" and r.get("state","MIGRATED") in ["MIGRATED"] ]
    dirac_flags = get_dq_flag_range_from_bkk(runs)
    keep_only = ["runid", "partitionname"]
    results = []

    dqdb_flags = dqdb.get_dq_flag_range_from_dqdb(runs)

    for r in rundb_info["runs"]:
        if r.get("partitionname","LHCb") == "LHCb" and r.get("destination","OFFLINE") == "OFFLINE" and r.get("state","MIGRATED") in ["MIGRATED"]:
            d = {key: r[key] for key in keep_only}
            d["flag_bkk"] = dirac_flags.get(str(d["runid"]), ("UNCHECKED",))[0]
            d["flag_bkk_extra"] = dirac_flags.get(str(d["runid"]), ("UNCHECKED", [""]))[1]
            d["flag_dqdb"] = dqdb_flags.get(d["runid"], ("UNCHECKED",))[0]
            d["flag_dqdb_extra"] = dqdb_flags.get(d["runid"], ("UNCHECKED", [""]))[1]
            results.append(d)

    return jsonify({"success": True, "rundb_info": results})


@requires_auth
def flag_run_range() -> Response:
    """Flags a range of runs with the given global flag

    Returns:
        Response: HTML response
    """
    run_start = int(request.args.get("run_start"))
    run_end = int(request.args.get("run_end"))
    global_flag = request.args.get("flag")
    elog_message = request.args.get("elog_message")

    try:
        rundb_info = get_rundb_info_range(run_start, run_end)
    except BaseException:
        pass

    if rundb_info.get("totalResults", 0) == 0:
        return jsonify({"successs": False})

    runs = [r.get("runid", 0) for r in rundb_info["runs"] if r.get("partitionname","LHCb") == "LHCb" and r.get("destination","OFFLINE") == "OFFLINE" and r.get("state","MIGRATED") in ["MIGRATED"]]

    if not set_dq_flag_range_in_bkk(runs, global_flag):
        return jsonify({"successs": False})

    if not dqdb.set_dq_flag_range_from_dqdb(runs, global_flag):
        return jsonify({"successs": False})

    # Write message in elog (one entry per run number)
    for r in runs:
        if not elog_flag_submission(r, global_flag, elog_message):
            return jsonify({"successs": False})

    return jsonify({"success": True})


@requires_auth
def flag_extra_run_range() -> Response:
    """Flags a range of runs with the given global flag

    Returns:
        Response: HTML response
    """
    run_start = int(request.args.get("run_start"))
    run_end = int(request.args.get("run_end"))
    extra_flag = [request.args.get("extra_flag")]

    try:
        rundb_info = get_rundb_info_range(run_start, run_end)
    except BaseException:
        pass

    if rundb_info.get("totalResults", 0) == 0:
        return jsonify({"successs": False})

    runs = [r.get("runid", 0) for r in rundb_info["runs"] if r.get("partitionname","LHCb") == "LHCb" and r.get("destination","OFFLINE") == "OFFLINE" and r.get("state","MIGRATED") in ["MIGRATED"]]

    if not set_dq_flag_extra_range_in_bkk(runs, extra_flag):
        return jsonify({"successs": False})

    if not dqdb.set_dq_flag_extra_range_from_dqdb(runs, extra_flag):
        return jsonify({"successs": False})

    return jsonify({"success": True})


@requires_auth
def rundb_json() -> Response:
    """Returns run database information.
    Parameters are taken from the HTTP arguments in the requests.args variable

    Returns:
        Response: HTLM response
    """
    rn = request.args.get("run")
    try:
        rundb_info = get_rundb_info(int(rn))
    except BaseException:
        rundb_info = None
        pass

    return jsonify({"success": True, "rundb_info": rundb_info})


def online_runnumber_view() -> Response:
    """Get information for the latest run

    Returns:
        Response: HTML response
    """
    mode = True if request.args.get("mode") == "offline" else False
    partition = request.args.get("partition")
    rn = get_latest_run_number(mode, partition)
    return jsonify({"run_number": rn})


def get_all_runs_in_2025() -> Response:
    """Get list of all 2025 runs sent offline

    Returns: 
        Response: HTML response
    """
    params = {
        "starttime": '2025-05-01T00:00:00',
        "destination": 'OFFLINE',
        "rows": -1
    }
    try:
        r = requests.get(f"http://rundb-internal.lbdaq.cern.ch/api/search", params = params)
    except Exception:
        return jsonify({"status": False})
    runs = r.json().get('runs',None)
    if not runs:
        return jsonify({"status": False})
    result = []
    for r in runs:
        result.append( { 
            'runid': r.get('runid'), 
            'runtype': r.get('runtype'), 
            'destination': r.get('destination'), 
            'tck': r.get('tck'), 
            'fillid': r.get('fillid'), 
            'startlumi': r.get('startlumi'), 
            'endlumi': r.get('endlumi'), 
            'starttime': r.get('starttime'), 
            'endtime': r.get('endtime'), 
            'avLumi': r.get('avLumi'), 
            'avMu': r.get('avMu'),
            'SMOG': r.get('SMOG'),
            'SMOGLumi': r.get('SMOGLumi'),
        })
    return jsonify({"status": True, "runs": result })