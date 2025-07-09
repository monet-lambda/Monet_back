Run Monet on the devmonet01 (or plus) machine
=============================================

After logging to the machine::

    cd Monet
    source /cvmfs/lhcb.cern.ch/group_login.sh
    lb-conda default
    source .venv/bin/activate
    export PATH=${PATH}:/cvmfs/lhcb.cern.ch/lhcbdirac/versions/v11.0.50-1730118722/Linux-x86_64/bin:/cvmfs/lhcb.cern.ch/lhcbdirac/versions/v11.0.50-1730118722/Linux-x86_64/condabin:/cvmfs/lhcb.cern.ch/lhcbdirac/versions/v11.0.50-1730118722/Linux-x86_64/bin:/cvmfs/lhcb.cern.ch/lhcbdirac/versions/v11.0.50-1730118722/Linux-x86_64/condabin
    export PYTHONPATH=`pwd`:`pwd`/.venv/lib/python3.12/site-packages:/cvmfs/lhcbdev.cern.ch/conda/envs/default/2024-07-10_13-01/linux-64/lib/python3.12/site-packages/
    export MONET_CONFIG=/home/probbe/Monet/configs/monet.cfg
    export PATH=/group/online/bin:${PATH}
    export FLASK_APP=presenter/app.py
    export FLASK_DEBUG=1
    flask run -h 0.0.0.0 -p 8123

To connect to Monet, from the online network, direct a web browser to port 8123 of the address of the machine where the application runs,
for example for devmonet01 ``https://10.128.124.42:8123``.
Alternatively or from outside of the LHCb online network, setup port forwarding with `ssh`::

    kinit <your lxplus login>
    ssh -N -p 22 <your user name>@lxplus.cern.ch -L 127.0.0.1:8123:10.128.124.42:8123

and connect to https://localhost:8123.