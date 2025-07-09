Deploy MonitoringHub on the online cluster
------------------------------------------

When a version of MonitoringHub is ready for deployment, commit the changes to the `mater branch <https://gitlab.cern.ch/lhcb-monitoring/MonitoringHub/-/tree/master?ref_type=heads>`_
and create a `tag <https://gitlab.cern.ch/lhcb-monitoring/MonitoringHub/-/tags>`_ ``X.Y`` for this new version from that branch. 
This will `trigger in gitlab <https://gitlab.cern.ch/lhcb-monitoring/MonitoringHub/-/blob/master/.gitlab-ci.yml>`_ the creation of a docker container with the server running inside. Once 
the `container is built <https://gitlab.cern.ch/lhcb-monitoring/MonitoringHub/-/pipelines>`_ , it can be deployed online with `kubernetes <https://kubernetes.io/>`_. 
The detailed instructions on the online kubernetes system can be found `here <https://lbkubernetes.docs.cern.ch>`_.

In short, the commands are::

    ssh monetkubeclient01
    sudo su kube
    cd /kube/kubernetes-configuration/production/monitoringhub
    nano deployment.yaml

Change the version number to the one to be deployed::

    image: gitlab-registry.cern.ch/lhcb/monitoringhub:X.Y

and restart the server::

    kubectl apply -f deployment.yaml

Change the MonitoringHub configuration files
++++++++++++++++++++++++++++++++++++++++++++

The configuration files used in production are in the directory ``/kube/kubernetes-configuration/production/monitoringhub``
(these files have to be kept secret and not distributed). After modifying one of them, execute the script ``update_monitoringhub_cfg.sh`` located
in the same directory.

The configuration files are:

:hub.cfg: the main MonitoringHub configuration file
:tnsnames.ora: the configuration file for the connection to the Oracle WinCC database
