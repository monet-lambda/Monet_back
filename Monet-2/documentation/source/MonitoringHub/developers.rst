.. MonitoringHub developers guide

MonitoringHub developers guide
==============================

The MonitoringHub source code is maintained in https://gitlab.cern.ch/lhcb-monitoring/MonitoringHub. 

MonitoringHub is a web application based on the `Flask framework <https://flask.palletsprojects.com/en/3.0.x/>`_. 
It is called from :ref:`Monet<Monet developers guide>` to obtain the data to display. To develop with MonitoringHub, it has to be done usually
with a local Monet instance that can be run as :ref:`described here<Run Monet on the devmonet01 (or plus) machine>`.


.. toctree::
    :maxdepth: 1
    :glob:

    development/setup_env
    development/run_online
    development/deploy_monitoringhub
    development/create_client
