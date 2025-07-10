# Monet Project (LHCb Data Quality Monitor)

The documentation for developers is here: https://lhcb-monitoring.docs.cern.ch/Monet/developers.html

python3 -m venv .venv

export ROOTSYS=$(brew --prefix)/opt/root
source "$ROOTSYS/bin/thisroot.sh"


source .venv/bin/activate
pip install -r requirements.txt

export MONET_CONFIG="$(pwd)/configs/monet.cfg"

python -m presenter.app

gunicorn -c config_unicorn.py 'presenter.app:app'

