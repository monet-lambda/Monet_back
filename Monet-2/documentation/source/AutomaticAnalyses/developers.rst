.. Automatic analyses developers guide

Automatic analyses developers guide
===================================

The Automatic Analyses source code is maintained in https://gitlab.cern.ch/lhcb-monitoring/AutomaticAnalyses. 

AutomaticAnalyses is a web application based on the `Flask framework <https://flask.palletsprojects.com/en/3.0.x/>`_.
It is usually called from the :ref:`MonitoringHub<MonitoringHub developers guide>`. 

For the most simple modifications of the code, it is easier to modify directly the source code and 
commit to the `Master branch <https://gitlab.cern.ch/lhcb-monitoring/AutomaticAnalyses/-/tree/master>`_ of the git repository. 
This will trigger the deployment of the code to the `online kubernetes infrastructure <https://lbkubernetes.docs.cern.ch>`_
through a `CI/CD in gitlab <https://gitlab.cern.ch/lhcb-monitoring/AutomaticAnalyses/-/ci/editor?branch_name=master>`_. 
The server will be deployed in about 2 minutes (see the `pipeline <https://gitlab.cern.ch/lhcb-monitoring/AutomaticAnalyses/-/pipelines>`_ to monitor the progress of the deployment) online and 
available then with the new code, from :ref:`Monet<Monet user guide>`. The log file of the AutomaticAnalyses server 
can be seen `here <https://lblogs.cern.ch/app/dashboards#/view/e91a2230-dfb6-11ee-b564-855e3ddbbe92?_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:now-15m,to:now))&_a=(description:'',filters:!(),fullScreenMode:!f,options:(hidePanelTitles:!f,useMargins:!t),query:(language:kuery,query:''),timeRestore:!f,title:'Monet%20logs',viewMode:view)>`_. 

.. toctree::
    :maxdepth: 1
    :glob:

    development/setup_env
    development/run_online
