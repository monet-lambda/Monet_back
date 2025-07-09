.. MonitoringHub user guide

MonitoringHub user guide
=============================

The MonitoringHub is a server used to collect all data available for the monitoring. It is usually called from :ref:`Monet<Monet user guide>`, 
but can also be called directly. The address of the server is http://monitoringhub.lbdaq.cern.ch/v1, accesible only from the online network. 
The API of calls to the MonitoringHub is available at http://monitoringhub.lbdaq.cern.ch/v1/api, also only from the online network. It can 
also be seen `in gitlab <https://gitlab.cern.ch/lhcb-monitoring/MonitoringHub/-/blob/master/openapi/hub_api.yaml?ref_type=heads>`_ in 
`OpenAPI <https://swagger.io/specification/>`_ syntax.

A python package is available from https://gitlab.cern.ch/lhcb-monitoring/MonitoringHubClient to communicate directly to the MonitoringHub server 
and get monitoring data from it. The gitlab page gives detailed documentation of the package. A summary of it is given below.

Installation
------------

On an online machine (possibly in a virtual environment)

::

    python -m venv .venv
    export https_proxy=http://lbproxy01:8080
    source .venv/bin/activate
    pip install git+https://gitlab.cern.ch/lhcb-monitoring/MonitoringHubClient.git


Usage
-----
After setting up the environment, 

::

    source .venv/bin/activate

In a Python script, for example:

.. code-block:: python

    import MonitoringHub
    from MonitoringHub.api import default_api
    import json
    import bz2
    from base64 import b64decode

    configuration = MonitoringHub.Configuration( host = "http://monitoringhub.lbdaq.cern.ch/v1" )

    with MonitoringHub.ApiClient( configuration ) as api_client:
        api_instance = default_api.DefaultApi(api_client)
        source = "source_example"
        partition = "partition_example"
        task = "task_example"
        entity = "entity_example"

        try:
            api_response = api_instance.api_hub_get_data(source, partition, task, entity)
            data = json.loads(bz2.decompress(b64decode(api_response.to_dict())))
        except MonitoringHub.ApiException as e:
            print("Error when calling the MonitoringHub server")

The main function ``api_hub_get_data()`` is described in details below:

.. py:function:: api_hub_get_data( source , partition, task, entity, dim_dns_node, server, path, run, run_max, fill, fill_max, runlist, time_start, time_end, sample_size, last_values_number, analysis_type, analysis_inputs, analysis_parameters, hist_titles, hist_index)

   Return data from the MonitoringHub.

   :param source: Source of the data:

    * ``dim`` - online data from DIM at the pit
    * ``savesets`` - history data from savesets (ROOT files containing monitoring histograms)
    * ``alarms`` - not yet implemented
    * ``wincc`` - data from the WinCC archive database, for trend plots
    * ``simulation`` - data from the simulation monitoring histograms on the grid
    * ``trends`` - data from trends (quantities as functions of run numbers of fill numbers) extracted from the DQDB

   :type source: str
   :param partition: Set to the online partition in case of ``dim`` source, otherwise set to ``LHCb``
   :type partition: str
   :param task: Name of the task (see below)
   :type task: str
   :param entity: Name of the entity (see below)
   :type entity: str
   :param dim_dns_node: Mandatory for ``dim`` source: name of the DIM DNS node (usually ``mon01``)
   :type dim_dns_node: str, optional   
   :param server: Name of the server to use for WinCC archve trend plots for the ``wincc`` source (obsolete)
   :type server: str, optional
   :param path: Path for savesets, for the ``savesets`` source
   :type path: str, optional
   :param run: Run number to get data from, for the ``savesets`` source; minimum of the run range for the ``trends`` source
   :type run: int, optional
   :param run_max: Maximum of the run range for the ``trends`` source
   :type run_max: int, optional
   :param fill: Fill number to get data from, for the ``savesets`` source; minimum of the fill range for the ``trends`` source``
   :type fill: int, optional 
   :param fill_max: Maximum of the fill range for the ``trends`` source
   :type fill_max: int, optional
   :param runlist: List of runs to get the data from, for the ``savesets`` source
   :type runlist: [int], optional 
   :param time_start: Beginning of the time range for the ``savesets`` source
   :type time_start: datetime, optional 
   :param time_end: End of the time range for the ``savesets`` source
   :type time_end: datetime, optional 
   :param sample_size: Number of values from the WinCC archive database, for the ``wincc`` source (obsolete)
   :type sample_size: int, optional 
   :param last_values_number: Obsolete
   :type last_values_number: int, optional 
   :param analysis_type: Name of the automatic analysis to be done on the list of histograms in the analysis_parameters parameter
   :type analysis_type: str, optional 
   :param analysis_inputs: List of names of hitograms to use for the automatic analysis
   :type analysis_inputs: [str], optional  
   :param analysis_parameters: List of parameters to use in the automatic analysis
   :type analysis_parameters: [str], optional 
   :param hist_titles: List of histogram titles to be sent to the automatic analysis
   :type hist_titles: [str], optional
   :param hist_index: Index of the histogram to send as a result in case the automatic analysis produces several of them
   :type hist_index: int, optional
   :return: 

    * An histogram containing the requested data, in JSON ROOT format
    * A list of pairs (timestamp, value) for the `wincc` data source

   :rtype: A compressed JSON object

The data to request is defined by the ``task`` and ``entity`` parameters of the function. Their meaning depends on the ``source`` and 
is explained in the table below: 

.. list-table:: Definition of ``task`` and ``entity`` for various sources
   :widths: 25 30 30
   :header-rows: 1

   * - Source
     - Task
     - Entity
   * - dim
     - Name of the task producing the histogram
     - Name of the histogram in the DIM service
   * - savesets
     - Name of the task producing the histogram. The directory of the ROOT file is ``/hist/Savesets/ByRun/TASK``
     - Name of the histogram in the ROOT file 
   * - alarms
     -
     -
   * - wincc
     - Name of the project
     - Name of the datapoint
   * - simulation
     -
     -
   * - trends
     - 
     -

Examples
--------

Data from WinCC archive database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To get the values of the archived data point ``bcm.station_0.flux.rel.rs2_sum`` in the WinCC ``BMBAI`` project, between 
October 10 2023 at 12:30 and October 10 2023 at 15:00 

.. code-block:: python

    import MonitoringHub
    from MonitoringHub.api import default_api
    import json
    import bz2
    from base64 import b64decode
    from datetime import datetime

    configuration = MonitoringHub.Configuration( host = "http://monitoringhub.lbdaq.cern.ch/v1" )

    with MonitoringHub.ApiClient( configuration ) as api_client:
        api_instance = default_api.DefaultApi(api_client)
        source = "wincc"
        partition = "LHCb"
        task = "BMBAI"
        entity = "bcm.station_0.flux.rel.rs2_sum"
        time_start = datetime.strptime('10/10/24 12:30:00', '%m/%d/%y %H:%M:%S')
        time_end   = datetime.strptime('10/10/24 15:00:00', '%m/%d/%y %H:%M:%S')
        server = "dummy"

        try:
            api_response = api_instance.api_hub_get_data(source, partition, task, entity, time_start=time_start, time_end=time_end, server=server)
            # list of (timestamp, value)
            result = json.loads(bz2.decompress(b64decode(api_response.to_dict())))
            print(result)
        except MonitoringHub.ApiException as e:
            print("Error when calling the MonitoringHub server")


