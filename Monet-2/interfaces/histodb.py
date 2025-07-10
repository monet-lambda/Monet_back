"""Functions to handle the yaml histogram database, and display them
in the page tree in Monet
"""


import logging
import os
import traceback
from collections import OrderedDict

import filelock
import git
from yaml import Loader, load


def sort_menu_dict(menu_dict: dict) -> OrderedDict:
    """Sort the dictionnary of pages

    Args:
        menu_dict (dict): unsorted dictionnary with pages

    Returns:
        OrderedDict: ordered dictionnary of pages
    """
    res = OrderedDict()
    for k, v in sorted(menu_dict.items()):
        if isinstance(v, dict):
            res[k] = sort_menu_dict(v)
        else:
            res[k] = v
    return res


class HistoFiles:
    """Class to handle the histogram database"""

    def __init__(self, histodb_path: str):
        """Initialize class

        Args:
            histodb_path (str): path of the histgram db repository
        """
        if not histodb_path.endswith("/"):
            histodb_path = histodb_path + "/"
        self.histodb_path = histodb_path

    def get_files(self) -> None:
        """Read histo db files from the repository"""
        # simple lock mechanism for git pull
        lock = filelock.FileLock("git.lock")
        if lock.is_locked:
            # just wait for the lock to be realeased but no need to
            # update git again
            with lock:
                return

        with lock:
            try:
                repo = git.Repo(self.histodb_path)
                repo.remotes.origin.pull()
            except BaseException:
                logging.error(f"Cant load histoYML: {traceback.format_exc()}")

    def generate_menu_dict(self) -> OrderedDict:
        """(Re)generate the tree with pages

        Returns:
            OrderedDict: New (re)generated dictionnary with pages
        """
        tree = {}
        for path, _, files in os.walk(self.histodb_path[:-1]):
            path_e = path.replace(self.histodb_path, "/histoyml/", 1)
            path_list = path_e.split("/")
            buf_dict = tree
            for dir in path_list:
                if dir not in buf_dict:
                    buf_dict[dir] = {}
                buf_dict = buf_dict[dir]
            for filename in files:
                if filename.endswith(".yml"):
                    buf_dict[filename] = None
        tree = tree[""]["histoyml"]

        to_clean_up = []
        for first_level_node in tree:
            if tree[first_level_node] is None:
                to_clean_up.append(first_level_node)
        for first_level_page in to_clean_up:
            del tree[first_level_page]
        del [tree[".git"]]
        return sort_menu_dict(tree)

    def get_histos_in_path(self, path: str) -> tuple[list[str], str]:
        """Get list of histograms in file

        Args:
            path (str): file name, relative to the histogram db repository,
            without the yml extension

        Raises:
            RuntimeError: if path does not exist anymore

        Returns:
            tuple[list[str], str]: list of histograms and page documentation
        """
        result = []
        try:
            with open(self.histodb_path + path + ".yml", "r") as f:
                page = load(f, Loader=Loader)
                page_doc = page.get("pagedoc", "")
                for histo in page["histograms"]:
                    if histo.get("badrun_file", None):
                        list_badruns = []
                        with open(f"/hist/Reference/{histo['badrun_file']}") as f:
                            list_badruns = f.read().splitlines()
                        histo["badrun_file"] = list_badruns
                    result.append(histo)
        except Exception:
            raise RuntimeError(
                "YML file does not exist anymore, try to click"
                " on the Reload Tree button"
            )
        return result, page_doc
