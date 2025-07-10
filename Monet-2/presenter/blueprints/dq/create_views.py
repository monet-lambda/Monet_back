"""Blueprint functions for Monet"""


from flask import Blueprint

from . import histodb_tree_menu as tree_menu
from . import views
from .render.views import (
    histos_for_path,
    histos_list_for_path,
    prepare_files,
    single_histo,
)


def add_common_dq_views(bp: Blueprint) -> None:
    """Define common URLs

    Args:
        bp (Blueprint): blueprint
    """
    bp.add_url_rule(
        "/save_run_flag", "save_run_flag", views.save_run_flag, methods=["POST"]
    )
    bp.add_url_rule("/elog_submit", "elog_submit", views.elog_submit, methods=["POST"])
    bp.add_url_rule(
        "/change_reference_state",
        "change_reference_state",
        views.change_reference_state,
    )

    bp.add_url_rule("/menutree", "menutree", tree_menu.generate_menu_tree_json)
    bp.add_url_rule(
        "/menu_tree_open_or_close_folder",
        "menu_tree_open_or_close_folder",
        tree_menu.menu_tree_open_or_close_folder,
    )
    bp.add_url_rule("/histo", "histo", histos_for_path)
    bp.add_url_rule("/histo_list", "histo_list", histos_list_for_path)
    bp.add_url_rule("/single_histo", "single_histo", single_histo, methods=["POST"])


def create_offline_dq_bp() -> Blueprint:
    """Define Offline DQ page

    Returns:
        Blueprint: blueprint for offline dq
    """
    bp = Blueprint(
        "offline_dq_bp",
        __name__,
        template_folder="../../templates/dq",
        static_folder="../../static",
    )

    bp.add_url_rule("/", "offline_dq", views.offline_dq)
    add_common_dq_views(bp)
    bp.add_url_rule(
        "/browse_run", "switch_run", views.create_run_switcher(".offline_dq")
    )
    bp.add_url_rule(
        "/get_next_runnumber", "get_next_runnumber", views.get_next_runnumber_rundb
    )
    bp.add_url_rule(
        "/get_previous_runnumber",
        "get_previous_runnumber",
        views.get_previous_runnumber_rundb,
    )

    return bp


def create_history_dq_bp() -> Blueprint:
    """Define History mode page

    Returns:
        Blueprint: blueprint for history mode page
    """
    bp = Blueprint(
        "history_dq_bp",
        __name__,
        template_folder="../../templates/dq",
        static_folder="../../static",
    )

    bp.add_url_rule("/", "history_dq", views.history_dq)
    add_common_dq_views(bp)
    bp.add_url_rule(
        "/browse_run", "switch_run", views.create_run_switcher(".history_dq")
    )
    bp.add_url_rule(
        "/get_next_runnumber", "get_next_runnumber", views.get_next_runnumber_rundb
    )
    bp.add_url_rule(
        "/get_latest_runnumber",
        "get_latest_runnumber",
        views.get_latest_runnumber_rundb,
    )
    bp.add_url_rule(
        "/get_previous_runnumber",
        "get_previous_runnumber",
        views.get_previous_runnumber_rundb,
    )
    bp.add_url_rule("/prepare_files", "prepare_files", prepare_files, methods=["POST"])

    return bp


def create_trends_bp() -> Blueprint:
    """Create page for trend plots

    Returns:
        Blueprint: blueprint for trend plots
    """
    bp = Blueprint(
        "trends_bp",
        __name__,
        template_folder="../../templates/dq",
        static_folder="../../static",
    )

    bp.add_url_rule("/", "trends", views.trends)
    bp.add_url_rule(
        "/change_displayfills_state",
        "change_displayfills_state",
        views.change_displayfills_state,
    )
    add_common_dq_views(bp)

    return bp


def create_online_dq_bp() -> Blueprint:
    """Create page for online DQ

    Returns:
        Blueprint: blueprint for online DQ page
    """
    bp = Blueprint(
        "online_dq_bp",
        __name__,
        template_folder="../../templates/dq",
        static_folder="../../static",
    )

    bp.add_url_rule("/", "online_dq", views.online_dq)
    add_common_dq_views(bp)

    return bp


def create_sim_dq_bp() -> Blueprint:
    """Create sim dq page

    Returns:
        Blueprint: simulation dq blueprint page
    """
    bp = Blueprint(
        "sim_dq_bp",
        __name__,
        template_folder="../../templates/dq",
        static_folder="../../static",
    )

    bp.add_url_rule("/", "sim_dq", views.sim_dq)
    bp.add_url_rule("/menutree", "menutree", tree_menu.generate_menu_tree_json)
    bp.add_url_rule(
        "/menu_tree_open_or_close_folder",
        "menu_tree_open_or_close_folder",
        tree_menu.menu_tree_open_or_close_folder,
    )
    bp.add_url_rule(
        "/change_reference_state",
        "change_reference_state",
        views.change_reference_state,
    )
    bp.add_url_rule("/histo", "histo", histos_for_path)
    bp.add_url_rule("/histo_list", "histo_list", histos_list_for_path)
    bp.add_url_rule("/single_histo", "single_histo", single_histo, methods=["POST"])

    bp.add_url_rule("/browse_req", "browse_req", views.create_run_switcher(".sim_dq"))
    bp.add_url_rule(
        "/get_next_request_id", "get_next_request_id", views.get_next_request_id
    )
    bp.add_url_rule(
        "/get_previous_request_id",
        "get_previous_request_id",
        views.get_previous_request_id,
    )
    bp.add_url_rule("/set_request_id", "set_request_id", views.set_request_id)
    bp.add_url_rule(
        "/get_latest_request_id", "get_latest_request_id", views.get_latest_request_id
    )
    bp.add_url_rule(
        "/get_oldest_request_id", "get_oldest_request_id", views.get_oldest_request_id
    )
    bp.add_url_rule("/get_req_info", "get_req_info", views.get_req_info)

    return bp

def create_page_documentation_bp() -> Blueprint:
    """Create page for page documentations

    Returns:
        Blueprint: blueprint for page documentation
    """
    bp = Blueprint(
        "page_documentation_bp",
        __name__,
        template_folder="../../templates/page_documentation",
        static_folder="../../static",
    )

    bp.add_url_rule("/", "page_documentation", views.page_documentation)
    add_common_dq_views(bp)

    return bp
