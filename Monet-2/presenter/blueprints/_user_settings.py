"""Handle user settings (server side cookies)"""

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
import os.path
import pickle
import time
from datetime import datetime, timedelta

import filelock
from flask import current_app

import interfaces.rundb


# Class implement server cookies store
class UserSettings:
    """Class to implement server cookies store"""

    def __init__(self):
        """Initialize class"""
        self.options_file_name = None
        self.options_tree_file_name = None

    def set_options_file(self, uid: str) -> None:
        """Set name of option file to use

        Args:
            uid (str): user id
        """
        self.options_file_name = f"sessions/{uid}options.tcl"

    def set_option_with_tree(self, uid: str) -> None:
        """Set name of tree option file to use

        Args:
            uid (str): user id
        """
        self.set_options_file(uid)
        self.options_tree_file_name = f"sessions/{uid}Tree.tcl"

    @staticmethod
    def get_default_value(property_name: str) -> any:
        """Get default value for a given property

        Args:
            property_name (str): name of the property

        Returns:
            any: default value
        """
        if property_name.startswith("run_number:"):
            if property_name.endswith("simulation"):
                return current_app.config["SIMPRODDB"].get_request_ids()[-1]
            else:
                return interfaces.rundb.get_latest_run_number()
        if property_name == "run_number_from:trends":
            return 100000
        if property_name == "run_number_to:trends":
            return 999999
        if property_name == "reference_state":
            return "deactivated"
        if property_name == "interval_begin":
            return (datetime.now() - timedelta(minutes=30)).strftime("%m/%d/%Y %H:%M")
        if property_name == "displayfills_state":
            return "deactivated"
        if property_name == "interval_start":
            return "00:30"
        else:
            return None

    def init_file(self) -> bool:
        """Init option file

        Returns:
            bool: True if success, False otherwise
        """
        if not (
            os.path.exists(self.options_file_name)
            and os.path.isfile(self.options_file_name)
        ):
            options = dict()
            options["reference_state"] = "deactivated"
            options["displayfills_state"] = "deactivated"

            options_file = open(self.options_file_name, "wb")
            pickle.dump(options, options_file)
            options_file.close()
            return True
        return False

    def check_tree_cache(self) -> bool:
        """Check if tree cache file exists

        Returns:
            bool: True if the file exists, False otherwise
        """
        return os.path.isfile(self.options_tree_file_name)

    def set_property(self, property_name: str, value: any) -> bool:
        """Set property in user option file

        Args:
            property_name (str): name of the property
            value (any): value to store

        Returns:
            bool: True if success, False otherwise
        """
        if not self.options_file_name:
            logging.error("Options file name not set")
            return False
        with filelock.FileLock(self.options_file_name + ".lock"):
            self.init_file()
            options_file = open(self.options_file_name, "rb")
            try:
                options = pickle.load(options_file)
            except EOFError:
                options = {}
            options_file.close()

            options[property_name] = value
            options_file = open(self.options_file_name, "wb")
            result = pickle.dump(options, options_file)
            options_file.close()

        return result

    def get_property(self, property_name: str) -> any:
        """Get property in user option file

        Args:
            property_name (str): name of property

        Returns:
            any: value
        """
        self.init_file()
        options_file = open(self.options_file_name, "rb")
        options = pickle.load(options_file)
        options_file.close()
        if property_name in options and options[property_name] is not None:
            return options[property_name]
        else:
            return UserSettings.get_default_value(property_name)

    def store_tree(self, my_tree: list[str]) -> float:
        """Store tree in tree option file

        Args:
            my_tree (list[str]): tree

        Returns:
            float: timestamp
        """
        with filelock.FileLock(self.options_tree_file_name + ".lock"):
            with open(self.options_tree_file_name, "wb") as tree_f:
                pickle.dump(my_tree, tree_f)
                menutree_timestamp = time.mktime(datetime.now().timetuple())
                self.set_property("menutree_timestamp", menutree_timestamp)
                return menutree_timestamp

    def read_tree(self) -> None | list[str]:
        """Read tree from option file

        Returns:
            None | list[str]: tree
        """
        if not self.check_tree_cache():
            return None

        with filelock.FileLock(self.options_tree_file_name + ".lock"):
            with open(self.options_tree_file_name, "rb") as tree_f:
                user_tree = pickle.load(tree_f)
            return user_tree

    def clear_tree_cache(self) -> None:
        """Clear tree cache files"""
        os.system("rm -f " + self.options_tree_file_name)
        os.system("rm -f " + self.options_tree_file_name + ".lock")

    def clear_options_cache(self) -> None:
        """Clear option files"""
        os.system("rm -f " + self.options_file_name)
        os.system("rm -f " + self.options_file_name + ".lock")
