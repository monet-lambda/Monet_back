"""Interface with Dirac for Data quality bookkeeping database"""


import logging
import subprocess
from datetime import datetime

from presenter.cache import cache


def dirac_call(command: str) -> str:
    """Call Dirac command via command line

    Args:
        command (str): command to execute in the Dirac environment

    Returns:
        str: output of the Dirac command
    """
    exec_command = " ".join(str(cmd) for cmd in command)
    logging.warning(
        "Execute at "
        + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        + " "
        + exec_command
        + " -- "
    )
    try:
        process = subprocess.run( command, capture_output=True, timeout=30 )
        output = process.stdout.decode('UTF-8')
        logging.debug(output)
    except (subprocess.CalledProcessError):
        logging.error("Error calling Dirac")
        logging.error(
            "Execute at "
            + datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            + " "
            + exec_command
            + " -- "
        )
        return ""
    return output


@cache.memoize(timeout=300)
def get_dq_flag_range_from_bkk(runs: list[int]) -> dict[str, tuple[str, list[str]]]:
    """Get DQ global flag from bookkeeping via Dirac for a list of runs

    Args:
        run (list[int]): list of run numbers

    Returns:
        dict[str,tuple[str, list[str]]]: dictionary of global flag ("UNCHECKED", "OK", "BAD" or "CONDITIONAL") and extra flags
    """
    list_of_runs = " ".join([str(run) for run in runs])
    output = dirac_call(["dirac-bookkeeping-getdataquality-runs", list_of_runs])
    result = {}
    # Check for full stream 90000000
    for line in output.split("\n"):
        if "90000000" in line:
            result[line.split()[0]] = line.split()[-1]
    # If not check stream 90700000 (heavy ions for example)
    for line in output.split("\n"):
        if "90700000" in line:
            result[line.split()[0]] = line.split()[-1]
    output = dirac_call(["dirac-bookkeeping-getextendeddqok-runs", list_of_runs])
    result_ex = {}
    for r in runs:
        for line in output.split("\n"):
            if str(r) in line:
                fields = line.split()
                if len(fields) == 1:
                    if str(r) in result:
                        result_ex[str(r)] = (result[str(r)], [""])
                    continue
                ext_flags = fields[1]
                result_ex[str(r)] = (result[str(r)], sorted(ext_flags.split(",")))
    return result_ex


@cache.memoize(timeout=300)
def get_dq_flag_from_bkk(run: int) -> str:
    """Get DQ global flag from bookkeeping via Dirac

    Args:
        run (int): run number

    Returns:
        str: global flag ("UNCHECKED", "OK", "BAD" or "CONDITIONAL")
    """
    output = dirac_call(["dirac-bookkeeping-getdataquality-runs", str(run)])
    # Check for full stream 90000000
    for line in output.split("\n"):
        if "90000000" in line:
            return line.split()[-1]
    # If not check stream 90700000 (heavy ions for example)
    for line in output.split("\n"):
        if "90700000" in line:
            return line.split()[-1]
    return "UNCHECKED"


@cache.memoize(timeout=300)
def get_dq_extendedflags_from_bkk(run: int) -> list[str]:
    """Get DQ extended flags from the bookkeeping with Dirac

    Args:
        run (int): run number

    Returns:
        list[str]: list of system with extra flags set as OK
    """
    output = dirac_call(["dirac-bookkeeping-getextendeddqok-runs", str(run)])
    # Check for full stream 90000000
    for line in output.split("\n"):
        if str(run) in line:
            fields = line.split()
            if len(fields) == 1:
                return []
            ext_flags = fields[1]
            return sorted(ext_flags.split(","))
    return []


def set_dq_flag_in_bkk(run: int, flag: str) -> int | None:
    """Set DQ global flag in bookkeeping via Dirac

    Args:
        run (int): run number
        flag (str): global flag ("OK", "BAD", "CONDITIONAL" or "UNCHECKED")

    Raises:
        NameError: if an error occurs with Dirac

    Returns:
        int | None: number of files flagged (None if an error occured)
    """
    cache.delete_memoized(get_dq_flag_from_bkk, run)
    try:
        output = dirac_call(["dirac-bookkeeping-setdataquality-run", str(run), flag])
    except BrokenPipeError:
        logging.error(f"Error when flaggin run {run}")
        return None
    for line in output.split("\n"):
        if "ERROR" in line:
            raise NameError("Global flag: " + line.split("ERROR:")[1])
    bkk_flag = get_dq_flag_from_bkk(run)
    if flag == bkk_flag:
        # Return number of flagged files
        return len(output.split("\n")) - 1
    logging.error(f"Bad DQ flag {flag} received")
    return None


def set_dq_flag_range_in_bkk(runs: list[int], flag: str) -> int | None:
    """Set DQ global flag in bookkeeping via Dirac for a list of runs

    Args:
        runs (list[int]): list of run numbers
        flag (str): global flag ("OK", "BAD" or "CONDITIONAL")

    Raises:
        NameError: if an error occurs with Dirac

    Returns:
        int | None: number of files flagged (None if an error occured)
    """
    nFiles = 0
    for r in runs:
        cache.delete_memoized(get_dq_flag_from_bkk, r)
        try:
            output = dirac_call(["dirac-bookkeeping-setdataquality-run", str(r), flag])
        except BrokenPipeError:
            logging.error(f"Error when flaggin run {r}")
            return None
        for line in output.split("\n"):
            if "ERROR" in line:
                raise NameError("Global flag: " + line.split("ERROR:")[1])
        bkk_flag = get_dq_flag_from_bkk(r)
        if flag == bkk_flag:
            # Return number of flagged files
            nFiles = nFiles + len(output.split("\n")) - 1
        else:
            logging.error(f"Bad DQ flag {flag} received")
            return None
    return nFiles


def set_dq_extendedflags_from_bkk(run: int, ext_flags: list[str]) -> int | None:
    """Set extended DQ flags in bookkeeping with Dirac

    Args:
        run (int): run number
        ext_flags (list[str]): list of systems to set "OK" extra flags

    Raises:
        NameError: in case of error with Dirac

    Returns:
        int | None: number of files flagged or None in case of error
    """
    ext_flags.sort()
    cache.delete_memoized(get_dq_extendedflags_from_bkk, run)
    flags_string = ""
    for s in ext_flags:
        if flags_string == "":
            flags_string = s
        else:
            flags_string += "," + s
    if flags_string == "":
        output = dirac_call(["dirac-bookkeeping-setextendeddqok-run", str(run)])
    else:
        output = dirac_call(["dirac-bookkeeping-setextendeddqok-run", str(run), flags_string])
    for line in output.split("\n"):
        if "ERROR" in line:
            raise NameError("Extended flags :" + line.split("ERROR:")[1])
    bkk_flags = get_dq_extendedflags_from_bkk(run)
    if ext_flags == bkk_flags:
        # Return number of flagged files
        return len(output.split("\n")) - 1
    logging.error("Bad DQ extended flags received")
    return None


def set_dq_flag_extra_range_in_bkk(runs: list[int], ext_flags: list[str]) -> int | None:
    """Set DQ extra flag in bookkeeping via Dirac for a list of runs

    Args:
        runs (list[int]): list of run numbers
        ext_flags (list[str]): list of extra flags  ("SMOG2")

    Raises:
        NameError: if an error occurs with Dirac

    Returns:
        int | None: number of files flagged (None if an error occured)
    """
    nFiles = 0
    ext_flags.sort()
    flags_string = ""
    for s in ext_flags:
        if flags_string == "":
            flags_string = s
        else:
            flags_string += "," + s

    for r in runs:
        cache.delete_memoized(get_dq_extendedflags_from_bkk, r)
        if flags_string == "":
            output = dirac_call(["dirac-bookkeeping-setextendeddqok-run", str(r), flags_string])
        else:
            output = dirac_call(["dirac-bookkeeping-setextendeddqok-run", str(r)])
        for line in output.split("\n"):
            if "ERROR" in line:
                raise NameError("Extended flags :" + line.split("ERROR:")[1])
        bkk_flags = get_dq_extendedflags_from_bkk(r)
        if ext_flags == bkk_flags:
            # Return number of flagged files
            nFiles = nFiles + len(output.split("\n")) - 1
        else:
            logging.error("Bad DQ extended flags received")
            return False
    return nFiles
