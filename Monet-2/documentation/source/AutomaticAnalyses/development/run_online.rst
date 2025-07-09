Run AutomaticAnalyses on the devmonet01 (or plus) machine
=========================================================

After logging to the machine::

    cd AutomaticAnalyses
    source /cvmfs/lhcb.cern.ch/group_login.sh
    lb_set_platform x86_64_v2-el9-gcc13-opt
    lb-run Online/v7r25 bash
    source .venv/bin/activate
    export LD_LIBRARY_PATH=/cvmfs/lhcb.cern.ch/lib/lcg/releases/ROOT/6.30.04-dd2db/x86_64-el9-gcc13-opt/lib:${LD_LIBRARY_PATH}
    export PYTHONPATH=/cvmfs/lhcb.cern.ch/lib/lhcb/ONLINE/ONLINE_v7r25/Online/Gaucho/python:${PYTHONPATH}
    export PYTHONPATH=`pwd`/.venv/lib/python3.9/site-packages:/cvmfs/lhcb.cern.ch/lib/lcg/releases/ROOT/6.30.04-dd2db/x86_64-el9-gcc13-opt/lib:${PYTHONPATH}
    export AA_CONFIG=aa.cfg
    python app.py

The connection to the AutomaticAnalyses server is done via the :ref:`MonitoringHub<MonitoringHub developers guide>`, changing in 
the :ref:`configuration file<Step 3: create the MonitoringHub configuration files>` *hub.cfg* the variable AA_HOST to

::

    AA_HOST = "http://10.128.124.42:5001"