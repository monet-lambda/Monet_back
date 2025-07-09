"""Main MONET application

The main file for MONET Flask application
"""

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
import logging
import subprocess
import os
import importlib.util

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from authlib.integrations.flask_client import OAuth
from flask import (
    Flask,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from presenter.cache import cache

# Load configuration early to know where static assets are stored
config_path = os.environ.get("MONET_CONFIG")
static_dir = None
if config_path and os.path.exists(config_path):
    spec = importlib.util.spec_from_file_location("config", config_path)
    _cfg = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_cfg)
    static_dir = getattr(_cfg, "ASSETS_DIRECTORY", None)

if static_dir:
    app = Flask(__name__, static_folder=static_dir)
else:
    app = Flask(__name__)

app.config.from_envvar("MONET_CONFIG")
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache.init_app(app) 

from flask.wrappers import Response
from flask_assets import Bundle, Environment
from flask_cors import cross_origin

from data_load import references
from interfaces import rundb
from interfaces.monitoringhub import (
    # cache,
    monitoringhub_get_online_partitions,
    monitoringhub_get_saveset_partitions,
)

from presenter import blueprints
from presenter.blueprints._auth import gitlab_webhook, requires_auth, python_webhook
from presenter.blueprints.dq import alarms  # noqa: F401
from presenter.blueprints.dq.create_views import (
    create_history_dq_bp,
    create_offline_dq_bp,
    create_online_dq_bp,
    create_sim_dq_bp,
    create_trends_bp,
    create_page_documentation_bp,
)



assets = Environment(app)
layout_css = Bundle(
    "stylesheets/external/bootstrap-3.4.1/css/bootstrap.min.css",
    "stylesheets/external/bootstrap-3.4.1/css/bootstrap-theme.min.css",
    "stylesheets/external/eonasdan-bootstrap-datetimepicker-4.17.49/"
    "bootstrap-datetimepicker.min.css",
    "stylesheets/webmonitor.css",
    filters="cssmin",
    output="stylesheets/gen/packed_layout.css",
)

common_css = Bundle(
    "stylesheets/common.css",
    "stylesheets/external/jquery-ui-themes-1.14.1/themes/base/theme.min.css",
    "stylesheets/external/jstree-3.3.17/themes/default/style.min.css",
    "stylesheets/external/tabulator-6.3.1/css/tabulator.min.css",
    filters="cssmin",
    output="stylesheets/gen/packed_common.css",
)

online_dq_css = Bundle(
    "stylesheets/online_dq.css",
    filters="cssmin",
    output="stylesheets/gen/packed_online_dq.css",
)

history_dq_css = Bundle(
    "stylesheets/history_dq.css",
    filters="cssmin",
    output="stylesheets/gen/packed_history_dq.css",
)

offline_dq_css = Bundle(
    "stylesheets/offline_dq.css",
    filters="cssmin",
    output="stylesheets/gen/packed_offline_dq.css",
)

sim_dq_css = Bundle(
    "stylesheets/sim_dq.css",
    filters="cssmin",
    output="stylesheets/gen/packed_sim_dq.css",
)

trend_dq_css = Bundle(
    "stylesheets/trends.css",
    filters="cssmin",
    output="stylesheets/gen/packed_trend_dq.css",
)

documentation_page_css = Bundle(
    "stylesheets/page_documentation.css",
    filters="cssmin",
    output="stylesheets/gen/packed_page_documentation.css",
)


assets.register("css_layout", layout_css)
assets.register("css_all", common_css)
assets.register("css_online_dq", online_dq_css)
assets.register("css_history_dq", history_dq_css)
assets.register("css_offline_dq", offline_dq_css)
assets.register("css_sim_dq", sim_dq_css)
assets.register("css_trend_dq", trend_dq_css)
assets.register("css_documentation_page", documentation_page_css)

layout_js = Bundle(
    "javascripts/external/jquery-3.7.1/jquery-3.7.1.min.js",
    "javascripts/external/bootstrap-3.4.1/bootstrap.min.js",
    "javascripts/external/moment-2.30.1/moment.min.js",
    "javascripts/external/eonasdan-bootstrap-datetimepicker-4.17.49/"
    "bootstrap-datetimepicker.min.js",
    "javascripts/external/js-cookie-3.0.5/js.cookie.min.js",
    filters="rjsmin",
    output="javascripts/gen/packed_layout.js",
)

common_js = Bundle(
    "javascripts/external/jquery-ui-1.14.1/jquery-ui.min.js",
    "javascripts/external/jstree-3.3.17/jstree.min.js",
    "javascripts/external/bokeh-3.7.2/bokeh.min.js",
    "javascripts/external/bokeh-3.7.2/bokeh-widgets.min.js",
    "javascripts/external/bokeh-3.7.2/bokeh-tables.min.js",
    "javascripts/external/html2canvas-1.4.1/html2canvas.min.js",
    "javascripts/histogram_tools.js",
    filters="rjsmin",
    output="javascripts/gen/packed_common.js",
)

online_dq_modules_js = Bundle(
    "javascripts/external/spin-4.1.2/spin.min.js",
    "javascripts/external/mustache-4.2.0/mustache.min.js",
    "javascripts/histoDB_menu.js",
    "javascripts/elog.js",
    "javascripts/dq.js",
    "javascripts/online_dq_topbar.js",
    "javascripts/alarm_menu.js",
    filters="rjsmin",
    output="javascripts/gen/packed_online_dq_modules.js",
)

offline_dq_modules_js = Bundle(
    "javascripts/external/spin-4.1.2/spin.min.js",
    "javascripts/external/mustache-4.2.0/mustache.min.js",
    "javascripts/external/tabulator-6.3.1/tabulator.min.js",
    "javascripts/histoDB_menu.js",
    "javascripts/elog.js",
    "javascripts/dq.js",
    "javascripts/offline_dq_topbar.js",
    filters="rjsmin",
    output="javascripts/gen/packed_offline_dq_modules.js",
)

history_dq_modules_js = Bundle(
    "javascripts/external/spin-4.1.2/spin.min.js",
    "javascripts/external/mustache-4.2.0/mustache.min.js",
    "javascripts/histoDB_menu.js",
    "javascripts/elog.js",
    "javascripts/dq.js",
    "javascripts/history_dq_topbar.js",
    "javascripts/alarm_menu.js",
    filters="rjsmin",
    output="javascripts/gen/packed_history_dq_modules.js",
)

trend_dq_modules_js = Bundle(
    "javascripts/external/spin-4.1.2/spin.min.js",
    "javascripts/external/mustache-4.2.0/mustache.min.js",
    "javascripts/histoDB_menu.js",
    "javascripts/elog.js",
    "javascripts/dq.js",
    "javascripts/trends_dq_topbar.js",
    # filters='rjsmin',
    output="javascripts/gen/packed_trend_dq_modules.js",
)

sim_dq_modules_js = Bundle(
    "javascripts/external/spin-4.1.2/spin.min.js",
    "javascripts/external/mustache-4.2.0/mustache.min.js",
    "javascripts/histoDB_menu.js",
    "javascripts/elog.js",
    "javascripts/dq.js",
    "javascripts/sim_dq_topbar.js",
    "javascripts/alarm_menu.js",
    filters="rjsmin",
    output="javascripts/gen/packed_sim_dq_modules.js",
)

page_documentation_modules_js = Bundle(
    "javascripts/external/mustache-4.2.0/mustache.min.js",
    "javascripts/histoDB_menu.js",
    "javascripts/dq.js",
    "javascripts/page_documentation_topbar.js",
    filters="rjsmin",
    output="javascripts/gen/packed_page_documentation_modules.js",
)

assets.register("js_layout", layout_js)
assets.register("js_common", common_js)
assets.register("js_online_dq_modules", online_dq_modules_js)
assets.register("js_offline_dq_modules", offline_dq_modules_js)
assets.register("js_sim_dq_modules", sim_dq_modules_js)
assets.register("js_trend_dq_modules", trend_dq_modules_js)
assets.register("js_history_dq_modules", history_dq_modules_js)
assets.register("js_page_documentation_modules", page_documentation_modules_js)



app.developer = app.config.get("MONET_DEVELOPER")
log_level = app.config.get("MONET_LOGLEVEL", logging.INFO)
sh_log_level = app.config.get("MONET_SH_LOGLEVEL", logging.INFO)

logging.basicConfig(
    format="(%(filename)s:%(lineno)d//%(levelname)s)\t%(message)s", level=log_level
)
logging.getLogger("sh").setLevel(sh_log_level)
logging.getLogger("filelock").setLevel(log_level)
logging.getLogger("werkzeug").setLevel(log_level)

oauth = OAuth(app)
oauth.register(
    name="CERN",
    server_metadata_url=("https://auth.cern.ch/auth/realms/cern/"
    ".well-known/openid-configuration"),
    client_kwargs={"scope": "openid profile email"},
)


@app.route("/login")
def login():
    """Login function

    Calls the CERN SSO login infrastructure

    Returns:
        A HTTP redirect response
    """
    # redirect_uri = url_for("auth", _external=True)
    # return oauth.CERN.authorize_redirect(redirect_uri)
    """DEV-заглушка входа без CERN"""
    logging.warning("Bypassing CERN SSO in /login")
    session['user'] = {
        "name": "Dev User",
        "email": "dev@localhost",
        "cern_uid": "devuser",
        "preferred_username": "test"
    }
    return redirect('/')


@app.route("/auth")
def auth() -> Response:
    """Authenticate via CERN SSO

    Returns:
        Response: A HTTP redirect response
    """
    try:
        token = oauth.CERN.authorize_access_token()
        user = oauth.CERN.userinfo(token=token)
    except Exception:
        logging.error("Error in authentication")
        # Logout
        logout_url = ("https://auth.cern.ch/auth/realms/cern/"
        "protocol/openid-connect/logout")
        session.pop("user", None)
        return redirect(f"{logout_url}?client_id={{app.config.get('CERN_CLIENT_ID')}}")
    session["user"] = user
    return redirect("/")


@app.route("/logout")
@requires_auth
def logout() -> Response:
    """Logout from CERN SSO

    Returns:
        Response: A HTTP redirect response
    """
    logout_url = ("https://auth.cern.ch/auth/realms/cern/"
    "protocol/openid-connect/logout")
    session.pop("user", None)
    return redirect(f"{logout_url}?client_id={{app.config.get('CERN_CLIENT_ID')}}")


@app.route("/api/git_update", methods=["POST"])
@gitlab_webhook(secret=app.config.get("HISTOYML_KEY"))
def git_update() -> tuple[Response, int]:
    """Triggers a git pull in a local repo of the histoyml repository
       upon receiving a GitLab webhook

    Returns:
        tuple[Response, int]: web response and HTML return code
    """
    payload = request.get_json()
    if payload is None:
        return jsonify({"result": "no JSON payload"}), 400  # Bad request
    try:
        project_id = int(payload["project_id"])
    except KeyError:
        return jsonify({"result": "no project ID present"}), 400  # Bad request
    try:
        db_name = {
            92850: "HISTODB",  # TODO: get project IDs from config?
            140017: "SIMPRODDB",
        }[project_id]
    except KeyError:
        # Bad request
        return jsonify({"result": f"unknown project ID {project_id}"}), 400
    try:
        app.config.get(db_name).get_files()
        return jsonify({"result": f"updated {db_name}"}), 200  # OK
    except BaseException as e:
        return jsonify({"result": str(e)}), 500  # Internal server error


@app.route("/api/automaticanalysis_update", methods=["POST"])
@gitlab_webhook(secret=app.config.get("AAYML_KEY"))
def aagit_update() -> tuple[Response, int]:
    """Call the Automatic Analysis server to update the yaml git
    repository there. This function in Monet is called from a web
    hook in the AutomaticAnalysisYaml git repository

    Raises:
        BaseException: In case of error sent from the automatic
        analysis server

    Returns:
        tuple[Response, int]: web response and HTML return code
    """
    payload = request.get_json()
    if payload is None:
        return jsonify({"result": "no JSON payload"}), 400  # Bad request
    try:
        project_id = int(payload["project_id"])
    except KeyError:
        return jsonify({"result": "no project ID present"}), 400  # Bad request
    try:
        db_name = {
            162244: "https://lbautomaticanalyses.cern.ch/api/updateyaml",
        }[project_id]
    except KeyError:
        return jsonify(
            {"result": f"unknown project ID {project_id}"}
        ), 400  # Bad request
    try:
        r = requests.get(db_name, verify=False)
        if r.status_code != 200:
            raise BaseException("access denied")
        return jsonify({"result": f"updated {db_name}"}), 200  # OK
    except BaseException as e:
        return jsonify({"result": str(e)}), 500  # Internal server error


@app.route("/api/is_alive")
def is_alive() -> Response:
    """Function used by kubernetes to check if the application is running,
    to be able to restart it if not

    Returns:
        Response: HTML response with json message
    """
    return jsonify({"result": "success"})


@app.route("/create_dqdb")
@requires_auth
def create_dqdb() -> Response:
    """Create Data Quality database
    Web entry point to call the create db DQDB database function

    Returns:
        Response: HTML response with json message
    """
    from interfaces.dqdb import create_dqdb_tables, create_monet_user

    if create_monet_user():
        if create_dqdb_tables():
            return jsonify({"result": "success"})
    return jsonify({"result": "error creating dqdb"})


@app.route("/transfer_dqdb")
@requires_auth
def transfer_dqdb() -> Response:
    """Transfer Data Quality database
    Web entry point to call the transfer db DQDB database function

    Returns:
        Response: HTML response with json message
    """
    from interfaces.dqdb import transfer_monet_dqdb

    if transfer_monet_dqdb():
        return jsonify({"result": "success"})
    return jsonify({"result": "error transfering dqdb"})


@app.route("/create_system/<path:name>")
@requires_auth
def create_sys(name: str) -> Response:
    """Create system in the DQDB
    Calls the create system DQDB function from web

    Args:
        name (str): name of the system to create in the DQDB

    Returns:
        Response: HTML response with json message
    """
    from interfaces.dqdb import create_system

    if create_system(name):
        return jsonify({"result": "success"})
    return jsonify({"result": f"error creating system {name}"})


@app.route("/get_systems")
@requires_auth
def get_systems() -> Response:
    """Get list of all systems in DQDB
    Calls get list of systems function from the web

    Returns:
        Response: HTML response with json message
    """
    from interfaces.dqdb import get_list_systems

    syts = get_list_systems()
    s = ""
    for sy in syts:
        s = sy + " " + s
    return jsonify({"result": s})


@app.route("/get_2025_runs")
@python_webhook(secret=app.config.get("PYTHON_KEY"))
def get_2025_runs() -> Response:
    """Get list of runs taken in 2025 with destination offline

    Returns:
        Response: HTML response with json message
    """
    from interfaces.rundb import get_all_runs_in_2025
    return get_all_runs_in_2025()


@app.route("/figures/<path:name>")
def show_figure(name: str) -> Response:
    """Display image file from the /hist/Reference/figures repository

    Args:
        name (str): name of the image file (relative to the
        /hist/Reference/figures repository)

    Returns:
        Response: HTML redirect
    """
    return send_from_directory("/hist/Reference/figures", name, as_attachment=True)


@app.route("/ROOT/<path:name>")
@cross_origin()
def show_roothisto(name: str) -> Response:
    """Show ROOT histogram in JSON ROOT format, calling
    an external ROOT JS server

    Args:
        name (str): name of the JSON ROOT file, relative to
        /hist/Monet/ROOT

    Returns:
        Response: HTML redirect
    """
    return send_from_directory(
        current_app.config.get("JSON_FILES_PATH", "/hist/Monet/ROOT"), name
    )


@app.route("/favicon.ico")
def favicon() -> Response:
    """Returns the favicon image (for Firefox)

    Returns:
        Response: HTML redirect
    """
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/")
@requires_auth
def index() -> str:
    """Returns the main Monet page

    Returns:
        str: code of the HTML page
    """
    return render_template("Hello.html", bplist=current_app.config["PROJECTS"])


@app.errorhandler(404)
def resource_not_found(e) -> Response:
    """Function to call in case of exception 404

    Args:
        e (exception): the exception thrown

    Returns:
        Response: HTML response with json message containing the error
    """
    split_message = e.description.split(":")
    i = -1
    if len(split_message) > 1:
        i = split_message[0]
        split_message = split_message[1]
    return jsonify(error=split_message, number=i), 404


@app.errorhandler(FileNotFoundError)
def handle_filenotfound(e) -> Response:
    """Function to call in case of exception FileNotFound

    Args:
        e (exception): the exception thrown

    Returns:
        Response: HTML response with json message
    """
    exception_url = request.url
    logging.error(f"Error with cache : {exception_url}")
    return jsonify({"message": "Error with cache"}), 404


def saveset_partitions_view() -> Response:
    """Returns the list of partitions for history mode

    Returns:
        Response: HTML response with list of partitions
    """
    monhub_config = current_app.config["MONHUB_CONFIG"]
    the_path = current_app.config["PATH_HISTOS"]
    return jsonify(
        {
            "partitions": list(
                monitoringhub_get_saveset_partitions(monhub_config, the_path)
            )
        }
    )


def online_partitions_view() -> Response:
    """Returns the list of partitions in online mode

    Returns:
        Response: HTML response with list of partitions
    """
    monhub_config = current_app.config["MONHUB_CONFIG"]
    dim_dns_node = current_app.config["DIM_DNS_NODE"]
    return jsonify(
        {
            "partitions": list(
                monitoringhub_get_online_partitions(monhub_config, dim_dns_node)
            )
        }
    )


app.add_url_rule("/partitions/saveset", "saveset_partitions", saveset_partitions_view)

app.add_url_rule("/partitions/online", "online_partitions", online_partitions_view)

app.register_blueprint(create_offline_dq_bp(), url_prefix="/offline_dq")
app.register_blueprint(create_history_dq_bp(), url_prefix="/history_dq")
app.register_blueprint(create_online_dq_bp(), url_prefix="/online_dq")
app.register_blueprint(create_sim_dq_bp(), url_prefix="/sim_dq")
app.register_blueprint(create_trends_bp(), url_prefix="/trends")
app.register_blueprint(create_page_documentation_bp(), url_prefix="/page_documentation")

app.add_url_rule("/alarms", "alarms", blueprints.dq.alarms.alarms_view)
# app.add_url_rule('/alarms/new', 'alarms_new', blueprints.dq.alarms_new,
#  methods=['POST'])
# app.add_url_rule('/alarms/clear', 'alarms_clear', blueprints.dq.alarms_clear,
# methods=['POST'])
app.add_url_rule("/rundb", "rundb_info", rundb.rundb_info_view)
app.add_url_rule("/rundb_range", "rundb_range", rundb.rundb_info_range)
app.add_url_rule("/flag_run_range", "flag_run_range", rundb.flag_run_range)
app.add_url_rule(
    "/flag_extra_run_range", "flag_extra_run_range", rundb.flag_extra_run_range
)
app.add_url_rule("/rundb_json", "rundb_json", rundb.rundb_json)
app.add_url_rule("/online_runnumber", "online_runnumber", rundb.online_runnumber_view)
app.add_url_rule("/update_reference", "update_reference", references.update_references)


def sensor() -> None:
    """Function called every 20h to renew the Dirac proxy"""
    logging.warning("Renew grid proxy")
    try:
        process = subprocess.run( ["lhcb-proxy-init", "-C", "MonetRobotCertificate.pem", "-K", "MonetRobotKey.pem"], capture_output=True, timeout=30 )
        output = process.stdout.decode('UTF-8')
        logging.warning(output)
    except (subprocess.CalledProcessorError):
        logging.error("Problem renewing proxy")
        output = process.stderr.decode('UTF-8')
        logging.error(output)

def on_starting(server) -> None:
    """Function on starting, called by gunicorn before starting the
    Monet servers
    """
    sensor()
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(sensor, "interval", hours=20)
    sched.start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8223, debug=True)
