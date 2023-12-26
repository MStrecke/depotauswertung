from contextlib import contextmanager
import sqlite3
import re

def local_cursor_wrapper(func):
    """ decorator to create/ensure a cursor from local database

    Advantage:
      - If a function is called multiple times, the parent function can create a db cursor which is reused.
      - If this is not done, the wrapper creates and closes a cursor for this function automatically.

    Notes:
      - The base class MUST have a function `cursor()` to create a cursor.
      - The calling function MUST use the keyword parameter `cursor=...` if it wants to overwrite it.
      - The function MUST use `cursor` as parameter

    @local_cursor_wrapper
    def abcde(self, a, b, cursor=None):
       cursor.execute(....)
       ...

    # use single cursor
    cu=db.cursor()
    self.abcde(...., cursor=cu)
    self.abcde(...., cursor=cu)
    self-abcde(...., cursor=cu)
    cu.close()

    # generate cursor (and destroy) for one call automatically
    self.abcde(....)  or
    self.abcde(...., cursor=None)

    # class must have a function to create a cursor, e.g.:
    def cursor(self):
        return con.cursor()
    """
    def function_wrapper(*args, **kwargs):
        cursor = kwargs.get('cursor')
        if cursor is not None:
            return func(*args, **kwargs)

        self = args[0]
        cu = self.cursor()
        kwargs['cursor'] = cu
        try:
            res = func(*args, **kwargs)
        except:
            raise
        finally:
            cu.close()
        return res

    return function_wrapper

def row2dict(row):
    """ convert result row from dict cursor to a simple dict

    :param row: result from dict cursor execute
    :return: dict with fields or None
    """
    if row is None:
        return None

    dt = {}
    for x in row.keys():
        dt[x] = row[x]
    return dt

def _open_sqlite_filename(dat):
    """ create sqlite connection from data dict

    :param dat: dict with connection parameters
    :return: connection
    """
    con = sqlite3.connect(dat["filename"], detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    con.row_factory = sqlite3.Row
    return con



class DBClass:
    """ Calling convention:

    class SubDBClass(DBClass):
        @classmethod
        def open_my_sqlite_db(cls, filename, moredata, schema=None):
            w = cls.open_sqlite(filename, schema=schema)
            cls.moredata = moredata
            ...
            return w

    ...

    subdb = SubDBClass.open_my_sqlite_db(filename, moredata, schema)

    """
    def __init__(self, driver_dict):
        self.driver_dict = driver_dict
        self.driver = driver_dict["drivername"]
        self.joker = driver_dict["joker"]
        self.replace_joker_flag = self.joker != "?"

        self.con = driver_dict.get("open_connection")
        if self.con is None:
            self._open_connection()

    def connection_valid(self):
        return self.con is not None

    def _open_connection(self):
        openfkt = self.driver_dict.get('open_function')
        openparam = self.driver_dict.get('open_param')
        self.con = openfkt(openparam)

    @classmethod
    def open_sqlite(cls, filename, schema=None):
        """ open an sqlite database file

        :param filename: filename
        :param schema: file name to sql script to create database (or None)
        :return:
        """
        import os
        con = None

        if ((filename == ":memory:") or (not os.path.exists(filename))) and schema is not None:
            fsch = os.path.expanduser(schema)
            assert os.path.exists(fsch), "** schema missing: " + fsch
            with open(fsch, 'r') as fein:
                schemasql = fein.read()
            # print("*** Creating "+filename)
            con = _open_sqlite_filename({'filename': filename})
            cur = con.cursor()
            cur.executescript(schemasql)
            cur.close()
            con.commit()

        return cls({
            "drivername": "sqlite",
            "joker": "?",
            "open_function": _open_sqlite_filename,
            "open_param": {
                "filename": filename
            },
            "open_connection": con
        })

    def cursor(self):
        return self.con.cursor()

    @contextmanager
    def cursor2(self, oldcursor=None):
        if not oldcursor is None:
            return oldcursor
        try:
            f = self.con.cursor()
            yield f
        finally:
            f.close()

    JOKER_REGEX = re.compile("\?(?=([^\"']*[\"'][^\"']*[\"'])*[^\"']*$)")
    def replace_joker(self, query):
        if self.replace_joker_flag:
            return self.JOKER_REGEX.sub(self.joker, query)
        return query

    def close(self):
        if self.con is not None:
            self.con.close()

    @local_cursor_wrapper
    def execute(self, query, params, *, cursor=None, debug=False):
        query = self.replace_joker(query)

        if params is None:
            params = ()

        if debug:
            print("QUERY :", query)
            print("PARAMS:", params)

        try:
            return cursor.execute(query, params)
        except Exception as err:
            print("Execute error:", err)
            print("QUERY :", query)
            print("PARAMS:", params)
            raise

    @local_cursor_wrapper
    def fetchone(self, query, params, *, singleparam=None, debug=False, cursor=None):
        if debug:
            print("QUERY :", query)
            print("PARAMS:", params)
            print("singleparam:", singleparam)

        self.execute(query, params, cursor=cursor)
        res = cursor.fetchone()

        if res is None:
            return None

        if singleparam is None:
            return row2dict(res)
        else:
            return res[singleparam]

    @local_cursor_wrapper
    def fetchall(self, query, params, cursor=None, tolistparam=None, debug=False):
        if debug:
            print("QUERY :", query)
            print("PARAMS:", params)

        self.execute(query, params, cursor=cursor)
        res = cursor.fetchall()

        if tolistparam is None:
            return [ row2dict(x) for x in res ]

        return [x[tolistparam] for x in res]

    def commit(self):
        self.con.commit()

    @local_cursor_wrapper
    def count(self, table, debug=False, cursor=None):
        return self.fetchone("SELECT COUNT(*) FROM %s" % table, params=(), singleparam="COUNT(*)", cursor=cursor, debug=debug)


    def last_insert_id(self, cursor):
        """ return id of last modified row
        :param cursor: cursor with has issued the INSERT
        :note: None after any operation other than INSERT
        """
        return cursor.lastrowid

    @local_cursor_wrapper
    def execute_last_row_id(self, query, param, cursor=cursor):
        self.execute(query, param, cursor=cursor)
        res = self.last_insert_id(cursor)
        return res

