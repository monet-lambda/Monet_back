"""Functions to handle the pages tree in Monet"""


import json
import time
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask.wrappers import Response

from .._auth import get_info, requires_auth
from .._user_settings import UserSettings

settings = UserSettings()

histogramDB_tree_menu = Blueprint(
    "histogramDB_tree_menu",
    __name__,
    template_folder="../templates/histogramDB_tree_menu",
    static_folder="../static",
)


@requires_auth
def generate_menu_tree_json() -> str:
    """Called by javascript via ajax call. Returns menu tree in json format.
    Receives two parameters during the ajax call:

    load_from_db_flag: the tree is cached to increase the speed of the menu
    generation. If this string (!!) == "true", the menu is freshly read from
    the database. If load_from_db_flag == "false" it is read from the cache
    file (if it exists)

    all_nodes_standard_state: When rereading from the database, this string
    determines if all nodes shall be opened or
    closed. Used by the "expand all" and "collapse all" button.


    Returns:
        str: tree in a json string
    """
    try:
        settings.set_option_with_tree(get_info("cern_uid"))
    except Exception:
        pass

    load_from_db_flag = request.args.get("loadFromDBFlag")
    all_nodes_standard_state = request.args.get("allNodesStandardState")
    filter_flag = request.args.get("filterFlag")
    menutree_timestamp = request.args.get("menutree_timestamp")

    menutree = generate_menu(
        load_from_db_flag, all_nodes_standard_state, filter_flag, menutree_timestamp
    )

    return menutree


@requires_auth
def sim_dq_tree() -> str:
    """Returns sim dq tree

    Returns:
        str: tree in json string
    """
    sim_dq_tree = [
        {
            "text": "/",
            "icon": "glyphicon glyphicon-folder-close",
            "state": {"selected": False, "opened": True},
            "children": [
                {
                    "text": "Generator",
                    "id": "/Generator",
                    "icon": "glyphicon glyphicon-file",
                },
                {
                    "text": "MCTruth",
                    "id": "/MCTruth",
                    "icon": "glyphicon glyphicon-file",
                },
            ],
        }
    ]

    menu_as_json_string = json.dumps(
        {
            "current_actual": False,
            "menutree_json": sim_dq_tree,
            "menutree_timestamp": time.mktime(datetime.now().timetuple()),
        }
    )

    return menu_as_json_string


@requires_auth
def menu_tree_open_or_close_folder() -> Response:
    """This method is called via ajax by javascript whenever a folder is
    opened or closed. The idea is to save this in the cache, so that when you
    reload the page or open anorther page, the tree state is persisted.
    This method receives to parameters via GET:
    folder_id: The folder_id of the node opened. This has to start with //F//,
    which denotes folders. After //F// the path follows, i.e. //FF///a/b/c
    action: Whether a node was closed or opened

    Raises:
        Exception: when problems in the tree

    Returns:
        Response: HTML response
    """

    try:
        settings.set_option_with_tree(get_info("cern_uid"))
    except Exception:
        pass
    folder_id = request.args.get("id")
    action = request.args.get("action")

    # Event came from a folder
    if folder_id.startswith("//F//"):
        folder_name = folder_id[5:]

        # Contains the parts of the path, e.g. /a/b/c => [a, b, c]
        # Root directory
        if folder_name == "":
            folder_name = "/"
            path_parts = [""]
        else:
            path_parts = folder_name.split("/")

        # Fetch structure from file
        menu_as_complex_object = settings.read_tree()

        # Containes the root folder
        # we are moving outgoing from root folder to the folder,
        # which shall have opened -> True
        current_folder = menu_as_complex_object

        if not current_folder:
            generate_menu()
            del menu_as_complex_object
            menu_as_complex_object = settings.read_tree()
            current_folder = menu_as_complex_object

        # this loop iterates over the folders contained in the via AJAX Get
        # given folder_id attribute, e.g.
        # /a/b/c
        # over a then b then c
        i = 0
        # in: path_parts, current_folder
        # out lookingAtPath, loo
        while i < len(path_parts):
            # this loop iterates over all all folders contained in the current
            # root object, i.e.
            # /a/b/c
            # /a/u/v
            # /a/u/w
            # and looking for /a/u/v
            # iterate over "/" finding a, iterate over a finding u, then
            # iterate over u finding v
            j = 0
            while j < len(current_folder):
                # just shortcut for current_folder[j]
                looking_at_folder = current_folder[j]

                # if name of the folder matches the name of the via GET
                # given path
                if looking_at_folder["text"] == path_parts[i]:
                    # something went wrong, reached leaf also expecting folder
                    if "children" not in looking_at_folder:
                        raise Exception("Reached lead unexpectedly")

                    # next step would not be the last step, therefore make a
                    # further step down the folder hirachy
                    if not i + 1 == len(path_parts):
                        current_folder = looking_at_folder["children"]
                    # change state
                    # close only last folder
                    else:
                        # change state
                        # close only last folder
                        if action == "close":
                            looking_at_folder["state"]["opened"] = False
                            looking_at_folder["icon"] = (
                                "glyphicon glyphicon-folder-close"
                            )

                    # change state
                    # open all folders
                    if action == "open":
                        looking_at_folder["state"]["opened"] = True
                        looking_at_folder["icon"] = "glyphicon glyphicon-folder-open"

                    break
                j += 1
            # END: while j < len(keysa)
            i += 1
        # END while i < len(path_parts):

        # save changes
        menutree_timestamp = settings.store_tree(menu_as_complex_object)
        d = dict(success=True, data=folder_name, menutree_timestamp=menutree_timestamp)

        return jsonify(d)


def generate_menu(
    load_from_db_flag: str = "true",
    all_nodes_standard_state: str = "closed",
    filter_flag: str = "false",
    menutree_timestamp_from_cookies: datetime = None,
) -> str:
    """Returns the JSON String for the tree menu.

    Args:
        load_from_db_flag (str, optional): the tree is cached to increase the
        speed of the menu generation. If this string (!!) == "true",
        the menu is freshly read from the database.
        If load_from_db_flag == "false" it is read from the cache file
        (if it exists). Defaults to "true".
        all_nodes_standard_state (str, optional): When rereading from the
        database, this string determines if all nodes shall be opened or
        closed. Used by the "expand all" and "collapse all" button. Defaults
        to "closed". filter_flag (str, optional): _description_.
        Defaults to "false".
        menutree_timestamp_from_cookies (datetime, optional): _description_.
        Defaults to None.

    Returns:
        str: tree menu in json format
    """
    try:
        settings.set_option_with_tree(get_info("cern_uid"))
    except Exception:
        pass
    connection = current_app.config["HISTODB"]
    current_actual = False

    # load_from_db_flag == "false" and not False because it is sent by json
    # by javascript!
    # if we are reading it from the file and this file also exists
    if (
        load_from_db_flag == "false"
        and filter_flag == "false"
        and settings.check_tree_cache()
    ):
        menutree_timestamp = settings.get_property("menutree_timestamp")
        if (
            menutree_timestamp
            and menutree_timestamp_from_cookies
            and menutree_timestamp_from_cookies != "undefined"
            and int(menutree_timestamp) == int(menutree_timestamp_from_cookies)
        ):
            menu_as_complex_object = None
            current_actual = True
        else:
            menu_as_complex_object = settings.read_tree()
    # Get it freshly from the database
    else:
        settings.clear_tree_cache()
        menu_as_complex_object = generate_menu_recursion(
            connection.generate_menu_dict(), "", all_nodes_standard_state
        )

        # Save database content for further uses in cache
        menutree_timestamp = settings.store_tree(menu_as_complex_object)
    return json.dumps(
        {
            "current_actual": current_actual,
            "menutree_json": menu_as_complex_object,
            "menutree_timestamp": menutree_timestamp,
        }
    )


def format_entry(
    children: str | None,
    prior_path: str,
    key: str,
    std_state_openend: str,
    std_icon: str,
) -> dict[str, str]:
    """Format entry

    Args:
        children (str | None): children name
        prior_path (str): priori path
        key (str): key
        std_state_openend (str): state
        std_icon (str): icon

    Returns:
        dict[str, str]: entry
    """
    entry = dict()
    # when returning NONE: this key has no children, i.e. is a leaf
    if children is None:
        key = key[:-4]
        entry["text"] = key
        entry["id"] = prior_path + key
        entry["icon"] = "glyphicon glyphicon-file"
    # otherwise it is a folder
    else:
        entry["text"] = key
        entry["id"] = "//F//" + prior_path + key
        entry["icon"] = std_icon
        # and we save the cildren
        entry["children"] = children
        # and consider if all nodes shall be opened or closed
        entry["state"] = {"opened": std_state_openend, "selected": False}
    return entry


def generate_menu_recursion(
    processed_input_dict: dict[str, str],
    prior_path: str = "",
    all_nodes_standard_state: str = "closed",
) -> list:
    """Recursive methode processing the processed database output
    (stored in processed_input_list) to a python structure
    with just needs to be jsonified to have the correct response to
    the ajax menu call.

    Args:
        processed_input_dict (dict[str, str]): After fetching a dict of PAGES
        from the DB, this list has to be prepocessed, which is done in
        histodb.py:generate_menu_dict() and which is automatically called by
        histodb.py:generate_menu_dict(). So you want to call this function with
        generate_menu_recursion

        prior_path (str, optional): Used by the recursion internally to set up
        the right ids, considering the corresponding root elements.
        Defaults to "".

        all_nodes_standard_state (str, optional): When rereading from the
        database, this string determines if all nodes shall be opened or
        closed. Used by the "expand all" and "collapse all" button.
        Defaults to "closed".

    Returns:
        list: processed entries
    """

    output = list()
    # Standard behavior, as normally tree is presented with all folders closed.
    std_icon = "glyphicon glyphicon-folder-close"
    std_state_openend = False
    # if we want instead an all open tree
    if all_nodes_standard_state == "opened":
        std_icon = "glyphicon glyphicon-folder-open"
        std_state_openend = True

    if processed_input_dict is None:
        return None

    # now go through every item in the preprocessed input list
    for key in processed_input_dict:
        value = processed_input_dict[key]
        # and iterate over keys and corresponding values
        children = generate_menu_recursion(
            value, prior_path + key + "/", all_nodes_standard_state
        )

        entry = format_entry(children, prior_path, key, std_state_openend, std_icon)
        # END: for key, value in item.iteritems():

        # we save our generated output
        output.append(entry)
    return output
