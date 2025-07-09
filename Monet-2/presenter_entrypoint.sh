#!/bin/bash
export ROOTSYS=/app/root
source /app/root/bin/thisroot.sh
export PYTHONPATH=/app:${PYTHONPATH}
#python3 presenter/app.py
gunicorn -c config_unicorn.py 'presenter.app:app'

