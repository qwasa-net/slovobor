import pymysql

import logging


def connect(user, password, database, host=None, unix_socket=None):
    try:
        cnx = pymysql.connect(user=user, password=password, database=database,
                              host=host, unix_socket=unix_socket)
        return cnx
    except Exception as x:
        logging.error("connect error: %s", x)
        raise


def close(cnx):
    try:
        if cnx:
            cnx.close()
    except Exception as _:
        pass


def execute(cnx, query):
    if not cnx:
        logging.error("no connection")
        return False, []

    try:
        cursor = cnx.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        return True, rows
    except Exception as x:
        logging.error("query failed: %s", x)
        raise
