### How to test locally the web pages

#### Installation of the environment and packages (required once)

     python -m venv myenv
     source myenv/bin/activate
     pip install sphinx sphinx-autobuild sphinx_rtd_theme

#### Creation of the documentation

     source myenv/bin/activate
     make html
     python -m http.server --directory build/html/
