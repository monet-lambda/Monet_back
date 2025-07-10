"""Interface to the logbook"""


import base64
import logging
import os
import re
import tempfile
from urllib import parse

from flask import current_app

from presenter.blueprints._auth import get_info

id_regex = re.compile(r"ID\=(\d+)")


def send_to_elog(
    logbook: str,
    author: str,
    system: str,
    subject: str,
    run_number: str,
    text: str,
    level: str = "",
    attachements: list[str] = [],
) -> bool:
    """Send message to ELOG

    Args:
        logbook (str): logbook name
        author (str): name of the author
        system (str): name of the system
        subject (str): subject
        run_number (str): run number
        text (str): description of the entry
        level (str, optional): level. Defaults to ''.
        attachements (list[str], optional): list of attachements.
        Defaults to [].

    Returns:
        bool: True if message was correctly sent, False if there was an error
    """

    def shellquote(s):
        return s  # can be used to filtrate user input

    system = system.rstrip()

    args = [
        "-l",
        shellquote(logbook),
        "-a",
        "Author={}".format(shellquote(author)),
        "-a",
        "System={}".format(shellquote(system)),
        "-a",
        "Subject={}".format(shellquote(subject)),
        "-a",
        "Run={}".format(shellquote(run_number)),
        "_timeout=30",
    ]

    if level != "":
        args.append("-a")
        args.append("Level={}".format(shellquote(level)))

    for path in attachements:
        args.append("-f")
        args.append(path)

    args.append(shellquote(text))
    return current_app.config["ELOG_CMD"](*args)


def construct_elog_link(cmd_stdout: str, logbook: str) -> str:
    """Returns the logbook link for the entry

    Args:
        cmd_stdout (str): output of the elog command
        logbook (str): name of the logbook

    Returns:
        str: link to the logbook entry
    """
    logbook = parse.quote(logbook)

    m = id_regex.search(cmd_stdout)
    if m:
        result = f"https://lblogbook.cern.ch/{logbook}/{m.group(1)}"
    else:
        result = cmd_stdout

    return result


def save_images_to_temp_files(imageuri_list: list[str]) -> list[str]:
    """Save images to temporary files

    Args:
        imageuri_list (list[str]): list of image

    Returns:
        list[str]: list of saved temporary image files
    """
    ret = []

    for datauri in imageuri_list:
        imgstr = re.search(r"base64,(.*)", datauri).group(1)
        temp = tempfile.NamedTemporaryFile(
            mode="wb", suffix=".png", prefix="monet_", dir="/tmp", delete=False
        )
        temp.write(base64.b64decode(imgstr))
        temp.close()
        ret.append(temp.name)

    return ret


def cleanup_image_pathes(image_path_list: list[str]) -> None:
    """Delete temporary image files

    Args:
        image_path_list (list[str]): list of files to delete
    """
    for path in image_path_list:
        try:
            os.remove(path)
        except Exception:
            logging.error(f"Could not remove file {path}")


def elog_flag_submission(run_number: int, flag_value: str, user_comment: str) -> bool:
    """Send comment to ELOG when flagging a run

    Args:
        run_number (int): run number
        flag_value (str): global flag
        user_comment (str): comment

    Returns:
        bool: True if OK, False if problem
    """
    subject = f"Run {run_number} flagged as {flag_value}"
    body = {
        "OK": "Run flagged for all needed processing passes",
        "BAD": "Run flagged BAD",
        "CONDITIONAL": "Run flagged CONDITIONAL",
    }[flag_value]

    if user_comment != "":
        body += "\nUser comment: " + user_comment

    return send_to_elog(
        logbook="Data Quality",
        author=get_info("name"),
        system="Flags",
        subject=subject,
        run_number=run_number,
        text=body,
    )
