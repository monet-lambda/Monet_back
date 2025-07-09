# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Monitoring'
copyright = '2024,LHCb collaboration'
author = 'Patrick Robbe'
release = 'v1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.autosectionlabel']

templates_path = ['_templates']
exclude_patterns = []
pygments_style = 'sphinx'


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme =  "sphinx_rtd_theme"
#html_static_path = ['_static']

html_context = {
    "display_gitlab": True, # Integrate Gitlab
    "gitlab_host": "gitlab.cern.ch",
    #"gitlab_user": "MyUserName", # Username
    "gitlab_repo": "lhcb-monitoring/Documentations", # Repo name
    "gitlab_version": "master", # Version
    "conf_py_path": "/source/", # Path in the checkout to the docs root
}

html_sidebars = {
   '**': ['globaltoc.html', 'sourcelink.html', 'searchbox.html'],
   'using/windows': ['windows-sidebar.html', 'searchbox.html'],
}

html_theme_options =  {
    'globaltoc_collapse': False,
    'globaltoc_maxdepth': -1,
}
