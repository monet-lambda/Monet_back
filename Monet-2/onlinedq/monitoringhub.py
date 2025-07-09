"""Interface functions to the monitoring hub"""
import datetime
import logging
import random
import string
import json
import bz2
import urllib3
from base64 import b64decode
import MonitoringHub
from MonitoringHub.api import default_api
import ROOT
from flask_caching import Cache

cache = Cache()


def rand_str(chars = string.ascii_lowercase, n=10):
    """Create random file name"""
    return ''.join(random.choice(chars) for _ in range(n))

def monitoringhub_trend_loader(hid, start_time, end_time, hub_configuration, wincc_server,
                               source="wincc"):
    """load trend plots via monitoring hub"""
    with MonitoringHub.ApiClient(hub_configuration) as api_client:

        api_instance = default_api.DefaultApi(api_client)
        partition = "LHCb"
        server=wincc_server
        task=hid['taskname'][6:]
        entity=hid['name']
        s_time = datetime.datetime.fromtimestamp(start_time)
        e_time = datetime.datetime.fromtimestamp(end_time)

        try:
            api_response = api_instance.api_hub_get_data(source, partition, task, entity,
                                server=server, _request_timeout = 60, async_req = True,
                                time_start = s_time, time_end = e_time, sample_size= 200,
                                last_values_number = 5000)
            return json.loads(bz2.decompress(b64decode(api_response.get())))
        except MonitoringHub.ApiException as e:
            if e.status == 404:
                logging.info("Datapoint %s:%s not found", task, entity)
            else:
                logging.error("Exception when calling DefaultApi->api_hub_get_data: %s", e)
            return None
        except IOError:
            logging.error("Timeout for entity %s:%s", task, entity)
            return None
        except urllib3.exceptions.MaxRetryError:
            logging.error("Max retry error: %s, %s, %s, %s", source, partition, task, entity)
            return None
    return None

def monitoringhub_counter_loader(hid, start_time, end_time, hub_configuration, wincc_server,
                                 source="wincc"):
    """get counter from the monitoring hub"""
    with MonitoringHub.ApiClient(hub_configuration) as api_client:
        api_instance = default_api.DefaultApi(api_client)
        partition = "LHCb"
        server=wincc_server
        task=hid['taskname'][13:]
        entity=hid['name']
        s_time = datetime.datetime.fromtimestamp(start_time)
        e_time = datetime.datetime.fromtimestamp(end_time)

        try:
            api_response = api_instance.api_hub_get_data(source, partition, task, entity,
                                server=server, _request_timeout = 60, async_req = True,
                                time_start = s_time, time_end = e_time,
                                last_values_number = 1)
            return json.loads(bz2.decompress(b64decode(api_response.get())))
        except MonitoringHub.ApiException as e:
            if e.status == 404:
                logging.info("Datapoint %s:%s not found", task, entity)
                return None
            else:
                logging.error("Exception when calling DefaultApi->api_hub_get_data: %s", e)
            return None
        except IOError:
            logging.error("Timeout for entity %s:%s", task, entity)
            return None
        except urllib3.exceptions.MaxRetryError:
            logging.error("Max retry error: %s, %s, %s, %s", source, partition, task, entity)
            return None         
    return None

@cache.memoize(timeout=120)
def monitoringhub_get_online_partitions(hub_configuration, dns):
    """get list of online partitions from monitoring hub"""
    with MonitoringHub.ApiClient(hub_configuration) as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        source = "dim" # str | source to get the partitions for
        dim_dns_node = dns # str | dim_dns_node for dim source (optional)

        try:
            api_response = api_instance.api_hub_get_partitions(source, dim_dns_node=dim_dns_node)
            return sorted(list(api_response))
        except MonitoringHub.ApiException as e:
            logging.error("Exception when calling DefaultApi->api_hub_get_partitions: %s", e)
            return list([])
    return list([])

@cache.memoize(timeout=3600)
def monitoringhub_get_saveset_partitions(hub_configuration, the_path):
    """get list of saveset partitions"""
    with MonitoringHub.ApiClient(hub_configuration) as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        source = "savesets" # str | source to get the partitions for

        try:
            api_response = api_instance.api_hub_get_partitions(source, path=the_path)
            return sorted(list(api_response))
        except MonitoringHub.ApiException as e:
            logging.error("Exception when calling DefaultApi->api_hub_get_partitions: %s", e)
            return list([])
        except IOError:
            logging.error("Error when searching for saveset partition, set it to LHCb")
            return list(["LHCb"])
        except urllib3.exceptions.MaxRetryError:
            logging.error("Max retry error: %s, %s, %s, %s", source)
            return list(["LHCb"])
    return list([])

@cache.memoize(timeout=20)
def monitoringhub_get_histogram_object(hub_configuration, dns, onlinehist, partition="LHCb", json_file='', 
                                       json_files_path='/hist/Monet/ROOT/' ):
    """get histogram from monitoring hub"""
    # Enter a context with an instance of the API client
    with MonitoringHub.ApiClient(hub_configuration) as api_client:
        # Create an instance of the API class
        api_instance = default_api.DefaultApi(api_client)
        source = "dim" # str | source to get the data for
        task = onlinehist["taskname"] # str | task to get the data for
        entity = onlinehist["name"] # str | task to get the data for
        dim_dns_node = dns # str | dim_dns_node in case of dim source (optional)
        analysis_type = ''
        analysis_inputs = []
        analysis_parameters = []
        ## Automatic analyses: operations
        if onlinehist.get("operation",None):
            analysis_type = f'operation/{onlinehist["operation"].get("type","")}'
            if analysis_type == '':
                logging.error("Error: no analysis type defined")
                return None
            analysis_inputs = [ f'{n["taskname"]}///{n["name"]}'
                               for n in onlinehist["operation"].get("inputs",[]) ]
            if not analysis_inputs:
                logging.error("Error: no input histogram defined")
                return None
            # remove type and inputs and send the rest as parameters
            onlinehist.get("operation").pop("type")
            onlinehist.get("operation").pop("inputs")
            o_map = onlinehist.get("operation")
            for k in o_map.keys():
                if isinstance( o_map[k] , list ):
                    for l in o_map[k]:
                        analysis_parameters.append( f"{k}:{l}" )
                else:
                    analysis_parameters.append( f"{k}:{o_map[k]}" )
        ## Automatic analyses: analyses
        elif onlinehist.get("analysis",None):
            analysis_type = f'analyze/{ onlinehist["analysis"].get("type","")}'
            if analysis_type == '':
                logging.error("Error: no analysis type defined")
                return None
            analysis_inputs = [ f'{n["taskname"]}///{n["name"]}'
                               for n in onlinehist["analysis"].get("inputs",[]) ]
            if not analysis_inputs:
                logging.error("Error: no input histogram defined")
                return None
            # remove type and inputs and send the rest as parameters
            onlinehist.get("analysis").pop("type")
            onlinehist.get("analysis").pop("inputs")
            o_map = onlinehist.get("analysis")
            for k in o_map.keys():
                analysis_parameters.append( f"{k}:{o_map[k]}" )
        try:
            api_response = api_instance.api_hub_get_data(source, partition, task, entity,
                                                         dim_dns_node=dim_dns_node,
                                                         analysis_type = analysis_type,
                                                         analysis_inputs=analysis_inputs,
                                                         analysis_parameters = analysis_parameters,
                                                        _request_timeout = 60  )
            file_to_write = rand_str( n=2 ) + ".json"
            filename = json_files_path+file_to_write
            if analysis_type == '':
                try:
                    with open( filename , "w" , encoding='UTF-8' ) as outfile:
                        outfile.write( api_response )
                except PermissionError:
                    file_to_write = "_"
                obj = ROOT.TBufferJSON.ConvertFromJSON(api_response), file_to_write
            else:
                try:
                    with open( filename , "w" , encoding='UTF-8' ) as outfile:
                        outfile.write( api_response["histo"] )
                except PermissionError:
                    file_to_write = "_"
                obj = ROOT.TBufferJSON.ConvertFromJSON(api_response["histo"]),\
                    api_response["results"], file_to_write
            if not obj:
                logging.error("Error in converting ROOT JSON to ROOT object")
            return obj
        except MonitoringHub.ApiException as e:
            if e.status == 404:
                logging.info("Histogram %s not found for task %s", entity, task)
            else:
                logging.error("Exception when calling DefaultApi->api_hub_get_data: %s" , e)
            return None
        except urllib3.exceptions.MaxRetryError:
            logging.error("Max retry error: %s, %s, %s, %s", source, partition, task, entity)
            return None
    return None
