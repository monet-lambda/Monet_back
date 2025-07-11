"""Data quality daabase (DQDB) interface

Function to setup and access the DQDB via MySQL client
"""


import logging
import os
import sqlite3
from pathlib import Path

import mysql.connector
from flask import current_app

from interfaces.dirac import (
    get_dq_extendedflags_from_bkk,
    get_dq_flag_from_bkk,
    set_dq_extendedflags_from_bkk,
    set_dq_flag_in_bkk,
)

DIR_PATH = Path(os.path.dirname(os.path.realpath(__file__)))


def create_monet_user() -> bool:
    """Create the Monet user in the DQDB

    Returns:
        bool: False if there was an error, True otherwise
    """
    try:
        print("!!!!!!!!!", current_app.config.get("DQDB_ADMIN_USER", "admin"), current_app.config.get("DQDB_ADMIN_PASSWORD", ""))
        cnx = mysql.connector.connect(
            user=current_app.config.get("DQDB_ADMIN_USER", "admin"),
            password=current_app.config.get("DQDB_ADMIN_PASSWORD", ""),
            host=current_app.config.get("DQDB_HOST", ""),
            port=current_app.config.get("DQDB_PORT", ""),
        )
        create_db = (
            "CREATE DATABASE IF NOT EXISTS "
            f"{current_app.config.get('DQDB_DATABASE', 'dqdb')}"
        )
        create_user = (
            "CREATE USER IF NOT EXISTS "
            f"'{current_app.config.get('DQDB_USER', 'monet')}'@'%' "
            f"IDENTIFIED BY '{current_app.config.get('DQDB_PASSWORD', '')}'"
        )
        set_permissions = (
            f"GRANT ALL "
            f"ON {current_app.config.get('DQDB_DATABASE', 'dqdb')}.* "
            f"TO '{current_app.config.get('DQDB_USER', 'monet')}'@'%'"
        )
        cursor = cnx.cursor()
        cursor.execute(create_db)
        cursor.execute(create_user)
        cursor.execute(set_permissions)
        cursor.close()
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(err)
        cursor.close()
        cnx.close()
        return False
    else:
        cnx.close()
    return True


def create_dqdb_tables() -> bool:
    """Create the database tables in the DQDB

    Returns:
        bool: False if there was an error, True otherwise
    """
    try:
        cnx = mysql.connector.connect(
            user=current_app.config.get("DQDB_USER", "monet"),
            password=current_app.config.get("DQDB_PASSWORD", ""),
            host=current_app.config.get("DQDB_HOST", ""),
            port=current_app.config.get("DQDB_PORT", ""),
            database=current_app.config.get("DQDB_DATABASE", "dqdb"),
        )
        cursor = cnx.cursor()

        TABLES = {}
        TABLES["runs"] = (
            "CREATE TABLE IF NOT EXISTS `runs` ("
            "  `run_number` MEDIUMINT(6) UNSIGNED NOT NULL,"
            "  `global_flag` VARCHAR(9) NOT NULL DEFAULT 'UNCHECKED',"
            " PRIMARY KEY (`run_number`)"
            ")"
        )
        TABLES["systems"] = (
            "CREATE TABLE IF NOT EXISTS `systems` ("
            "  `systemID` TINYINT UNSIGNED NOT NULL AUTO_INCREMENT,"
            "  `name` VARCHAR(20) NOT NULL,"
            " PRIMARY KEY (`systemID`),"
            " UNIQUE (`name`)"
            ")"
        )
        TABLES["flags"] = (
            "CREATE TABLE IF NOT EXISTS `flags` ("
            "  `run_number` MEDIUMINT(6) UNSIGNED NOT NULL,"
            "  `systemID` TINYINT UNSIGNED NOT NULL,"
            "  `flag` VARCHAR(9) NOT NULL DEFAULT 'UNCHECKED',"
            " PRIMARY KEY (`run_number`, `systemID`),"
            " FOREIGN KEY (`run_number`) REFERENCES `runs`(`run_number`)"
            " ON DELETE CASCADE ON UPDATE CASCADE,"
            " FOREIGN KEY (`systemID`) REFERENCES `systems`(`systemID`)"
            " ON DELETE CASCADE ON UPDATE CASCADE"
            ")"
        )
        for table_name in TABLES:
            table_description = TABLES[table_name]
            cursor.execute(table_description)
        cursor.close()
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(err)
        return False
    else:
        cnx.close()
    return True


def transfer_monet_dqdb() -> bool:
    """Transfer the Monet local dqlite DQDB to the central SQL one

    Returns:
        bool: False if an error occured, True otherwise
    """
    with sqlite3.connect(DIR_PATH / "database/dqdb.db") as dqdb:
        cur = dqdb.cursor()
        cur.execute("SELECT run_number, flag FROM dq")
        result = cur.fetchall()

        try:
            cnx = mysql.connector.connect(
                user=current_app.config.get("DQDB_USER", "monet"),
                password=current_app.config.get("DQDB_PASSWORD", ""),
                host=current_app.config.get("DQDB_HOST", ""),
                port=current_app.config.get("DQDB_PORT", ""),
                database=current_app.config.get("DQDB_DATABASE", "dqdb"),
            )
            cursor = cnx.cursor()
            insert_data = "INSERT INTO runs (run_number, global_flag) VALUES (%s, %s)"
            for i in result:
                if i[0] > 999999:
                    continue
                data_dq = (i[0], i[1])
                cursor.execute(insert_data, data_dq)
            cnx.commit()
            cursor.close()
            cnx.close()
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
                logging.error("Something is wrong with your credentials")
            elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                logging.error("Database does not exist")
            else:
                logging.error(err)
            cursor.close()
            cnx.close()
            return False
        else:
            cnx.close()
    return True


def _get_flag_from_db(run_number: int) -> tuple[str, list[str]]:
    """Get DQ flag from DQDB

    Args:
        run_number (int): run number

    Returns:
        tuple[str, list[str]]: DQ dflag ("UNCHECKED", "OK", "BAD" or "CONDITIONAL") and list
            of system flags ("SMOG2")
    """
    the_flag = "UNCHECKED"
    system_flags = []
    try:
        cnx = mysql.connector.connect(
            user=current_app.config.get("DQDB_USER", "monet"),
            password=current_app.config.get("DQDB_PASSWORD", ""),
            host=current_app.config.get("DQDB_HOST", ""),
            port=current_app.config.get("DQDB_PORT", ""),
            database=current_app.config.get("DQDB_DATABASE", "dqdb"),
        )
        cursor = cnx.cursor()
        select_data = "SELECT global_flag FROM runs WHERE run_number = %s"
        cursor.execute(select_data, (run_number,))
        for flag in cursor:
            the_flag = flag[0]
        select_data = (
            "SELECT flags.flag, systems.name FROM flags "
            "JOIN systems "
            "ON flags.systemID = systems.systemID "
            "WHERE flags.run_number = %s"
        )
        cursor.execute(select_data, (run_number,))
        for flag in cursor:
            if flag[0] == "OK":
                system_flags.append(flag[1])
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(err)
        cursor.close()
        cnx.close()
        return "UNCHECKED", []
    else:
        cnx.close()
    return the_flag, sorted(system_flags)


def get_dq_flag_range_from_dqdb(
    run_numbers: list[int],
) -> dict[int, tuple[str, list[str]]]:
    """Get DQ flag from DQDB for a range of runs

    Args:
        run_numbers (list[int]): list of run numbers

    Returns:
        dict[str,tuple[str, list[str]]]: dictionary of DQ dflag ("UNCHECKED", "OK", "BAD" or "CONDITIONAL") and list
            of system flags ("SMOG2")
    """
    run_numbers.sort()
    result = {}
    result_ex = {}
    try:
        cnx = mysql.connector.connect(
            user=current_app.config.get("DQDB_USER", "monet"),
            password=current_app.config.get("DQDB_PASSWORD", ""),
            host=current_app.config.get("DQDB_HOST", ""),
            port=current_app.config.get("DQDB_PORT", ""),
            database=current_app.config.get("DQDB_DATABASE", "dqdb"),
        )
        cursor = cnx.cursor()
        select_data = "SELECT run_number, global_flag FROM runs WHERE run_number >= %s AND run_number <= %s"
        cursor.execute(
            select_data,
            (
                run_numbers[0],
                run_numbers[-1],
            ),
        )

        for flag in cursor:
            result[flag[0]] = flag[1]

        for r in result:
            select_data = (
                "SELECT flags.flag, systems.name FROM flags "
                "JOIN systems "
                "ON flags.systemID = systems.systemID "
                "WHERE flags.run_number = %s"
            )
            cursor.execute(select_data, (r,))
            system_flags = []
            for flag_ex in cursor:
                if flag_ex[0] == "OK":
                    system_flags.append(flag_ex[1])
            result_ex[r] = (result[r], system_flags)
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(err)
        cursor.close()
        cnx.close()
        return {}
    else:
        cnx.close()
    return result_ex


def get_list_systems() -> list[str]:
    """Returns the list of systems defined in the DQDB

    Returns:
        list[str]: list of systems
    """
    the_list = []
    try:
        cnx = mysql.connector.connect(
            user=current_app.config.get("DQDB_USER", "monet"),
            password=current_app.config.get("DQDB_PASSWORD", ""),
            host=current_app.config.get("DQDB_HOST", ""),
            port=current_app.config.get("DQDB_PORT", ""),
            database=current_app.config.get("DQDB_DATABASE", "dqdb"),
        )
        cursor = cnx.cursor()
        select_data = "SELECT name FROM systems"
        cursor.execute(select_data)
        for n in cursor:
            the_list.append(n[0])
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(err)
        cursor.close()
        cnx.close()
        return []
    else:
        cnx.close()
    return the_list


def _set_flag_in_db(run_number: int, flag: str, extra_flags: list[str] = []) -> bool:
    """Set flag in the DQDB

    Args:
        run_number (int): run number
        flag (str): flag to set ("UNCHECKED", "OK", "BAD" or "CONDITIONAL")
        extra_flags (list[str], optional): list of systems for
            extra DQ flags ("SMOG2"). Defaults to [].

    Returns:
        bool: False in case of error, True otherwise
    """
    try:
        cnx = mysql.connector.connect(
            user=current_app.config.get("DQDB_USER", "monet"),
            password=current_app.config.get("DQDB_PASSWORD", ""),
            host=current_app.config.get("DQDB_HOST", ""),
            port=current_app.config.get("DQDB_PORT", ""),
            database=current_app.config.get("DQDB_DATABASE", "dqdb"),
        )
        cursor = cnx.cursor()
        insert_data = "REPLACE INTO runs (run_number, global_flag) VALUES (%s, %s)"
        data_dq = (run_number, flag)
        cursor.execute(insert_data, data_dq)
        cnx.commit()

        for k in extra_flags:
            # Get system ID
            system_id = -1
            select_data = "SELECT systemID FROM systems WHERE name = %s"
            cursor.execute(select_data, (k,))
            for n in cursor:
                system_id = n[0]
                break
            # Insert data
            insert_data = (
                "REPLACE INTO flags (run_number, systemID, flag) VALUES (%s, %s, %s)"
            )
            data_dq = (run_number, system_id, "OK")
            cursor.execute(insert_data, data_dq)

        cnx.commit()
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(err)
        cursor.close()
        cnx.close()
        return False
    else:
        cnx.close()
    return True


def set_dq_flag_range_from_dqdb(run_numbers: list[int], flag: str) -> bool:
    """Set DQ flag from DQDB for a range of runs

    Args:
        run_numbers (list[int]): list of run numbers
        flag (str): flag

    Returns:
        True is success, False otherwise
    """
    for r in run_numbers:
        current_flag, extra_flags = _get_flag_from_db(r)
        if not _set_flag_in_db(r, flag, extra_flags):
            return False

    return True


def _set_flag_extra_in_db(run_number: int, extra_flags: list[str]) -> bool:
    """Set flag in the DQDB

    Args:
        run_number (int): run number
        extra_flags (list[str]): list of systems for
            extra DQ flags ("SMOG2")..

    Returns:
        bool: False in case of error, True otherwise
    """
    try:
        cnx = mysql.connector.connect(
            user=current_app.config.get("DQDB_USER", "monet"),
            password=current_app.config.get("DQDB_PASSWORD", ""),
            host=current_app.config.get("DQDB_HOST", ""),
            port=current_app.config.get("DQDB_PORT", ""),
            database=current_app.config.get("DQDB_DATABASE", "dqdb"),
        )
        cursor = cnx.cursor()

        for k in extra_flags:
            # Get system ID
            system_id = -1
            select_data = "SELECT systemID FROM systems WHERE name = %s"
            cursor.execute(select_data, (k,))
            for n in cursor:
                system_id = n[0]
                break
            # Insert data
            insert_data = (
                "REPLACE INTO flags (run_number, systemID, flag) VALUES (%s, %s, %s)"
            )
            data_dq = (run_number, system_id, "OK")
            cursor.execute(insert_data, data_dq)

        cnx.commit()
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(err)
        cursor.close()
        cnx.close()
        return False
    else:
        cnx.close()
    return True


def set_dq_flag_extra_range_from_dqdb(
    run_numbers: list[int], extra_flags: list[str]
) -> bool:
    """Set DQ extra flag from DQDB for a range of runs

    Args:
        run_numbers (list[int]): list of run numbers
        extra_flags (list[str]): list of extra flags

    Returns:
        True is success, False otherwise
    """
    for r in run_numbers:
        if not _set_flag_extra_in_db(r, extra_flags):
            return False

    return True


def create_system(name: str) -> bool:
    """Create system in the DQ databse

    Args:
        name (str): name of the system

    Returns:
        bool: False if an error occured, True otherwise
    """
    try:
        cnx = mysql.connector.connect(
            user=current_app.config.get("DQDB_USER", "monet"),
            password=current_app.config.get("DQDB_PASSWORD", ""),
            host=current_app.config.get("DQDB_HOST", ""),
            port=current_app.config.get("DQDB_PORT", ""),
            database=current_app.config.get("DQDB_DATABASE", "dqdb"),
        )
        cursor = cnx.cursor()
        insert_data = "INSERT INTO systems (name) VALUES (%s)"
        data_dq = (name,)
        cursor.execute(insert_data, data_dq)
        cnx.commit()
        cursor.close()
        cnx.close()
    except mysql.connector.Error as err:
        if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
            logging.error("Something is wrong with your user name or password")
        elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
            logging.error("Database does not exist")
        else:
            logging.error(err)
        cursor.close()
        cnx.close()
        return False
    else:
        cnx.close()
    return True


def get_dq_flag(run_number: int) -> tuple[str, dict[str, str]]:
    """Get DQ flag from Dirac and DQ database

    Args:
        run_number (int): Run number

    Returns:
        tuple[str, dict[str, str]]: global flag ("UNCHECKED", "OK", "BAD" or "CONDITIONAL")
            and dictionnary with system extra flags
    """
    try:
        run_number_i = int(run_number)
        if run_number_i <= 0:
            return "UNCHECKED", {}
    except ValueError:
        return "UNCHECKED", {}
    flag, system_flags = _get_flag_from_db(run_number)
    # Don't rely on the existing DB entry if the flag is UNCHECKED as this is
    # likely to change
    if flag is None or flag == "UNCHECKED":
        try:
            bkk_flag = get_dq_flag_from_bkk(run_number)
            bkk_system_flags = get_dq_extendedflags_from_bkk(run_number)
        except Exception:
            bkk_flag = None
            bkk_system_flags = []
        # Update flag in DB if needed
        if flag != bkk_flag:
            _set_flag_in_db(run_number, bkk_flag, bkk_system_flags)
            flag = bkk_flag
            system_flags = bkk_system_flags
        if system_flags != bkk_system_flags:
            _set_flag_in_db(run_number, bkk_flag, bkk_system_flags)
            flag = bkk_flag
            system_flags = bkk_system_flags
    result = {}
    for i in system_flags:
        result[i] = "OK"
    return flag, result


def set_dq_flag(run_number: int, flag: str, extra_flags: list[str] = []) -> bool:
    """Set DQ flag in Dirac and DQDB

    Args:
        run_number (int): run number
        flag (str): global flag ("UNCHECKED", "OK", "BAD" or "CONDITIONAL")
        extra_flags (list[str], optional): List of systems for extra DQ flag
            ("SMOG2"). Defaults to [].

    Returns:
        bool: False if an error occured, True otherwise
    """
    try:
        run_number_i = int(run_number)
        if run_number_i <= 0:
            return False
    except ValueError:
        return False
    if flag == "":
        logging.warning(f"Tried to set empty global_flag for run {run_number}")
        return False
    ret = set_dq_flag_in_bkk(run_number, flag)
    if ret:
        ret = set_dq_extendedflags_from_bkk(run_number, sorted(extra_flags))
        if ret:
            _set_flag_in_db(run_number, flag, sorted(extra_flags))
    return ret
