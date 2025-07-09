Create the MonitoringHub client
=====================================================

When modifying the `API <https://gitlab.cern.ch/lhcb-monitoring/MonitoringHub/-/blob/master/openapi/hub_api.yaml?ref_type=heads>`_ of the 
MonitoringHub server, the `MonitoringHub client <https://gitlab.cern.ch/lhcb-monitoring/MonitoringHubClient>`_ must be updated. 
A script is available in the https://gitlab.cern.ch/lhcb-monitoring/MonitoringHubClient repository. It relies
on the `openapi-generator-cli.jar <https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.9.0/openapi-generator-cli-7.9.0.jar>`_
library::

    git clone ssh://git@gitlab.cern.ch:7999/lhcb-monitoring/MonitoringHub.git
    cd MonitoringHub
    git pull
    cd ..
    git clone ssh://git@gitlab.cern.ch:7999/lhcb-monitoring/MonitoringHubClient.git
    cd MonitoringHubClient
    wget https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.9.0/openapi-generator-cli-7.9.0.jar -O openapi-generator-cli.jar
    . create_client.sh
    git commit -am "New version"
    git push

Once pushed to git, the new version of the package can be installed with::

    pip install git+https://gitlab.cern.ch/lhcb-monitoring/MonitoringHubClient.git

    

