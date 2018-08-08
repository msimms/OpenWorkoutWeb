# Copyright 2017 Michael J Simms
"""Database base classes"""

import logging
import sqlite3


class Database(object):
    """Base class for a database. Encapsulates common functionality."""
    db_file = ""

    def __init__(self, root_dir):
        super(Database, self).__init__()

    def log_error(self, log_str):
        """Writes an error message to the log file."""
        logger = logging.getLogger()
        logger.debug(log_str)

    def is_quoted(self, log_str):
        """Determines if the provided string starts and ends with a double quote."""
        if len(log_str) < 2:
            return False
        return log_str[0] == '\"' and log_str[len(log_str)-1] == '\"'

    def quote_identifier(self, log_str, errors="strict"):
        """Adds quotes to the given string if they do not already exist."""
        if self.is_quoted(log_str):
            return log_str
        encodable = log_str.encode("utf-8", errors).decode("utf-8")
        null_index = encodable.find("\x00")
        if null_index >= 0:
            return ""
        return "\"" + encodable.replace("\"", "\"\"") + "\""


class SqliteDatabase(Database):
    """Abstract Sqlite database implementation."""
    def __init__(self, root_dir):
        Database.__init__(self, root_dir)

    def connect(self):
        """Inherited from the base class and unused."""
        pass

    def execute(self, sql):
        """Executes the specified SQL query."""
        try:
            con = sqlite3.connect(self.db_file)
            with con:
                cur = con.cursor()
                cur.execute(sql)
                return cur.fetchall()
        except:
            self.log_error("Database error:\n\tfile = " + self.db_file + "\n\tsql = " + self.quote_identifier(sql))
        finally:
            if con:
                con.close()
        return None
