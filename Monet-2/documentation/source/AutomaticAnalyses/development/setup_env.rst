Setup the automatic analysis development environment on the online plus machines
--------------------------------------------------------------------------------

Step 1: install the AutomaticAnalyses source code from git
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Log on the devmonet01 (or a plus) machine in the online cluster:: 

  ssh devmonet01

From the CERN network, log on the gateway first: ``ssh lbgw``.
From outside CERN, log on *lxplus* before loging on *lbgw*.

Checkout the source code from git::

    git clone ssh://git@gitlab.cern.ch:7999/lhcb-monitoring/AutomaticAnalyses.git


Step 2: create a virtual environment for AutomaticAnalyses
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

::

    cd AutomaticAnalyses
    source /cvmfs/lhcb.cern.ch/group_login.sh
    lb_set_platform x86_64_v2-el9-gcc13-opt
    lb-run Online/v7r25 bash
    python -m venv .venv
    source .venv/bin/activate
    export https_proxy=http://lbproxy01.cern.ch:8080
    pip install -r requirements.txt

Step 3: create the AutomaticAnalyses configuration file
+++++++++++++++++++++++++++++++++++++++++++++++++++++++

The AutomaticAnalyses server needs a main configuration file *aa.cfg* that should be placed in the directory where the AutomaticAnalyses
server is installed. Be careful not to add the *aa.cfg* file to the gitlab repository.
The full content of the *aa.cfg* file is given in the example below:

::

    import logging
    APP_NAME = 'AutomaticAnalysis'
    LOGLEVEL = logging.INFO  # Set the log level
    YAMLDIR = '/home/probbe/automaticanalysisyaml/'  # Set the directory with the Yaml files are stored
    USE_DIM = False  # Set to True to use DIM (usually only for the production version, keep False for developping)

    INIT_DQDB = False  # Initialize the Data Quality Database, keep to False except when creating the database for the first time
    DQDB_ADMIN_USER = "admin" 
    DQDB_ADMIN_PASSWORD = "yaadminepassword"   # Set the Data quality database password
    DQDB_USER = "aa"
    DQDB_PASSWORD = "auserpassword"
    DQDB_HOST = "dbod-dqdbtest.cern.ch"  # Use this test database or create your own
    DQDB_PORT = 5501
    DQDB_DATABASE = "trends"


In this file, adapt the variable *YAMLDIR* to point to a directory where you have write access and 
where you have cloned the `AutomaticAnalysesYAML <https://gitlab.cern.ch/lhcb-monitoring/automaticanalysisyaml>`_ git directory:

::

    git clone ssh://git@gitlab.cern.ch:7999/lhcb-monitoring/automaticanalysisyaml.git
    

Step 4: :ref:`Run AutomaticAnalyses on the devmonet01 (or plus) machine`
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++