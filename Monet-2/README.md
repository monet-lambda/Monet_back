# Monet Project (LHCb Data Quality Monitor)

The documentation for developers is here: https://lhcb-monitoring.docs.cern.ch/Monet/developers.html


export ROOTSYS=$(brew --prefix)/opt/root
source "$ROOTSYS/bin/thisroot.sh"

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export MONET_CONFIG="$(pwd)/configs/monet.cfg"

gunicorn -c config_unicorn.py 'presenter.app:app'

python -m presenter.app