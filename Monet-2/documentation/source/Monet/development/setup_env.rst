Setup the Monet development environment on the online plus machines
-------------------------------------------------------------------

Step 1: install the Monet source code from git
++++++++++++++++++++++++++++++++++++++++++++++

Log on the devmonet01 (or a plus) machine in the online cluster:: 

  ssh devmonet01

From the CERN network, log on the gateway first: ``ssh lbgw``.
From outside CERN, log on *lxplus* before loging on *lbgw*.

Checkout the source code from git::

    git clone ssh://git@gitlab.cern.ch:7999/lhcb/Monet.git


Step 2: create a virtual environment for Monet
++++++++++++++++++++++++++++++++++++++++++++++

::

    cd Monet
    source /cvmfs/lhcb.cern.ch/group_login.sh
    lb-conda default
    python -m venv .venv
    source .venv/bin/activate
    export https_proxy=http://lbproxy01.cern.ch:8080
    pip install -r requirements.txt
    pip install git+https://gitlab.cern.ch/lhcb-monitoring/MonitoringHubClient.git
    git clone https://gitlab.cern.ch/lhcb/histoyml.git histoyml
    git clone https://gitlab.cern.ch/lhcb-simulation/simdqdata.git simproddb


Step 3: copy the Monet configuration files
++++++++++++++++++++++++++++++++++++++++++

Monet needs a main configuration file *monet.cfg* in the *configs* directory that contains the connection informations to the various infrastructures it is 
connected to (databases, monitoring hub, Dirac, ...). This file can be found in */home/probbe/Monet/configs*::

    cp /home/probbe/Monet/configs/monet.cfg configs/monet.cfg

In this file, adapt the variable *CACHE_DIR* to point to a directory where you have write access and 
the *HISTODB_DIR* and *SIMPRODDB_DIR* to the location of the *histoyml* and *simproddb* directories. 
Be careful not to add this file to the gitlab repository.

It needs also files for alarms (this is still under development). 

    cp -r /home/probbe/Monet/alarmsdb . 

Step 4: :ref:`Run Monet on the devmonet01 (or plus) machine`
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++