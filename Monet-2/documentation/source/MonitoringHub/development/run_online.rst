Run MonitoringHub on the devmonet01 (or plus) machine
=====================================================

After logging to the machine::

    cd MonitoringHub
    source /cvmfs/lhcb.cern.ch/group_login.sh
    lb_set_platform x86_64_v2-el9-gcc13-opt
    lb-run Online/v7r25 bash
    source .venv/bin/activate
    export LD_LIBRARY_PATH=/cvmfs/lhcb.cern.ch/lib/lcg/releases/ROOT/6.30.04-dd2db/x86_64-el9-gcc13-opt/lib:${LD_LIBRARY_PATH}
    export PYTHONPATH=`pwd`:`pwd`/.venv/lib/python3.9/site-packages:/cvmfs/lhcb.cern.ch/lib/lcg/releases/ROOT/6.30.04-dd2db/x86_64-el9-gcc13-opt/lib:${PYTHONPATH}
    export MONITORINGHUB_CONFIG=`pwd`/hub.cfg
    python app.py

The connection to the MonitoringHub is done from Monet and set up in the *Monet.cfg*  :ref:`Monet configuration file<Step 3: copy the Monet configuration files>`:

::

    import MonitoringHub
    MONHUB_CONFIG = MonitoringHub.Configuration(
        #host = "http://monitoringhub.lbdaq.cern.ch/v1" # If using the deployed MonitoringHub server
        host="http://10.128.124.42:5000/v1"  # If using a local MonitoringHub server on monetdev01
    )