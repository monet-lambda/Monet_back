Histo Yaml
==========

The pages in Monet are defined with yaml files, stored in https://gitlab.cern.ch/lhcb/histoyml.
The syntax of the files is described in the :ref:`Monet user guide<Add a page>`.

In addition, after every commit to the git repository, the git folder in the Monet server is 
automatically updated `with a gitlab webhook <https://gitlab.cern.ch/lhcb/histoyml/-/hooks>`_. 
The location of the directory where the histo yaml files are checked out in the server is 
`/histoyml` by default. It is a directory which is common to all instances of the Monet 
servers online. This location can be modified in the *Monet.cfg* :ref:`configuration file<Change the configuration files>`::

    HISTODB_DIR = '/histoyml/'

A key is used to authenticate the webhook to the Monet server. On the server side, the key is 
set in the *Monet.cfg* :ref:`configuration file<Change the configuration files>`::

    HISTOYML_KEY = XXXXXX
