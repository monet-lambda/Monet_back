Setup the MonitoringHub development environment on the online plus machines
---------------------------------------------------------------------------

Step 1: install the MonitoringHub source code from git
++++++++++++++++++++++++++++++++++++++++++++++++++++++

Log on the devmonet01 (or a plus) machine in the online cluster:: 

  ssh devmonet01

From the CERN network, log on the gateway first: ``ssh lbgw``.
From outside CERN, log on *lxplus* before loging on *lbgw*.

Checkout the source code from git::

    git clone ssh://git@gitlab.cern.ch:7999/lhcb-monitoring/MonitoringHub.git


Step 2: create a virtual environment for MonitoringHub
++++++++++++++++++++++++++++++++++++++++++++++++++++++

::

    cd MonitoringHub
    source /cvmfs/lhcb.cern.ch/group_login.sh
    lb_set_platform x86_64_v2-el9-gcc13-opt
    python -m venv .venv
    source .venv/bin/activate
    export https_proxy=http://lbproxy01.cern.ch:8080
    pip install -r requirements.txt

Step 3: create the MonitoringHub configuration files
++++++++++++++++++++++++++++++++++++++++++++++++++++

MonitoringHub needs a configuration file *hub.cfg* that contains the connection informations to the various infrastructures it is 
connected to (databases, monitoring hub, Dirac, ...). The secret keys or passwords can be asked to patrick.robbe@ijclab.in2p3.fr. 

The content of the *hub.cfg* configuration file is:

.. code-block:: python
    
    USE_DIRECTWINCC = True
    CACHE_TYPE= "FileSystemCache"
    CACHE_DEFAULT_TIMEOUT= 300
    CACHE_DIR="set to a directory in your home space"
    AA_HOST = "http://lbautomaticanalyses.cern.ch"  # Address of the automatic analysis server host
    AA_SERVER = AA_HOST+"/v1"
    SECRET_KEY = "ask"
    TESTING = True # True for testing mode
    DEBUG = True # Set debug mode
    LOCALRUN = True # Set to true if you run on devmonet01
    import logging
    LOGLEVEL = logging.WARNING # log level

    # Data quality database (DQDB) connection informations (used for trend plots)
    DQDB_USER = "monitoringhub"  
    DQDB_PASSWORD = "ask"
    DQDB_HOST = "dbod-lbdqdb.cern.ch"
    DQDB_PORT = 5503
    DQDB_DATABASE = "trends"

    # Data quality database (DQDB) HLT piquet connection informations (used for trend plots)
    DQDB_HLTPIQUET_USER = "hltpiquet"
    DQDB_HLTPIQUET_PASSWORD = "ask"
    DQDB_AUTH_KEY = "ask"
    DQDB_AUTH_USER = "HLTPiquet"

    USE_DIRECTWINCC = True # Set to true to connect directly to the WinCC oracle database
    if USE_DIRECTWINCC:
        WINCC_USER = "wincc_lb_reader"
        WINCC_PASSWORD = "ask"
        WINCC_DBNAME = "lhcbonr_pvssprod"

Step 4: :ref:`Run MonitoringHub on the devmonet01 (or plus) machine`
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++