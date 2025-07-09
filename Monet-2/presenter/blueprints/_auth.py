"""Functions to handle authentication in Monet"""

###############################################################################
# (c) Copyright 2000-2020 CERN for the benefit of the LHCb Collaboration      #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
from functools import wraps

from flask import abort, jsonify, redirect, request, session


def get_info(info: str) -> str:
    """Get user information from the CERN authentication system

    Args:
        info (str): Type of information to get

    Returns:
        str: the information
    """
    if "user" not in session:
        abort(401)
    print(session["user"])
    our_var = str(session["user"][info])
    return our_var


def requires_auth(f):
    """requires authentication decorator"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" in session:
            return f(*args, **kwargs)
        else:
            return redirect("/login")

    return decorated_function


def gitlab_webhook(secret=None):
    """decorator for gitlab web authentication"""

    def outer_wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            if secret is not None:
                try:
                    token = request.headers["X-Gitlab-Token"]
                except KeyError:
                    # Unauthorized
                    return jsonify({"result": "no token present"}), 401
            else:
                return jsonify({"result": "no secret present"}), 401
            if token == secret:
                return f(*args, **kwargs)
            else:
                return jsonify({"result": "incorrect token"}), 403  # Forbidden

        return decorated_function

    return outer_wrapper


def python_webhook(secret=None):
    """decorator for python web authentication"""

    def outer_wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            if secret is not None:
                try:
                    token = request.headers["X-Python-Token"]
                except KeyError:
                    # Unauthorized
                    return jsonify({"result": "no token present"}), 401
            else:
                return jsonify({"result": "no secret present"}), 401
            if token == secret:
                return f(*args, **kwargs)
            else:
                return jsonify({"result": "incorrect token"}), 403  # Forbidden

        return decorated_function

    return outer_wrapper
