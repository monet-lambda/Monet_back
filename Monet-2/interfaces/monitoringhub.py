"""Interface functions to the monitoring hub"""
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

import bz2
import copy
from datetime import datetime
import json
import logging
import random
import string
from base64 import b64decode

import interfaces.rundb
import MonitoringHub
import ROOT
import urllib3
from MonitoringHub.api import default_api
from data_load.obtainers.utilities import rand_str
from presenter.cache import cache
from flask import current_app, abort
from threading import Thread

def monitoringhub_trend_loader(
    hid, start_time, end_time, hub_configuration, wincc_server, source="wincc"
):
    """load trend plots via monitoring hub"""
    with MonitoringHub.ApiClient(hub_configuration) as api_client:
        api_instance = default_api.DefaultApi(api_client)
        partition = "LHCb"
        server = wincc_server
        task = hid["taskname"][6:]
        entity = hid["name"]
        s_time = datetime.fromtimestamp(start_time)
        e_time = datetime.fromtimestamp(end_time)

        try:
            api_response = api_instance.api_hub_get_data(
                source,
                partition,
                task,
                entity,
                server=server,
                _request_timeout=30,
                time_start=s_time,
                time_end=e_time,
                sample_size=200,
                last_values_number=5000,
            )
            return json.loads(bz2.decompress(b64decode(api_response.to_dict())))
        except MonitoringHub.ApiException as e:
            if e.status == 404:
                logging.info("Datapoint %s:%s not found", task, entity)
            else:
                logging.error(
                    "Exception when calling DefaultApi->api_hub_get_data: %s", e
                )
            return None
        except IOError:
            logging.error("Timeout for entity %s:%s", task, entity)
            return None
        except urllib3.exceptions.MaxRetryError:
            logging.error(
                "Max retry error: %s, %s, %s, %s", source, partition, task, entity
            )
            return None
    return None


def monitoringhub_counter_loader(
    hid, start_time, end_time, hub_configuration, wincc_server, source="wincc"
):
    """get counter from the monitoring hub"""
    with MonitoringHub.ApiClient(hub_configuration) as api_client:
        api_instance = default_api.DefaultApi(api_client)
        partition = "LHCb"
        server = wincc_server
        task = hid["taskname"][13:]
        entity = hid["name"]
        s_time = datetime.fromtimestamp(start_time)
        e_time = datetime.fromtimestamp(end_time)

        try:
            api_response = api_instance.api_hub_get_data(
                source,
                partition,
                task,
                entity,
                server=server,
                _request_timeout=30,
                time_start=s_time,
                time_end=e_time,
                last_values_number=1,
            )
            return json.loads(bz2.decompress(b64decode(api_response.to_dict())))
        except MonitoringHub.ApiException as e:
            if e.status == 404:
                logging.info("Datapoint %s:%s not found", task, entity)
                return None
            else:
                logging.error(
                    "Exception when calling DefaultApi->api_hub_get_data: %s", e
                )
            return None
        except IOError:
            logging.error("Timeout for entity %s:%s", task, entity)
            return None
        except urllib3.exceptions.MaxRetryError:
            logging.error(
                "Max retry error: %s, %s, %s, %s", source, partition, task, entity
            )
            return None
    return None


@cache.memoize(timeout=120)
def monitoringhub_get_online_partitions(hub_configuration, dns):
    """get list of online partitions from monitoring hub"""
    with MonitoringHub.ApiClient(hub_configuration) as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        source = "dim"  # str | source to get the partitions for
        dim_dns_node = dns  # str | dim_dns_node for dim source (optional)

        try:
            api_response = api_instance.api_hub_get_partitions(
                source, dim_dns_node=dim_dns_node
            )
            return sorted(list(api_response))
        except MonitoringHub.ApiException as e:
            logging.error(
                "Exception when calling DefaultApi->api_hub_get_partitions: %s", e
            )
            return list([])
        except urllib3.exceptions.MaxRetryError:
            logging.error("Max retry in get online partitions")
            return list([])
    return list([])


@cache.memoize(timeout=3600)
def monitoringhub_get_saveset_partitions(hub_configuration, the_path):
    """get list of saveset partitions"""
    with MonitoringHub.ApiClient(hub_configuration) as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        source = "savesets"  # str | source to get the partitions for

        try:
            api_response = api_instance.api_hub_get_partitions(source, path=the_path)
            return sorted(list(api_response))
        except MonitoringHub.ApiException as e:
            logging.error(
                "Exception when calling DefaultApi->api_hub_get_partitions: %s", e
            )
            return list([])
        except IOError:
            logging.error("Error when searching for saveset partition, set it to LHCb")
            return list(["LHCb"])
        except urllib3.exceptions.MaxRetryError:
            logging.error("Max retry error: %s, %s, %s, %s", source)
            return list(["LHCb"])
    return list([])


@cache.memoize(timeout=20)
def monitoringhub_get_histogram_object(
    hub_configuration,
    dns,
    in_onlinehist,
    partition="LHCb",
    json_file="",
    json_files_path="/hist/Monet/ROOT/",
    run="",
    fill="",
    mu=-1.,
):
    """get histogram from monitoring hub"""
    if partition == "":
        logging.debug("No partition set")
        return None
    onlinehist = copy.deepcopy(in_onlinehist)
    # Enter a context with an instance of the API client
    with MonitoringHub.ApiClient(hub_configuration) as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        source = "dim"  # str | source to get the data for
        task = onlinehist["taskname"]  # str | task to get the data for
        entity = onlinehist["name"]  # str | task to get the data for
        dim_dns_node = dns  # str | dim_dns_node in case of dim source (optional)
        analysis_type = ""
        analysis_inputs = []
        analysis_parameters = []
        analysis_parameters.append(f"mu:{mu}")
        hist_titles = []
        hist_index = -1
        if run == "":
            run = -1
        if fill == "":
            fill = -1
        ## Automatic analyses: operations
        if onlinehist.get("operation", None):
            analysis_type = f"operation/{onlinehist['operation'].get('type', '')}"
            if analysis_type == "":
                logging.error("Error: no analysis type defined")
                return None, ""
            analysis_inputs = [
                f"{n['taskname']}///{n['name']}"
                for n in onlinehist["operation"].get("inputs", [])
            ]
            hist_titles = onlinehist["operation"].get("hist_titles", [])
            hist_index = onlinehist["operation"].get("hist_index", -1)
            if not analysis_inputs:
                logging.error("Error: no input histogram defined")
                return None, ""
            # remove type and inputs and send the rest as parameters
            onlinehist.get("operation").pop("type")
            onlinehist.get("operation").pop("inputs")
            o_map = onlinehist.get("operation")
            for k in o_map.keys():
                if isinstance(o_map[k], list):
                    for m in o_map[k]:
                        analysis_parameters.append(f"{k}:{m}")
                else:
                    analysis_parameters.append(f"{k}:{o_map[k]}")
        ## Automatic analyses: analyses
        elif onlinehist.get("analysis", None):
            analysis_type = f"analyze/{onlinehist['analysis'].get('type', '')}"
            if analysis_type == "":
                logging.error("Error: no analysis type defined")
                return None, ""
            analysis_inputs = [
                f"{n['taskname']}///{n['name']}"
                for n in onlinehist["analysis"].get("inputs", [])
            ]
            if not analysis_inputs:
                logging.error("Error: no input histogram defined")
                return None, ""
            # remove type and inputs and send the rest as parameters
            onlinehist.get("analysis").pop("type")
            onlinehist.get("analysis").pop("inputs")
            o_map = onlinehist.get("analysis")
            for k in o_map.keys():
                analysis_parameters.append(f"{k}:{o_map[k]}")


        try:
            if len(analysis_inputs)<100:
                api_response = api_instance.api_hub_get_data(
                    source,
                    partition,
                    task,
                    entity,
                    run=run,
                    fill=fill,
                    dim_dns_node=dim_dns_node,
                    analysis_type=analysis_type,
                    analysis_inputs=analysis_inputs,
                    analysis_parameters=analysis_parameters,
                    hist_titles=hist_titles,
                    hist_index=hist_index,
                    _request_timeout=30,
                )
            else:
                api_response = api_instance.api_hub_get_large_data(
                    source, 
                    partition, 
                    task,
                    entity,
                    analysis_type, 
                    {'analysis_inputs':analysis_inputs}, 
                    run=run, 
                    fill=fill, 
                    dim_dns_node=dim_dns_node,
                    analysis_parameters=analysis_parameters, 
                    hist_titles=hist_titles, 
                    hist_index=hist_index,
                    _request_timeout=60,
                )

            file_to_write = rand_str(n=2) + ".json"
            filename = json_files_path + file_to_write
            if analysis_type == "":
                try:
                    with open(filename, "w", encoding="UTF-8") as outfile:
                        outfile.write(api_response.to_dict())
                except PermissionError:
                    file_to_write = "_"
                obj = (
                    ROOT.TBufferJSON.ConvertFromJSON(api_response.to_dict()),
                    file_to_write,
                )
                with ROOT.TFile( filename.replace('.json','.root'), 'RECREATE' ) as root_file:
                    root_file.WriteObject(obj[0], "MonetHisto")
            else:
                try:
                    with open(filename, "w", encoding="UTF-8") as outfile:
                        outfile.write(api_response.to_dict()["histo"])
                except PermissionError:
                    file_to_write = "_"
                try:
                    obj = (
                        ROOT.TBufferJSON.ConvertFromJSON(
                            api_response.to_dict()["histo"]
                        ),
                        api_response.to_dict()["results"],
                        file_to_write,
                    )
                except Exception:
                    return None, ""
            if not obj:
                logging.error("Error in converting ROOT JSON to ROOT object")
            return obj, "DIM"
        except MonitoringHub.ApiException as e:
            if e.status == 404:
                logging.info("Histogram %s not found for task %s", entity, task)
            else:
                logging.error(
                    "Exception when calling DefaultApi->api_hub_get_data: %s", e
                )
            return None, ""
        except urllib3.exceptions.MaxRetryError:
            logging.error(
                "Max retry error: %s, %s, %s, %s", source, partition, task, entity
            )
            return None, ""
    return None, ""

@cache.memoize(timeout=600)
def find_reference_file(identifier, onlinehist, rundb_info, path="/hist", json_file=""):
    """find reference file"""
    task, key = identifier.split("/", 1)
    json_files_path = current_app.config.get("JSON_FILES_PATH", "/hist/Monet/ROOT/")

    with MonitoringHub.ApiClient(
        current_app.config.get("MONHUB_CONFIG", None)
    ) as api_client:
        api_instance = default_api.DefaultApi(api_client)
        source = "savesets"
        partition = "LHCb"
        entity = key
        mu = -1
        if rundb_info:
            runnumber = rundb_info.get("runid", 1)
            if rundb_info.get("endtime", "") == rundb_info.get("starttime", ""):
                runnumber = 1
        else:
            runnumber = 1

        ## Add informations to find the correct reference file
        extrapath = ""
        if rundb_info:
            # TCK
            if "tck" in rundb_info:
                if rundb_info["tck"] != "":
                    if extrapath != "":
                        extrapath = extrapath + "_TCK=0x{:08X}".format(
                            int(rundb_info["tck"])
                        )
                    else:
                        extrapath = "TCK=0x{:08X}".format(int(rundb_info["tck"]))
            # Magnet
            if "magnetState" in rundb_info:
                if extrapath != "":
                    extrapath = (
                        extrapath + "_Mag=" + rundb_info["magnetState"].capitalize()
                    )
                else:
                    extrapath = "Mag=" + rundb_info["magnetState"].capitalize()
            # Activity
            if "runtype" in rundb_info:
                if extrapath != "":
                    extrapath = extrapath + "_ACTIVITY=" + rundb_info["runtype"].upper()
                else:
                    extrapath = "ACTIVITY=" + rundb_info["runtype"].upper()
        else:
            extrapath = ""
        analysis_type = ""

        analysis_inputs = []
        analysis_parameters = []
        analysis_parameters.append(f"mu:{mu}")

        if onlinehist.get("operation", None):
            analysis_type = f"operation/{onlinehist['operation'].get('type', '')}"
            if analysis_type == "":
                logging.error("Error: no analysis type defined")
                return None
            analysis_inputs = [
                f"{n['taskname']}///{n['name']}"
                for n in onlinehist["operation"].get("inputs", [])
            ]
            if not analysis_inputs:
                logging.error("Error: no input histogram defined")
                return None
            # remove type and inputs and send the rest as parameters
            onlinehist.get("operation").pop("type")
            onlinehist.get("operation").pop("inputs")
            o_map = onlinehist.get("operation")
            for k in o_map.keys():
                if isinstance(o_map[k], list):
                    for m in o_map[k]:
                        analysis_parameters.append(f"{k}:{m}")
                else:
                    analysis_parameters.append(f"{k}:{o_map[k]}")
        elif onlinehist.get("analysis", None):
            analysis_type = f"analyze/{onlinehist['analysis'].get('type', '')}"
            if analysis_type == "":
                logging.error("Error: no analysis type defined")
                return None
            analysis_inputs = [
                f"{n['taskname']}///{n['name']}"
                for n in onlinehist["analysis"].get("inputs", [])
            ]
            if not analysis_inputs:
                logging.error("Error: no input histogram defined")
                return None
            # remove type and inputs and send the rest as parameters
            onlinehist.get("analysis").pop("type")
            onlinehist.get("analysis").pop("inputs")
            o_map = onlinehist.get("analysis")
            for k in o_map.keys():
                analysis_parameters.append(f"{k}:{o_map[k]}")

        try:
            api_response = api_instance.api_hub_get_reference(
                source,
                partition,
                task,
                runnumber,
                entity,
                path,
                analysis_type=analysis_type,
                analysis_inputs=analysis_inputs,
                analysis_parameters=analysis_parameters,
                extrapath=extrapath,
                _request_timeout=30,
            )
            res = api_response.to_dict()
            if res["hub_type"] == "ROOT_JSON":
                if analysis_type == "":
                    j_res = bz2.decompress(b64decode(res["hub_data"]))
                    obj = ROOT.TBufferJSON.ConvertFromJSON(j_res)
                else:
                    j_res = bz2.decompress(b64decode(res["hub_data"]["histo"]))
                    obj = (
                        ROOT.TBufferJSON.ConvertFromJSON(j_res),
                        res["hub_data"]["results"],
                    )

                if json_file:
                    json_file_decoded = None
                    json_file_decoded_1 = None
                    json_file_template = None
                    xmin = 0
                    xmax = 0
                    ymin = 0
                    ymax = 0
                    with open(json_files_path + json_file, "r", encoding="utf-8") as f:
                        try:
                            json_file_decoded = json.load(f)
                        except json.decoder.JSONDecodeError:
                            logging.error("Error decoding JSON file")
                        try:
                            xmin = json_file_decoded["fXaxis"]["fXmin"]
                            xmax = json_file_decoded["fXaxis"]["fXmax"]
                            ymin = json_file_decoded["fYaxis"]["fXmin"]
                            xmax = json_file_decoded["fYaxis"]["fXmax"]
                        except KeyError:
                            logging.info("Key error for reference file %s", identifier)
                        except TypeError:
                            logging.error("None type for json file %s", identifier)
                    with open("template.json", "r", encoding="utf-8") as f:
                        json_file_template = json.load(f)
                        json_file_template["fUxmin"] = xmin
                        json_file_template["fUxmax"] = xmax
                        json_file_template["fUymin"] = ymin
                        json_file_template["fUymax"] = ymax
                    json_file_decoded_1 = json.loads(j_res.decode("utf-8"))
                    try:
                        json_file_template["fPrimitives"]["arr"] = [
                            json_file_decoded,
                            json_file_decoded_1,
                        ]
                        with open(
                            json_files_path + json_file, "w", encoding="utf-8"
                        ) as f:
                            f.write(json.dumps(json_file_template))
                    except PermissionError:
                        pass
            if not obj:
                logging.error("Error in converting ROOT JSON to ROOT object")
                return None, "Not found"
            return obj, res.get("hub_path",None)
        except IOError:
            logging.error(
                "IO error in reference file: %s, %s, %s", source, partition, task
            )
            return None, "Not found"
        except MonitoringHub.exceptions.NotFoundException:
            logging.info(
                "Not found in reference file: %s, %s, %s", source, partition, task
            )
            return None, "Not found"
        except urllib3.exceptions.MaxRetryError:
            logging.error(
                "Max retry error in reference file: %s, %s, %s",
                source,
                partition,
                task,
            )
        except MonitoringHub.exceptions.ServiceException:
            logging.error(
                "Service exception error in reference file: %s, %s, %s",
                source,
                partition,
                task,
            )
    return None, "Not found"

def monitoringhub_get_histogram_in_savesets(in_db_hist, **kwargs):
    db_hist = copy.deepcopy(in_db_hist)

    with MonitoringHub.ApiClient(
        current_app.config.get("MONHUB_CONFIG", None)
    ) as api_client:
        api_instance = default_api.DefaultApi(api_client)
        source = "savesets"
        partition = kwargs['partition']
        path = current_app.config.get("PATH_HISTOS", "/hist")
        timeout = 30
        if kwargs['history_type'] == "Run":
            run = kwargs['run_number']
            fill = -1
            runlist = []
        else:
            run = -1
            fill = kwargs['run_number']
            runlist = kwargs['run_list']
            timeout = 60
        analysis_type = ""
        analysis_inputs = []
        analysis_parameters = []
        hist_titles = []
        hist_index = -1
        analysis_parameters.append(f"mu:{kwargs.get('mu',-1.)}")
        if db_hist.get("operation", None):
            analysis_type = f"operation/{db_hist['operation'].get('type', '')}"
            if analysis_type == "":
                logging.error("Error: no analysis type defined")
                return None, ""
            try:
                analysis_inputs = [
                    f"{n['taskname']}///{n['name']}"
                    for n in db_hist["operation"].get("inputs", [])
                ]
            except KeyError:
                logging.error("no taskname for analysis input")
                return None, ""
            if not analysis_inputs:
                logging.error("Error: no input histogram defined")
                return None, ""
            # remove type and inputs and send the rest as parameters
            db_hist.get("operation").pop("type")
            db_hist.get("operation").pop("inputs")
            hist_titles = db_hist["operation"].get("hist_titles", [])
            hist_index = db_hist["operation"].get("hist_index", -1)
            o_map = db_hist.get("operation")
            for k in o_map.keys():
                if isinstance(o_map[k], list):
                    for m in o_map[k]:
                        analysis_parameters.append(f"{k}:{m}")
                else:
                    analysis_parameters.append(f"{k}:{o_map[k]}")
        elif db_hist.get("analysis", None):
            analysis_type = f"analyze/{db_hist['analysis'].get('type', '')}"
            if analysis_type == "":
                print("Error: no analysis type defined")
                return None, ""
            analysis_inputs = [
                f"{n['taskname']}///{n['name']}"
                for n in db_hist["analysis"].get("inputs", [])
            ]
            if not analysis_inputs:
                print("Error: no input histogram defined")
                return None, ""
            # remove type and inputs and send the rest as parameters
            db_hist.get("analysis").pop("type")
            db_hist.get("analysis").pop("inputs")
            o_map = db_hist.get("analysis")
            for k in o_map.keys():
                analysis_parameters.append(f"{k}:{o_map[k]}")
        try:
            if (kwargs['run_starttime'] is None) or (kwargs['run_endtime'] is None):
                return None, ""
            if len(analysis_inputs)<100:
                api_response = api_instance.api_hub_get_data(
                    source,
                    partition,
                    kwargs['task'],
                    kwargs['key'],
                    path=path,
                    run=run,
                    fill=fill,
                    runlist=runlist,
                    time_start=kwargs['run_starttime'],
                    time_end=kwargs['run_endtime'],
                    analysis_type=analysis_type,
                    analysis_inputs=analysis_inputs,
                    analysis_parameters=analysis_parameters,
                    hist_titles=hist_titles,
                    hist_index=hist_index,
                    _request_timeout=timeout,
                )
            else:
                api_response = api_instance.api_hub_get_large_data(
                    source, 
                    partition, 
                    kwargs['task'],
                    kwargs['key'],
                    analysis_type, 
                    {'analysis_inputs':analysis_inputs}, 
                    path=path, 
                    run=run, 
                    fill=fill, 
                    runlist=runlist, 
                    time_start=kwargs['run_starttime'],
                    time_end=kwargs['run_endtime'],
                    analysis_parameters=analysis_parameters, 
                    hist_titles=hist_titles, 
                    hist_index=hist_index,
                    _request_timeout=60,
                )

            res = api_response.to_dict()
            file_to_write = rand_str(n=2) + ".json"
            filename = (
                current_app.config.get("JSON_FILES_PATH", "/hist/Monet/ROOT/")
                + file_to_write
            )

            if res["hub_type"] == "ROOT_JSON":
                if analysis_type == "":
                    try:
                        with open(filename, "wb") as outfile:
                            outfile.write(
                                bz2.decompress(b64decode(res["hub_data"]))
                            )
                    except PermissionError:
                        file_to_write = "_"
                    obj = (
                        ROOT.TBufferJSON.ConvertFromJSON(
                            bz2.decompress(b64decode(res["hub_data"]))
                        ),
                        file_to_write,
                    )
                    with ROOT.TFile( filename.replace('.json','.root'), 'RECREATE' ) as root_file:
                        root_file.WriteObject(obj[0], "MonetHisto")
                else:
                    try:
                        with open(filename, "wb") as outfile:
                            outfile.write(
                                bz2.decompress(b64decode(res["hub_data"]["histo"]))
                            )
                    except PermissionError:
                        file_to_write = "_"
                    obj = (
                        ROOT.TBufferJSON.ConvertFromJSON(
                            bz2.decompress(b64decode(res["hub_data"]["histo"]))
                        ),
                        res["hub_data"]["results"],
                        file_to_write,
                    )
            if not obj:
                print("Error in converting ROOT JSON to ROOT object")
            return obj, res.get("hub_path","")
        except MonitoringHub.ApiException as e:
            if e.status == 404:
                logging.info("Histogram %s not found for run %s", kwargs['key'], run)
                if kwargs['fallback_key']:
                    print(f"Try fallback {kwargs['fallback_key']}")
                    try:
                        api_response = api_instance.api_hub_get_data(
                            source,
                            partition,
                            kwargs['task'],
                            kwargs['fallback_key'],
                            path=path,
                            run=run,
                            fill=fill,
                            runlist=runlist,
                            time_start=kwargs['run_starttime'],
                            time_end=kwargs['run_endtime'],
                            _request_timeout=timeout,
                        )
                        res = api_response.to_dict()
                        if res["hub_type"] == "ROOT_JSON":
                            obj = ROOT.TBufferJSON.ConvertFromJSON(
                                bz2.decompress(b64decode(res["hub_data"]))
                            )
                        if not obj:
                            print("Error in converting ROOT JSON to ROOT object")
                        return obj, res.get("hub_path","")
                    except MonitoringHub.exceptions.NotFoundException:
                        logging.error("File not found")
                        return None, ""
                    except RuntimeError:
                        return None, ""
                return None, ""
            else:
                print("Exception when calling DefaultApi->api_hub_get_data: %s", e)
            return None, ""
        except RuntimeError:
            print(f"Timeout for histogram {kwargs['key']}")
            return None, ""
        except urllib3.exceptions.MaxRetryError:
            logging.error(
                "Max retry error: %s, %s, %s, %s", source, partition, kwargs['task'], kwargs['key']
            )
            return None, ""
        except MonitoringHub.exceptions.NotFoundException:
            logging.error("File not found")
            return None, ""
    return None, ""


def monitoringhub_create_saveset(the_config, partition, task, path, run, fill, runlist, time_start, time_end, request_timeout):
    try:
        with MonitoringHub.ApiClient(the_config) as api_client:
            api_instance = default_api.DefaultApi(api_client)
            api_instance.api_hub_create_saveset(
                partition,
                task,
                path=path,
                run=run,
                fill=fill,
                runlist=runlist,
                time_start=time_start,
                time_end=time_end,
                _request_timeout=request_timeout,
            )
    except Exception:
        pass

def thread_function(
    the_config,
    partition,
    task,
    path,
    run,
    fill,
    runlist,
    time_start,
    time_end,
    request_timeout,
):
    monitoringhub_create_saveset(the_config, partition, task, path, run, fill, runlist, time_start, time_end, request_timeout)

def monitoringhub_prepare_file(partition, task, history_type, run_number, interval_begin, interval_size, number_of_tasks ):
    with MonitoringHub.ApiClient(
        current_app.config.get("MONHUB_CONFIG", None)
    ) as api_client:
        api_instance = default_api.DefaultApi(api_client)
        path = current_app.config.get("PATH_HISTOS", "/hist")
        if history_type == "Run":
            try:
                run = int(run_number)
            except ValueError:
                abort(404, description="Bad run number")
            rdb_info = interfaces.rundb.get_rundb_info(run)
            time_start = rdb_info.get("starttime", None)
            time_end = rdb_info.get("endtime", None)
            if time_start is None or time_end is None:
                abort(404, description="Run DB data is incomplete for this run")
            fill = -1
            runlist = []
        elif history_type == "Fill":
            partition = "LHCb"
            run = -1
            fill = int(run_number)
            rdb_info = interfaces.rundb.get_rundb_info_fill(fill)

            try:
                time_start = rdb_info["start_date"]
            except KeyError:
                time_start = "2000-01-01T01:00:00"
            try:
                time_end = rdb_info["timestamp"]
            except KeyError:
                time_end = "2000-01-01T01:00:00"
            runlist = rdb_info["runs"]
        elif history_type == "Interval":
            run = -1
            fill = -1
            time_start = datetime.strptime(
                interval_begin, "%m/%d/%Y %H:%M"
            )
            diff = datetime.strptime(
                interval_size, "%H:%M"
            ) - datetime(1900, 1, 1)
            time_end = time_start + diff
            time_start = time_start.strftime("%Y-%m-%dT%H:%M:%S")
            time_end = time_end.strftime("%Y-%m-%dT%H:%M:%S")
            runlist = []
        else:
            abort(404, description="History type not known")
        try:
            api_instance.api_hub_prepare_file(
                partition,
                task,
                path=path,
                run=run,
                fill=fill,
                runlist=runlist,
                time_start=time_start,
                time_end=time_end,
                _request_timeout=5,
            )
        except MonitoringHub.ApiException as e:
            if e.status == 404:
                if number_of_tasks == 1:
                    abort(404, description="Savesets do not exist for that run")
                else:
                    return task
            elif e.status == 400:
                t = Thread(
                    target=thread_function,
                    args=(
                        current_app.config.get("MONHUB_CONFIG", None),
                        partition,
                        task,
                    ),
                    kwargs={
                        "path": path,
                        "run": run,
                        "fill": fill,
                        "runlist": runlist,
                        "time_start": time_start,
                        "time_end": time_end,
                        "request_timeout": 60,
                    },
                )
                t.start()
                abort(
                    404,
                    "Saveset files are being created for this run, try again in 2 minutes",
                )
            elif e.status == 412:
                abort(
                    404, "Saveset file merging not finished, try again in 2 minutes"
                )
            else:
                logging.error(
                    "Exception when calling DefaultApi->api_hub_prepare_file: %s\n"
                    % e
                )
        except Exception:
            abort(404, "Timeout")
    return None

