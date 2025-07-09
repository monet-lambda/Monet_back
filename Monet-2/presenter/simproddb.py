"""Utility functions to handle simulation production numbers
"""
###############################################################################
# (c) Copyright 2000-2022 CERN for the benefit of the LHCb Collaboration      #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################

import os
import git
import logging
import traceback
import filelock
from yaml import load, Loader
from functools import lru_cache


def only_numeric_strings_length(strings: list[str],
                                length: int = 8) -> list[str]:
    """Given a list of strings, return the ones that are purely numeric and of
    a certain length. Both zero-padded request_id/transformation IDs and
    event_types are length 8.

       Args:
        strings (list[str]): input list of strings
        length (int, optional): length to keep. Defaults to 8.

    Returns:
        list[str]: list of strings
    """
    return list(filter(lambda s: s.isnumeric() and len(s) == length, strings))


class SimProdFiles:
    """Class to handle the repository of simulation production files
    """
    def __init__(self, simproddb_path: str):
        """Initialize class

        Args:
            simproddb_path (str): path of the repository with simulation
            production yaml files
        """
        self.simproddb_path = simproddb_path.rstrip("/")
        self.get_files()

    def get_files(self):
        """Get yaml files from the git repository
        """
        lock = filelock.FileLock("git.lock")
        if lock.is_locked:
            # just wait for the lock to be realeased but no need to update
            # git again
            with lock:
                logging.debug("Waiting for lock to be released")
        else:
            with lock:
                try:
                    repo = git.Repo(self.simproddb_path)
                    repo.remotes.origin.pull()
                    for child in dir(self):
                        if hasattr(child, "clear_cache"):
                            child.clear_cache()
                except BaseException:
                    logging.error("Can't load Sim prod DB:"
                                  f" {traceback.format_exc()}")

        # use assertion as excuse to build the cache on self.sort_by_
        # timestamp now
        assert len(self.get_request_ids()) == len(self.valid_request_ids)

    @lru_cache
    def get_timestamp(self, path: str) -> str:
        """Get the most recent commit timestamp for a given path

        Args:
            path (str): path

        Returns:
            str: timestamp
        """
        repo = git.Repo(self.simproddb_path)
        timestamps = map(lambda path: int(path.strip('"')),
                         repo.git.log('--pretty="%ct"', path).split("\n"))
        most_recent = max(timestamps)
        return most_recent

    @lru_cache
    def sort_by_timestamp(self, paths: list[str]) -> list[str]:
        """Sort a list of files by their timestamp

        Args:
            paths (list[str]): list of files to sort

        Returns:
            list[str]: sorted list
        """
        return sorted(paths, key=self.get_timestamp)

    def request_id_path(self, request_id: int) -> str:
        """Returns the path of a request

        Args:
            request_id (int): request id number

        Returns:
            str: path of the files for this request id
        """
        path = '/'.join([
            self.simproddb_path,
            request_id.rjust(8, '0'),
        ])
        return path

    def event_type_path(self, request_id: int, event_type: int) -> str:
        """Path for a given event type and request id

        Args:
            request_id (int): request id number
            event_type (int): event type number

        Returns:
            str: path of the files for the request and event type
        """
        path = '/'.join([
            self.request_id_path(request_id),
            event_type.rjust(8, '0'),
        ])
        return path

    @property
    def valid_request_ids(self) -> list[str]:
        """Get list of valid requests ids
        """
        return self.get_request_ids(sort_by_timestamp=False)

    def get_request_ids(self, *, sort_by_timestamp=False) -> list[str]:
        """Get list of available request IDs
        Optionally sort by most recent commit timestamp for the corresponding
        directory

        Args:
            sort_by_timestamp (bool, optional): Sort or not the requests by
            timestamp. Defaults to False.

        Returns:
            list[str]: list of request ids
        """
        dir_contents = os.listdir(self.simproddb_path)
        # only take numeric 8-character items (zero-padded request IDs)
        req_ids = only_numeric_strings_length(dir_contents)
        if sort_by_timestamp:
            return self.sort_by_timestamp(frozenset(req_ids))
        return sorted(req_ids)

    def get_event_types(self, request_id: int) -> list[str]:
        """Get list of available event types in this request ID

        Args:
            request_id (int): request id number

        Returns:
            list[str]: list of event types
        """
        dir_contents = os.listdir(self.request_id_path(request_id))
        # only take numeric 8-character items (event types)
        return only_numeric_strings_length(dir_contents)

    def get_filenames(self, request_id: int, event_type: int) -> list[str]:
        """Get list of available YAML files for this request ID/event type
        combination

        Args:
            request_id (int): request id number
            event_type (int): event type number

        Returns:
            list[str]: _description_
        """
        dir_contents = os.listdir(self.event_type_path(request_id, event_type))
        is_yaml = lambda f: f.endswith(".yml") or f.endswith(".yaml")
        return list(filter(is_yaml, dir_contents))

    def get_prod_info(self, request_id: int, event_type: int,
                      filename: str = "1-GAUSSHIST.yml") -> any:
        """Read the desired YAML file for this request ID/event_type
        combination

        Args:
            request_id (int): request id number
            event_type (int): event type number
            filename (str, optional): file name.
            Defaults to "1-GAUSSHIST.yml".

        Returns:
            any: _description_
        """
        path = '/'.join([
            self.event_type_path(request_id, event_type),
            filename,
        ])
        with open(path, 'r') as f:
            metadata = load(f, Loader=Loader)
            return metadata
