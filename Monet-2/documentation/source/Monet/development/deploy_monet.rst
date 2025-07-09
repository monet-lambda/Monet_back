Deploy Monet on the online cluster
----------------------------------

When a version of Monet is ready for deployment, commit the changes to the `dockerfile-for-prod branch <https://gitlab.cern.ch/lhcb/Monet/-/tree/dockerfile-for-prod?ref_type=heads>`_
and create a `tag <https://gitlab.cern.ch/lhcb/Monet/-/tags>`_ ``X.Y`` for this new version from that branch. 
This will `trigger in gitlab <https://gitlab.cern.ch/lhcb/Monet/-/blob/dockerfile-for-prod/.gitlab-ci.yml?ref_type=heads>`_ the creation of a docker container with the server running inside. Once 
the `container is built <https://gitlab.cern.ch/lhcb/Monet/-/pipelines>`_ , it can be deployed online with `kubernetes <https://kubernetes.io/>`_. 
The detailed instructions on the online kubernetes system can be found `here <https://lbkubernetes.docs.cern.ch>`_.

In short, the commands are::

    ssh monetkubeclient01
    sudo su kube
    cd /kube/kubernetes-configuration/production/monet
    nano deployment.yaml

Change the version number to the one to be deployed::

    image: gitlab-registry.cern.ch/lhcb/monet:X.Y

and restart the server::

    kubectl apply -f deployment.yaml

Change the configuration files
++++++++++++++++++++++++++++++

The configuration files used in production are in the directory ``/kube/kubernetes-configuration/production/monet``
(these files have to be kept secret and not distributed). After modifying one of them, execute the script ``update_monet_cfg.sh`` located
in the same directory.

The configuration files are:

:monet.cfg: the main Monet configuration file
:keycloak.json: the configuration file for the CERN SSO authentication
:MonetRobotCertificate.pem: the grid certificate to flag runs in Dirac
:MonetRobotKey.pem: the key of the grid certificate

Change the base container
+++++++++++++++++++++++++

In order to speed up the time of the docker container in gitlab, 
a `base container <https://gitlab.cern.ch/lhcb/Monet/-/blob/dockerfile-for-prod/Dockerfile_base?ref_type=heads>`_ is 
built and stored in gitlab. This base container is based on:

* `cern/alma9-base:latest <https://linux.web.cern.ch/almalinux/alma9/>`_ docker image.
* Python 3.12.4
* ROOT v6.32.02.

When major changes are made, for example when changing one of the above software version, or when modifying the list 
of `packages used by Monet <https://gitlab.cern.ch/lhcb/Monet/-/blob/dockerfile-for-prod/requirements.txt?ref_type=heads>`_,
a new base container must be created on a machine with ``docker`` and ``cvmfs`` installed::

    docker login gitlab-registry.cern.ch
    docker build -t gitlab-registry.cern.ch/lhcb/monet/monet-base:alma9-root --file Dockerfile_base .
    docker push  gitlab-registry.cern.ch/lhcb/monet/monet-base:alma9-root

The Dirac credentials used for Offline data quality to flag runs must be loaded inside::

    docker login gitlab-registry.cern.ch
    cp /cvmfs/lhcb.cern.ch/lhcbdirac/etc/dirac.cfg .
    docker build -t gitlab-registry.cern.ch/lhcb/monet/monet-base:alma9-root-dirac --file Dockerfile_base_Dirac .

Copy the files containing the Dirac identification for Monet, ``MonetRobotCertificate.pem`` and ``MonetRobotKey.pem`` 
from ``/home/probbe/Monet`` on the online cluster (these files should not be distributed). 
Run the container::

    docker run -it -v "$(pwd)"/MonetRobotCertificate.pem:/app/MonetRobotCertificate.pem -v "$(pwd)"/MonetRobotKey.pem:/app/MonetRobotKey.pem gitlab-registry.cern.ch/lhcb/monet/monet-base:alma9-root-dirac

and execute inside::

    dirac-proxy-init --nocs -C MonetRobotCertificate.pem -K MonetRobotKey.pem
    dirac-configure --cert MonetRobotCertificate.pem
    dirac-proxy-destroy
    exit
    
Find the ``<id>`` of the container (this is usually the most recent one in the list)::

    docker ps -a

Commit the changes done in the image and upload it to gitlab::

    docker commit <id> gitlab-registry.cern.ch/lhcb/monet/monet-base:alma9-root-dirac
    docker push  gitlab-registry.cern.ch/lhcb/monet/monet-base:alma9-root-dirac

