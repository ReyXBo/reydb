# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database connection methods.
"""


from __future__ import annotations
from typing import Any, List, Dict, Tuple, Union, Optional, Literal, Iterable, Generator, NoReturn, Type, overload
from types import TracebackType
from re import findall
from urllib.parse import quote as urllib_quote
from sqlalchemy import create_engine as sqlalchemy_create_engine, text
from sqlalchemy.engine.base import Engine, Connection
from sqlalchemy.engine.cursor import CursorResult
from sqlalchemy.engine.url import URL
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.exc import OperationalError
from pandas import DataFrame
from reytool.rdata import objs_in, RGenerator
from reytool.rmonkey import monkey_patch_sqlalchemy_result_more_fetch, monkey_patch_sqlalchemy_row_index_field
from reytool.rregex import search
from reytool.rstdout import echo
from reytool.rsystem import throw, get_first_notnull
from reytool.rtable import Table, fetch_table
from reytool.rtext import join_data_text, to_json
from reytool.rwrap import wrap_runtime, wrap_retry


__all__ = (
    "RResult",
    "RDatabase",
    "RDBConnection"
)


# Monkey path.
monkey_result = monkey_patch_sqlalchemy_result_more_fetch()
RResult = monkey_result
monkey_patch_sqlalchemy_row_index_field()


class RDatabase(object):
    """
    Rey's `database` type.
    """


    # Values to be converted to "NULL".
    nulls: Tuple = ("", " ", b"", [], (), {}, set())

    # Default value.
    default_report: bool = False


    @overload
    def __init__(
        self,
        host: None = None,
        port: Optional[Union[str, int]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        drivername: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: Optional[int] = None,
        retry: bool = False,
        url: None = None,
        engine: None = None,
        **query: str
    ) -> NoReturn: ...

    @overload
    def __init__(
        self,
        host: Optional[str] = None,
        port: None = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        drivername: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: Optional[int] = None,
        retry: bool = False,
        url: None = None,
        engine: None = None,
        **query: str
    ) -> NoReturn: ...

    @overload
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[Union[str, int]] = None,
        username: None = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        drivername: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: Optional[int] = None,
        retry: bool = False,
        url: None = None,
        engine: None = None,
        **query: str
    ) -> NoReturn: ...

    @overload
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[Union[str, int]] = None,
        username: Optional[str] = None,
        password: None = None,
        database: Optional[str] = None,
        drivername: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: Optional[int] = None,
        retry: bool = False,
        url: None = None,
        engine: None = None,
        **query: str
    ) -> NoReturn: ...

    @overload
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[Union[str, int]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        drivername: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: Optional[int] = None,
        retry: bool = False,
        url: Optional[Union[str, URL]] = None,
        engine: Optional[Union[Engine, Connection]] = None,
        **query: str
    ) -> None: ...

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[Union[str, int]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        drivername: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: Optional[int] = None,
        retry: bool = False,
        url: Optional[Union[str, URL]] = None,
        engine: Optional[Union[Engine, Connection]] = None,
        **query: str
    ) -> None:
        """
        Build `database` instance.

        Parameters
        ----------
        host : Server host.
        port : Server port.
        username : Server username.
        password : Server password.
        database : Database name in the server.
        drivername : Database backend and driver name.
            - `None` : Automatic select and try.
            - `str` : Use this value.

        pool_size : Number of connections `keep open`.
        max_overflow : Number of connections `allowed overflow`.
        pool_timeout : Number of seconds `wait create` connection.
        pool_recycle : Number of seconds `recycle` connection.
            - `None` : Use database variable `wait_timeout` value.
            - `Literal[-1]` : No recycle.
            - `int` : Use this value.

        retry : Whether retry execute.
        url: Get parameter from server `URL`, but preferred input parameters.
            Parameters include `username`, `password`, `host`, `port`, `database`, `drivername`, `query`.
        engine : Use existing `Engine` or `Connection` object, and get parameter from it.
            Parameters include `username`, `password`, `host`, `port`, `database`, `drivername`, `query`,
            `pool_size`, `max_overflow`, `pool_timeout`, `pool_recycle`.
        query : Server parameters.
        """

        # Handle parameter.
        if port.__class__ == int:
            port = str(port)

        # Set attribute.
        self.retry = retry

        # From existing Engine or Connection object.
        if engine is not None:

            ## Extract Engine object from Connection boject.
            if engine.__class__ == Connection:
                engine = engine.engine

            ## Extract parameter.
            params = self.extract_engine(engine)

            ## Set.
            self.drivername: str = params["drivername"]
            self.username: str = params["username"]
            self.password: str = params["password"]
            self.host: str = params["host"]
            self.port: str = params["port"]
            self.database: Optional[str] = params["database"]
            self.query: Dict = params["query"]
            self.pool_size: int = params["pool_size"]
            self.max_overflow: int = params["max_overflow"]
            self.pool_timeout: float = params["pool_timeout"]
            self.pool_recycle: int = params["pool_recycle"]
            self.engine = engine

        # From parameters create.
        else:

            ## Extract parameters from URL.
            if url is not None:
                params = self.extract_url(url)
            else:
                params = dict.fromkeys(
                    (
                        "drivername",
                        "username",
                        "password",
                        "host",
                        "port",
                        "database",
                        "query"
                    )
                )

            ## Set parameters by priority.
            self.drivername: str = get_first_notnull(drivername, params["drivername"])
            self.username: str = get_first_notnull(username, params["username"], default="exception")
            self.password: str = get_first_notnull(password, params["password"], default="exception")
            self.host: str = get_first_notnull(host, params["host"], default="exception")
            self.port: str = get_first_notnull(port, params["port"], default="exception")
            self.database: Optional[str] = get_first_notnull(database, params["database"])
            self.query: Dict = get_first_notnull(query, params["query"])
            self.pool_size = pool_size
            self.max_overflow = max_overflow
            self.pool_timeout = pool_timeout

            ## Create Engine object.
            if pool_recycle is None:
                self.pool_recycle = -1
                self.engine = self.create_engine()
                wait_timeout = int(self.variables["wait_timeout"])
                self.pool_recycle = wait_timeout
                self.engine.pool._recycle = wait_timeout
            else:
                self.pool_recycle = pool_recycle
                self.engine = self.create_engine()


    def extract_url(self, url: Union[str, URL]) -> Dict[
        Literal["drivername", "username", "password", "host", "port", "database", "query"],
        Any
    ]:
        """
        Extract parameters from URL of string.

        Parameters
        ----------
        url : URL of string.

        Returns
        -------
        Extracted parameters.
        """

        # Extract.

        ## When str object.
        if url.__class__ == str:
            pattern = "^([\w\+]+)://(\w+):(\w+)@(\d+\.\d+\.\d+\.\d+):(\d+)[/]?([\w/]+)?[\?]?([\w&=]+)?$"
            result = search(pattern, url)
            if result is None:
                throw(ValueError, url)
            (
                drivername,
                username,
                password,
                host,
                port,
                database,
                query_str
            ) = result
            if query_str is not None:
                pattern = "(\w+)=(\w+)"
                query_findall = findall(pattern, query_str)
                query = {key: value for key, value in query_findall}
            else:
                query = {}

        ## When URL object.
        elif url.__class__ == URL:
            drivername = url.drivername
            username = url.username
            password = url.password
            host = url.host
            port = url.port
            database = url.database
            query = dict(url.query)

        # Generate parameter.
        params = {
            "drivername": drivername,
            "username": username,
            "password": password,
            "host": host,
            "port": port,
            "database": database,
            "query": query
        }

        return params


    def extract_engine(self, engine: Union[Engine, Connection]) -> Dict[
        Literal[
            "drivername", "username", "password", "host", "port", "database", "query",
            "pool_size", "max_overflow", "pool_timeout", "pool_recycle"
        ],
        Any
    ]:
        """
        Extract parameters from `Engine` or `Connection` object.

        Parameters
        ----------
        engine : Engine or Connection object.

        Returns
        -------
        Extracted parameters.
        """

        ## Extract Engine object from Connection boject.
        if engine.__class__ == Connection:
            engine = engine.engine

        ## Extract.
        drivername = engine.url.drivername
        username = engine.url.username
        password = engine.url.password
        host = engine.url.host
        port = engine.url.port
        database = engine.url.database
        query = dict(engine.url.query)
        pool_size = engine.pool._pool.maxsize
        max_overflow = engine.pool._max_overflow
        pool_timeout = engine.pool._timeout
        pool_recycle = engine.pool._recycle

        # Generate parameter.
        params = {
            "drivername": drivername,
            "username": username,
            "password": password,
            "host": host,
            "port": port,
            "database": database,
            "query": query,
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_timeout": pool_timeout,
            "pool_recycle": pool_recycle
        }

        return params


    @overload
    def extract_path(
        self,
        path: str,
        main: Literal["table"] = "table"
    ) -> Tuple[Optional[str], str, Optional[str]]: ...

    @overload
    def extract_path(
        self,
        path: str,
        main: Literal["database"] = "table"
    ) -> Tuple[str, Optional[str], Optional[str]]: ...

    def extract_path(
        self,
        path: str,
        main: Literal["table", "database"] = "table"
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extract table name and database name and column name from path.

        Parameters
        ----------
        path : Automatic extract.
            * ```Not contain '.' or contain '`'```: Main name.
            * `Contain '.'` : Database name and table name, column name is optional. Example 'database.table[.column]'.

        main : Priority main name, 'table' or 'database'.

        Returns
        -------
        Database name and table name and column name.
        """

        # Extract.
        if (
            "." not in path
            or "`" in path
        ):
            name = path.replace("`", "")
            if main == "table":
                names = (None, name, None)
            elif main == "database":
                names = (name, None, None)
            else:
                throw(ValueError, main)
        else:
            names = path.split(".", 2)
            if len(names) == 2:
                names.append(None)
            names = tuple(names)

        return names


    @property
    def url(self) -> str:
        """
        Generate server URL.

        Returns
        -------
        Server URL.
        """

        # Generate URL.
        password = urllib_quote(self.password)
        _url = f"{self.drivername}://{self.username}:{password}@{self.host}:{self.port}"

        # Add database path.
        if self.database is not None:
            _url = f"{_url}/{self.database}"

        # Add Server parameter.
        if self.query != {}:
            query = "&".join(
                [
                    f"{key}={value}"
                    for key, value in self.query.items()
                ]
            )
            _url = f"{_url}?{query}"

        return _url


    def create_engine(self, **kwargs) -> Engine:
        """
        Create database `Engine` object.

        Parameters
        ----------
        kwargs : Keyword arguments of create engine method.

        Returns
        -------
        Engine object.
        """

        # Handle parameter.
        if self.drivername is None:
            drivernames = ("mysql+mysqldb", "mysql+pymysql", "mysql+mysqlconnector")
        else:
            drivernames = (self.drivername,)

        # Create Engine object.
        for drivername in drivernames:

            ## Set engine parameter.
            self.drivername = drivername
            engine_params = {
                "url": self.url,
                "pool_size": self.pool_size,
                "max_overflow": self.max_overflow,
                "pool_timeout": self.pool_timeout,
                "pool_recycle": self.pool_recycle,
                **kwargs
            }

            ## Try create.
            try:
                engine = sqlalchemy_create_engine(**engine_params)
            except ModuleNotFoundError:
                pass
            else:
                return engine

        # Throw exception.
        drivernames_str = " and ".join(
            [
                "'%s'" % dirvername.split("+", 1)[-1]
                for dirvername in drivernames
            ]
        )
        raise ModuleNotFoundError(f"module {drivernames_str} not fund")


    @property
    def count(self) -> Tuple[int, int]:
        """
        Count number of keep open and allowed overflow connection.

        Returns
        -------
        Number of keep open and allowed overflow connection.
        """

        # Get parameter.
        if hasattr(self, "engine"):
            rdatabase = self
        else:
            rdatabase: RDatabase = self.rdatabase

        # Count.
        _overflow = rdatabase.engine.pool._overflow
        if _overflow < 0:
            keep_n = rdatabase.pool_size + _overflow
            overflow_n = 0
        else:
            keep_n = rdatabase.pool_size
            overflow_n = _overflow

        return keep_n, overflow_n


    def handle_data(
        self,
        data: Table,
        sql: Union[str, TextClause],
    ) -> List[Dict]:
        """
        Handle data based on the content of SQL.

        Parameters
        ----------
        data : Data set for filling.
        sql : SQL in method sqlalchemy.text format, or TextClause object.

        Returns
        -------
        Filled data.
        """

        # Handle parameter.
        if data.__class__ == dict:
            data = [data]
        elif data.__class__ != list:
            data = fetch_table(data)
        if sql.__class__ == TextClause:
            sql = sql.text

        # Extract keys.
        pattern = "(?<!\\\):(\w+)"
        sql_keys = findall(pattern, sql)

        # Extract keys of syntax "in".
        pattern = "[iI][nN]\s+(?<!\\\):(\w+)"
        sql_keys_in = findall(pattern, sql)

        # Loop.
        for row in data:
            if row == {}:
                continue
            for key in sql_keys:
                value = row.get(key)

                # Fill.
                if (
                    value is None
                    or value in self.nulls
                ):
                    row[key] = None

                # Convert.
                elif (
                    value.__class__ in (list, dict)
                    and key not in sql_keys_in
                ):
                    value= to_json(value)
                    row[key] = value

        return data


    def get_syntax(self, sql: Union[str, TextClause]) -> List[str]:
        """
        Extract SQL syntax type for each segment form SQL.

        Parameters
        ----------
        sql : SQL text or TextClause object.

        Returns
        -------
        SQL syntax type for each segment.
        """

        # Handle parameter.
        if sql.__class__ == TextClause:
            sql = sql.text

        # Extract.
        syntax = [
            search("[a-zA-Z]+", sql_part).upper()
            for sql_part in sql.split(";")
        ]

        return syntax


    def is_multi_sql(self, sql: Union[str, TextClause]) -> bool:
        """
        Judge whether it is multi segment SQL.

        Parameters
        ----------
        sql : SQL text or TextClause object.

        Returns
        -------
        Judgment result.
        """

        # Handle parameter.
        if sql.__class__ == TextClause:
            sql = sql.text

        # Judge.
        if ";" in sql.rstrip()[:-1]:
            return True
        return False


    def executor(
        self,
        connection: Connection,
        sql: TextClause,
        data: List[Dict],
        report: bool
    ) -> RResult:
        """
        SQL executor.

        Parameters
        ----------
        connection : Connection object.
        sql : TextClause object.
        data : Data set for filling.
        report : Whether report SQL execute information.

        Returns
        -------
        Result object.
        """

        # Create Transaction object.
        with connection.begin():

            # Execute.

            ## Report.
            if report:
                result, report_runtime = wrap_runtime(connection.execute, sql, data, _return_report=True)
                report_info = (
                    f"{report_runtime}\n"
                    f"Row Count: {result.rowcount}"
                )
                sqls = [
                    sql_part.strip()
                    for sql_part in sql.text.split(";")
                ]
                if data == []:
                    echo(report_info, *sqls, title="SQL")
                else:
                    echo(report_info, *sqls, data, title="SQL")

            ## Not report.
            else:
                result = connection.execute(sql, data)

        return result


    def execute(
        self,
        sql: Union[str, TextClause],
        data: Optional[Table] = None,
        report: Optional[bool] = None,
        **kwdata: Any
    ) -> RResult:
        """
        Execute SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or `TextClause` object.
        data : Data set for filling.
        report : Whether report SQL execute information.
            - `None` : Use attribute `default_report`.
            - `bool` : Use this value.

        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.
        """

        # Get parameter by priority.
        report = get_first_notnull(report, self.default_report, default="exception")

        # Handle parameter.
        if sql.__class__ == str:
            sql = text(sql)
        if data is None:
            if kwdata == {}:
                data = []
            else:
                data = [kwdata]
        else:
            if data.__class__ == dict:
                data = [data]
            elif isinstance(data, CursorResult):
                data = fetch_table(data)
            elif data.__class__ == DataFrame:
                data = fetch_table(data)
            else:
                data = data.copy()
            for param in data:
                param.update(kwdata)

        # Handle data.
        data = self.handle_data(data, sql)

        # Execute.

        ## Create Connection object.
        with self.engine.connect() as connection:

            ## Can retry.
            if (
                self.retry
                and not self.is_multi_sql(sql)
            ):
                result = wrap_retry(
                    self.executor,
                    connection,
                    sql,
                    data,
                    report,
                    _report="Database Execute Operational Error",
                    _exception=OperationalError
                )

            ## Cannot retry.
            else:
                result = self.executor(connection, sql, data, report)

        return result


    def execute_select(
        self,
        path: Union[str, Tuple[str, str]],
        fields: Optional[Union[str, Iterable[str]]] = None,
        where: Optional[str] = None,
        group: Optional[str] = None,
        having: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[Union[int, str, Tuple[int, int]]] = None,
        report: Optional[bool] = None,
        **kwdata: Any
    ) -> RResult:
        """
        Execute select SQL.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        fields : Select clause content.
            - `None` : Is `SELECT *`.
            - `str` : Join as `SELECT str`.
            - `Iterable[str]` : Join as `SELECT \`str\`, ...`.
                * `str and first character is ':'` : Use this syntax.
                * `str` : Use this field.

        where : Clause `WHERE` content, join as `WHERE str`.
        group : Clause `GROUP BY` content, join as `GROUP BY str`.
        having : Clause `HAVING` content, join as `HAVING str`.
        order : Clause `ORDER BY` content, join as `ORDER BY str`.
        limit : Clause `LIMIT` content.
            - `Union[int, str]` : Join as `LIMIT int/str`.
            - `Tuple[int, int]` : Join as `LIMIT int, int`.

        report : Whether report SQL execute information.
            - `None` : Use attribute `report_execute_info` of object `ROption`.
            - `int` : Use this value.

        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `fields`.
        >>> fields = ['id', ':`id` + 1 AS `id_`']
        >>> result = RDatabase.execute_select('database.table', fields)
        >>> print(result.fetch_table())
        [{'id': 1, 'id_': 2}, ...]

        Parameter `kwdata`.
        >>> fields = '`id`, `id` + :value AS `id_`'
        >>> result = RDatabase.execute_select('database.table', fields, value=1)
        >>> print(result.fetch_table())
        [{'id': 1, 'id_': 2}, ...]
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, _ = self.extract_path(path)
        else:
            database, table = path

        # Get parameter by priority.
        database = get_first_notnull(database, self.database, default="exception")

        # Generate SQL.
        sql_list = []

        ## Part "SELECT" syntax.
        if fields is None:
            fields = "*"
        elif fields.__class__ != str:
            fields = ", ".join(
                [
                    field[1:]
                    if (
                        field.startswith(":")
                        and field != ":"
                    )
                    else f"`{field}`"
                    for field in fields
                ]
            )
        sql_select = f"SELECT {fields}"
        sql_list.append(sql_select)

        ## Part "FROM" syntax.
        sql_from = f"FROM `{database}`.`{table}`"
        sql_list.append(sql_from)

        ## Part "WHERE" syntax.
        if where is not None:
            sql_where = f"WHERE {where}"
            sql_list.append(sql_where)

        ## Part "GROUP BY" syntax.
        if group is not None:
            sql_group = f"GROUP BY {group}"
            sql_list.append(sql_group)

        ## Part "GROUP BY" syntax.
        if having is not None:
            sql_having = f"HAVING {having}"
            sql_list.append(sql_having)

        ## Part "ORDER BY" syntax.
        if order is not None:
            sql_order = f"ORDER BY {order}"
            sql_list.append(sql_order)

        ## Part "LIMIT" syntax.
        if limit is not None:
            if limit.__class__ in (str, int):
                sql_limit = f"LIMIT {limit}"
            else:
                if len(limit) == 2:
                    sql_limit = f"LIMIT {limit[0]}, {limit[1]}"
                else:
                    throw(ValueError, limit)
            sql_list.append(sql_limit)

        ## Join sql part.
        sql = "\n".join(sql_list)

        # Execute SQL.
        result = self.execute(sql, report=report, **kwdata)

        return result


    def execute_insert(
        self,
        path: Union[str, Tuple[str, str]],
        data: Table,
        duplicate: Optional[Literal["ignore", "update"]] = None,
        report: Optional[bool] = None,
        **kwdata: Any
    ) -> RResult:
        """
        Insert the data of table in the datebase.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        data : Insert data.
        duplicate : Handle method when constraint error.
            - `None` : Not handled.
            - `ignore` : Use `UPDATE IGNORE INTO` clause.
            - `update` : Use `ON DUPLICATE KEY UPDATE` clause.

        report : Whether report SQL execute information.
            - `None` : Use attribute `report_execute_info` of object `ROption`.
            - `int` : Use this value.

        kwdata : Keyword parameters for filling.
            - `str and first character is ':'` : Use this syntax.
            - `Any` : Use this value.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `data` and `kwdata`.
        >>> data = [{'key': 'a'}, {'key': 'b'}]
        >>> kwdata = {'value1': 1, 'value2': ':(SELECT 2)'}
        >>> result = RDatabase.execute_insert('database.table', data, **kwdata)
        >>> print(result.rowcount)
        2
        >>> result = RDatabase.execute_select('database.table')
        >>> print(result.fetch_table())
        [{'key': 'a', 'value1': 1, 'value2': 2}, {'key': 'b', 'value1': 1, 'value2': 2}]
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, _ = self.extract_path(path)
        else:
            database, table = path

        # Get parameter by priority.
        database = get_first_notnull(database, self.database, default="exception")

        # Handle parameter.

        ## Data.
        if data.__class__ == dict:
            data = [data]
        elif isinstance(data, CursorResult):
            data = fetch_table(data)
        elif data.__class__ == DataFrame:
            data = fetch_table(data)

        ## Check.
        if data in ([], [{}]):
            throw(ValueError, data)

        ## Keyword data.
        kwdata_method = {}
        kwdata_replace = {}
        for key, value in kwdata.items():
            if (
                value.__class__ == str
                and value.startswith(":")
                and value != ":"
            ):
                kwdata_method[key] = value[1:]
            else:
                kwdata_replace[key] = value

        # Generate SQL.

        ## Part "fields" syntax.
        fields_replace = {
            field
            for row in data
            for field in row
        }
        fields_replace = {
            field
            for field in fields_replace
            if field not in kwdata
        }
        sql_fields_list = (
            *kwdata_method,
            *kwdata_replace,
            *fields_replace
        )
        sql_fields = ", ".join(
            [
                f"`{field}`"
                for field in sql_fields_list
            ]
        )

        ## Part "values" syntax.
        sql_values_list = (
            *kwdata_method.values(),
            *[
                ":" + field
                for field in (
                    *kwdata_replace,
                    *fields_replace
                )
            ]
        )
        sql_values = ", ".join(sql_values_list)

        ## Join sql part.

        ### Ignore.
        if duplicate == "ignore":
            sql = (
                f"INSERT IGNORE INTO `{database}`.`{table}`({sql_fields})\n"
                f"VALUES({sql_values})"
            )

        ### Update.
        elif duplicate == "update":
            update_content = ",\n    ".join([f"`{field}` = VALUES(`{field}`)" for field in sql_fields_list])
            sql = (
                f"INSERT INTO `{database}`.`{table}`({sql_fields})\n"
                f"VALUES({sql_values})\n"
                "ON DUPLICATE KEY UPDATE\n"
                f"    {update_content}"
            )

        ### Not handle.
        else:
            sql = (
                f"INSERT INTO `{database}`.`{table}`({sql_fields})\n"
                f"VALUES({sql_values})"
            )

        # Execute SQL.
        result = self.execute(sql, data, report, **kwdata_replace)

        return result


    def execute_update(
        self,
        path: Union[str, Tuple[str, str]],
        data: Table,
        where_fields: Optional[Union[str, Iterable[str]]] = None,
        report: Optional[bool] = None,
        **kwdata: Any
    ) -> RResult:
        """
        Update the data of table in the datebase.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        data : Update data, clause `SET` and `WHERE` and `ORDER BY` and `LIMIT` content.
            - `Key` : Table field.
                * `literal['order']` : Clause `ORDER BY` content, join as `ORDER BY str`.
                * `literal['limit']` : Clause `LIMIT` content, join as `LIMIT str`.
                * `Other` : Clause `SET` and `WHERE` content.
            - `Value` : Table value.
                * `Union[List, Tuple]` : Join as `field IN :str`.
                * `Any` : Join as `field = :str`.

        where_fields : Clause `WHERE` content fields.
            - `None` : The first key value pair of each item is judged.
            - `str` : This key value pair of each item is judged.
            - `Iterable[str]` : Multiple judged, `and` relationship.

        report : Whether report SQL execute information.
            - `None` : Use attribute `report_execute_info` of object `ROption`.
            - `int` : Use this value.

        kwdata : Keyword parameters for filling.
            - `str and first character is ':'` : Use this syntax.
            - `Any` : Use this value.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `data` and `kwdata`.
        >>> data = [{'key': 'a'}, {'key': 'b'}]
        >>> kwdata = {'value': 1, 'name': ':`key`'}
        >>> result = RDatabase.execute_update('database.table', data, **kwdata)
        >>> print(result.rowcount)
        2
        >>> result = RDatabase.execute_select('database.table')
        >>> print(result.fetch_table())
        [{'key': 'a', 'value': 1, 'name': 'a'}, {'key': 'b', 'value': 1, 'name': 'b'}]
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, _ = self.extract_path(path)
        else:
            database, table = path

        # Get parameter by priority.
        database = get_first_notnull(database, self.database, default="exception")

        # Handle parameter.

        ## Data.
        if data.__class__ == dict:
            data = [data]
        elif isinstance(data, CursorResult):
            data = fetch_table(data)
        elif data.__class__ == DataFrame:
            data = fetch_table(data)

        ## Check.
        if data in ([], [{}]):
            throw(ValueError, data)

        ## Keyword data.
        kwdata_method = {}
        kwdata_replace = {}
        for key, value in kwdata.items():
            if (
                value.__class__ == str
                and value.startswith(":")
                and value != ":"
            ):
                kwdata_method[key] = value[1:]
            else:
                kwdata_replace[key] = value
        sql_set_list_kwdata = [
            f"`{key}` = {value}"
            for key, value in kwdata_method.items()
        ]
        sql_set_list_kwdata.extend(
            [
                f"`{key}` = :{key}"
                for key in kwdata_replace
            ]
        )

        # Generate SQL.
        data_flatten = kwdata_replace
        if where_fields is None:
            no_where = True
        else:
            no_where = False
            if where_fields.__class__ == str:
                where_fields = [where_fields]
        sqls_list = []
        sql_update = f"UPDATE `{database}`.`{table}`"
        for index, row in enumerate(data):
            sql_parts = [sql_update]
            for key, value in row.items():
                if key in ("order", "limit"):
                    continue
                index_key = f"{index}_{key}"
                data_flatten[index_key] = value
            if no_where:
                for key in row:
                    where_fields = [key]
                    break

            ## Part "SET" syntax.
            sql_set_list = sql_set_list_kwdata.copy()
            sql_set_list.extend(
                [
                    f"`{key}` = :{index}_{key}"
                    for key in row
                    if (
                        key not in where_fields
                        and key not in kwdata
                        and key not in ("order", "limit")
                    )
                ]
            )
            sql_set = "SET " + ",\n    ".join(sql_set_list)
            sql_parts.append(sql_set)

            ## Part "WHERE" syntax.
            sql_where_list = []
            for field in where_fields:
                index_field = f"{index}_{field}"
                index_value = data_flatten[index_field]
                if index_value.__class__ in (list, tuple):
                    sql_where_part = f"`{field}` IN :{index_field}"
                else:
                    sql_where_part = f"`{field}` = :{index_field}"
                sql_where_list.append(sql_where_part)
            sql_where = "WHERE " + "\n    AND ".join(sql_where_list)
            sql_parts.append(sql_where)

            ## Part "ORDER BY" syntax.
            order = row.get("order")
            if order is not None:
                sql_order = f"ORDER BY {order}"
                sql_parts.append(sql_order)

            ## Part "LIMIT" syntax.
            limit = row.get("limit")
            if limit is not None:
                sql_limit = f"LIMIT {limit}"
                sql_parts.append(sql_limit)

            ## Join sql part.
            sql = "\n".join(sql_parts)
            sqls_list.append(sql)

        ## Join sqls.
        sqls = ";\n".join(sqls_list)

        # Execute SQL.
        result = self.execute(sqls, data_flatten, report)

        return result


    def execute_delete(
        self,
        path: Union[str, Tuple[str, str]],
        where: Optional[str] = None,
        order: Optional[str] = None,
        limit: Optional[Union[int, str]] = None,
        report: Optional[bool] = None,
        **kwdata: Any
    ) -> RResult:
        """
        Delete the data of table in the datebase.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        where : Clause `WHERE` content, join as `WHERE str`.
        order : Clause `ORDER BY` content, join as `ORDER BY str`.
        limit : Clause `LIMIT` content, join as `LIMIT int/str`.
        report : Whether report SQL execute information.
            - `None` : Use attribute `report_execute_info` of object `ROption`.
            - `int` : Use this value.

        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `where` and `kwdata`.
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2)
        >>> result = RDatabase.execute_delete('database.table', where, ids=ids)
        >>> print(result.rowcount)
        2
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, _ = self.extract_path(path)
        else:
            database, table = path

        # Get parameter by priority.
        database = get_first_notnull(database, self.database, default="exception")

        # Generate SQL.
        sqls = []

        ## Part 'DELETE' syntax.
        sql_delete = f"DELETE FROM `{database}`.`{table}`"
        sqls.append(sql_delete)

        ## Part 'WHERE' syntax.
        if where is not None:
            sql_where = f"WHERE {where}"
            sqls.append(sql_where)

        ## Part "ORDER BY" syntax.
        if order is not None:
            sql_order = f"ORDER BY {order}"
            sqls.append(sql_order)

        ## Part "LIMIT" syntax.
        if limit is not None:
            sql_limit = f"LIMIT {limit}"
            sqls.append(sql_limit)

        ## Join sqls.
        sqls = "\n".join(sqls)

        # Execute SQL.
        result = self.execute(sqls, report=report, **kwdata)

        return result


    def execute_copy(
        self,
        path: Union[str, Tuple[str, str]],
        where: Optional[str] = None,
        limit: Optional[Union[int, str, Tuple[int, int]]] = None,
        report: Optional[bool] = None,
        **kwdata: Any
    ) -> RResult:
        """
        Copy record of table in the datebase.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        where : Clause `WHERE` content, join as `WHERE str`.
        limit : Clause `LIMIT` content.
            - `Union[int, str]` : Join as `LIMIT int/str`.
            - `Tuple[int, int]` : Join as `LIMIT int, int`.

        report : Whether report SQL execute information.
            - `None` : Use attribute `report_execute_info` of object `ROption`.
            - `int` : Use this value.

        kwdata : Keyword parameters for filling.
            - `In 'WHERE' syntax` : Fill 'WHERE' syntax.
            - `Not in 'WHERE' syntax` : Fill 'INSERT' and 'SELECT' syntax.
                * `str and first character is ':'` : Use this syntax.
                * `Any` : Use this value.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `where` and `kwdata`.
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2, 3)
        >>> result = RDatabase.execute_copy('database.table', where, 2, ids=ids, id=None, time=':NOW()')
        >>> print(result.rowcount)
        2
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, _ = self.extract_path(path)
        else:
            database, table = path

        # Get parameter by priority.
        database = get_first_notnull(database, self.database, default="exception")

        # Get parameter.
        table_info: List[Dict] = self.info(database)(table)()
        fields = [
            row["COLUMN_NAME"]
            for row in table_info
        ]
        pattern = "(?<!\\\):(\w+)"
        if where.__class__ == str:
            where_keys = findall(pattern, where)
        else:
            where_keys = ()

        # Generate SQL.
        sqls = []

        ## Part "INSERT" syntax.
        sql_fields = ", ".join(
            f"`{field}`"
            for field in fields
            if field not in kwdata
        )
        if kwdata != {}:
            sql_fields_kwdata = ", ".join(
                f"`{field}`"
                for field in kwdata
                if field not in where_keys
            )
            sql_fields_filter = filter(
                lambda sql: sql != "",
                (
                    sql_fields,
                    sql_fields_kwdata
                )
            )
            sql_fields = ", ".join(sql_fields_filter)
        sql_insert = f"INSERT INTO `{database}`.`{table}`({sql_fields})"
        sqls.append(sql_insert)

        ## Part "SELECT" syntax.
        sql_values = ", ".join(
            f"`{field}`"
            for field in fields
            if field not in kwdata
        )
        if kwdata != {}:
            sql_values_kwdata = ", ".join(
                value[1:]
                if (
                    value.__class__ == str
                    and value.startswith(":")
                    and value != ":"
                )
                else f":{field}"
                for field, value in kwdata.items()
                if field not in where_keys
            )
            sql_values_filter = filter(
                lambda sql: sql != "",
                (
                    sql_values,
                    sql_values_kwdata
                )
            )
            sql_values = ", ".join(sql_values_filter)
        sql_select = (
            f"SELECT {sql_values}\n"
            f"FROM `{database}`.`{table}`"
        )
        sqls.append(sql_select)

        ## Part "WHERE" syntax.
        if where is not None:
            sql_where = f"WHERE {where}"
            sqls.append(sql_where)

        ## Part "LIMIT" syntax.
        if limit is not None:
            if limit.__class__ in (str, int):
                sql_limit = f"LIMIT {limit}"
            else:
                if len(limit) == 2:
                    sql_limit = f"LIMIT {limit[0]}, {limit[1]}"
                else:
                    throw(ValueError, limit)
            sqls.append(sql_limit)

        ## Join.
        sql = "\n".join(sqls)

        # Execute SQL.
        result = self.execute(sql, report=report, **kwdata)

        return result


    def execute_exist(
        self,
        path: Union[str, Tuple[str, str]],
        where: Optional[str] = None,
        report: Optional[bool] = None,
        **kwdata: Any
    ) -> bool:
        """
        Judge the exist of record.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        where : Match condition, `WHERE` clause content, join as `WHERE str`.
            - `None` : Match all.
            - `str` : Match condition.

        report : Whether report SQL execute information.
            - `None` : Use attribute `report_execute_info` of object `ROption`.
            - `int` : Use this value.

        kwdata : Keyword parameters for filling.

        Returns
        -------
        Judged result.

        Examples
        --------
        Parameter `where` and `kwdata`.
        >>> data = [{'id': 1}]
        >>> RDatabase.execute_insert('database.table', data)
        >>> where = '`id` = :id_'
        >>> id_ = 1
        >>> result = RDatabase.execute_exist('database.table', where, id_=id_)
        >>> print(result)
        True
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, _ = self.extract_path(path)
        else:
            database, table = path

        # Execute.
        result = self.execute_select((database, table), "1", where=where, limit=1, report=report, **kwdata)

        # Judge.
        judge = result.exist

        return judge


    def execute_count(
        self,
        path: Union[str, Tuple[str, str]],
        where: Optional[str] = None,
        report: Optional[bool] = None,
        **kwdata: Any
    ) -> int:
        """
        Count records.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        where : Match condition, `WHERE` clause content, join as `WHERE str`.
            - `None` : Match all.
            - `str` : Match condition.

        report : Whether report SQL execute information.
            - `None` : Use attribute `report_execute_info` of object `ROption`.
            - `int` : Use this value.

        kwdata : Keyword parameters for filling.

        Returns
        -------
        Record count.

        Examples
        --------
        Parameter `where` and `kwdata`.
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2)
        >>> result = RDatabase.execute_count('database.table', where, ids=ids)
        >>> print(result)
        2
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, _ = self.extract_path(path)
        else:
            database, table = path

        # Execute.
        result = self.execute_select((database, table), "1", where=where, report=report, **kwdata)
        count = result.rowcount

        return count


    def execute_generator(
        self,
        sql: Union[str, TextClause],
        data: Table,
        report: Optional[bool] = None,
        **kwdata: Any
    ) -> Generator[RResult, Any, None]:
        """
        Return a generator that can execute SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or `TextClause` object.
        data : Data set for filling.
        report : Whether report SQL execute information.
            - `None` : Use attribute `default_report`.
            - `bool` : Use this value.

        kwdata : Keyword parameters for filling.

        Returns
        -------
        Generator.
        """

        # Handle parameter.
        if data.__class__ == dict:
            data = [data]
        elif isinstance(data, CursorResult):
            data = fetch_table(data)
        elif data.__class__ == DataFrame:
            data = fetch_table(data)
        else:
            data = data.copy()

        # Instance.
        rgenerator = RGenerator(
            self.execute,
            sql=sql,
            report=report,
            **kwdata
        )

        # Add.
        for row in data:
            rgenerator(**row)

        return rgenerator.generator


    def connect(self) -> RDBConnection:
        """
        Build `database connection` instance.

        Returns
        -------
        Database connection instance.
        """

        # Build.
        rdbconnection = RDBConnection(
            self.engine.connect(),
            self
        )

        return rdbconnection


    @property
    def exe(self):
        """
        Build `database execute` instance.

        Returns
        -------
        Database execute instance.

        Examples
        --------
        Execute.
        >>> sql = 'select :value'
        >>> result = RDBExecute(sql, value=1)

        Select.
        >>> field = ["id", "value"]
        >>> where = "`id` = ids"
        >>> ids = (1, 2)
        >>> result = RDBExecute.database.table(field, where, ids=ids)

        Insert.
        >>> data = [{'id': 1}, {'id': 2}]
        >>> duplicate = 'ignore'
        >>> result = RDBExecute.database.table + data
        >>> result = RDBExecute.database.table + (data, duplicate)
        >>> result = RDBExecute.database.table + {"data": data, "duplicate": duplicate}

        Update.
        >>> data = [{'name': 'a', 'id': 1}, {'name': 'b', 'id': 2}]
        >>> where_fields = 'id'
        >>> result = RDBExecute.database.table & data
        >>> result = RDBExecute.database.table & (data, where_fields)
        >>> result = RDBExecute.database.table & {"data": data, "where_fields": where_fields}

        Delete.
        >>> where = '`id` IN (1, 2)'
        >>> report = True
        >>> result = RDBExecute.database.table - where
        >>> result = RDBExecute.database.table - (where, report)
        >>> result = RDBExecute.database.table - {"where": where, "report": report}

        Copy.
        >>> where = '`id` IN (1, 2)'
        >>> limit = 1
        >>> result = RDBExecute.database.table * where
        >>> result = RDBExecute.database.table * (where, limit)
        >>> result = RDBExecute.database.table * {"where": where, "limit": limit}

        Exist.
        >>> where = '`id` IN (1, 2)'
        >>> report = True
        >>> result = where in RDBExecute.database.table
        >>> result = (where, report) in RDBExecute.database.table
        >>> result = {"where": where, "report": report} in RDBExecute.database.table

        Count.
        >>> result = len(RDBExecute.database.table)

        Default database.
        >>> field = ["id", "value"]
        >>> engine = RDatabase(**server, database)
        >>> result = engine.exe.table()
        """

        # Import.
        from .rexecute import RDBExecute

        # Build.
        rdbexecute = RDBExecute(self)

        return rdbexecute


    @property
    def schema(self) -> Dict[str, Dict[str, List]]:
        """
        Get schemata of databases and tables and columns.

        Returns
        -------
        Schemata of databases and tables and columns.
        """

        # Select.
        filter_db = (
            "information_schema",
            "mysql",
            "performance_schema",
            "sys"
        )
        result = self.execute_select(
            "information_schema.COLUMNS",
            ["TABLE_SCHEMA", "TABLE_NAME", "COLUMN_NAME"],
            "`TABLE_SCHEMA` NOT IN :filter_db",
            order="`TABLE_SCHEMA`, `TABLE_NAME`, `ORDINAL_POSITION`",
            filter_db=filter_db
        )

        # Convert.
        database_dict = {}
        for database, table, column in result:

            ## Index database.
            if database not in database_dict:
                database_dict[database] = {table: [column]}
                continue
            table_dict: Dict = database_dict[database]

            ## Index table. 
            if table not in table_dict:
                table_dict[table] = [column]
                continue
            column_list: List = table_dict[table]

            ## Add column.
            column_list.append(column)

        return database_dict


    @property
    def info(self):
        """
        Build `database schema information` instance.

        Returns
        -------
        Database schema information instance.

        Examples
        --------
        Get databases information of server.
        >>> databases_info = RDBISchema()

        Get tables information of database.
        >>> tables_info = RDBISchema.database()

        Get columns information of table.
        >>> columns_info = RDBISchema.database.table()

        Get database attribute.
        >>> database_attr = RDBISchema.database["attribute"]

        Get table attribute.
        >>> database_attr = RDBISchema.database.table["attribute"]

        Get column attribute.
        >>> database_attr = RDBISchema.database.table.column["attribute"]
        """

        # Import.
        from .rinformation import RDBISchema

        # Build.
        rdbischema = RDBISchema(self)

        return rdbischema


    @property
    def build(self):
        """
        Build `database build` instance.

        Returns
        -------
        Database build instance.
        """

        # Import.
        from .rbuild import RDBBuild

        # Build.
        rdbbuild = RDBBuild(self)

        return rdbbuild


    @property
    def file(self):
        """
        Build `database file` instance.

        Returns
        -------
        Database file instance.
        """

        # Import.
        from .rfile import RDBFile

        # Build.
        rdbfile = RDBFile(self)

        return rdbfile


    @property
    def status(self):
        """
        Build `database status parameters` instance.

        Returns
        -------
        Database status parameters instance.
        """

        # Import.
        from .rparameter import RDBPStatus

        # Build.
        rdbpstatus = RDBPStatus(self, False)

        return rdbpstatus


    @property
    def global_status(self):
        """
        Build global `database status parameters` instance.

        Returns
        -------
        Global database status parameters instance.
        """

        # Import.
        from .rparameter import RDBPStatus

        # Build.
        rdbpstatus = RDBPStatus(self, True)

        return rdbpstatus


    @property
    def variables(self):
        """
        Build `database variable parameters` instance.

        Returns
        -------
        Database variable parameters instance.
        """

        # Import.
        from .rparameter import RDBPVariable

        # Build.
        rdbpvariable = RDBPVariable(self, False)

        return rdbpvariable


    @property
    def global_variables(self):
        """
        Build global `database variable parameters` instance.

        Returns
        -------
        Global database variable parameters instance.
        """

        # Import.
        from .rparameter import RDBPVariable

        # Build.
        rdbpvariable = RDBPVariable(self, True)

        return rdbpvariable


    @overload
    def __call__(
        self,
        sql: Union[str, TextClause],
        data: Optional[Table] = None,
        report: Optional[bool] = None,
        generator: Literal[False] = False,
        **kwdata: Any
    ) -> RResult: ...

    @overload
    def __call__(
        self,
        sql: Union[str, TextClause],
        data: Table = None,
        report: Optional[bool] = None,
        generator: Literal[True] = False,
        **kwdata: Any
    ) -> Generator[RResult, Any, None]: ...

    @overload
    def __call__(
        self,
        sql: Union[str, TextClause],
        data: None = None,
        report: Optional[bool] = None,
        generator: Literal[True] = False,
        **kwdata: Any
    ) -> NoReturn: ...

    def __call__(
        self,
        sql: Union[str, TextClause],
        data: Optional[Table] = None,
        report: Optional[bool] = None,
        generator: bool = False,
        **kwdata: Any
    ) -> Union[RResult, Generator[RResult, Any, None]]:
        """
        Execute SQL or return a generator that can execute SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or `TextClause` object.
        data : Data set for filling.
        report : Whether report SQL execute information.
            - `None` : Use attribute `default_report`.
            - `bool` : Use this value.

        generator : whether return a generator that can execute SQL, otherwise execute SQL.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object or generator.
        """

        # Get parameter.
        if generator:
            func = self.execute_generator
        else:
            func = self.execute

        # Execute.
        result = func(
            sql,
            data,
            report,
            **kwdata
        )

        return result


    def __str__(self) -> str:
        """
        Return connection information text.
        """

        # Get parameter.
        if hasattr(self, "engine"):
            attr_dict = self.__dict__
        else:
            rdatabase: RDatabase = self.rdatabase
            attr_dict = {
                **self.__dict__,
                **rdatabase.__dict__
            }

        # Generate.
        filter_key = (
            "engine",
            "connection",
            "rdatabase",
            "begin"
        )
        info = {
            key: value
            for key, value in attr_dict.items()
            if key not in filter_key
        }
        info["count"] = self.count
        text = join_data_text(info)

        return text


class RDBConnection(RDatabase):
    """
    Rey's `database connection` type.
    """


    def __init__(
        self,
        connection: Connection,
        rdatabase: RDatabase
    ) -> None:
        """
        Build `database connection` instance.

        Parameters
        ----------
        connection : Connection object.
        rdatabase : RDatabase object.
        """

        # Set parameter.
        self.connection = connection
        self.rdatabase = rdatabase
        self.begin = None
        self.begin_count = 0
        self.drivername = rdatabase.drivername
        self.username = rdatabase.username
        self.password = rdatabase.password
        self.host = rdatabase.host
        self.port = rdatabase.port
        self.database = rdatabase.database
        self.query = rdatabase.query
        self.pool_recycle = rdatabase.pool_recycle
        self.retry = rdatabase.retry


    def executor(
        self,
        connection: Connection,
        sql: TextClause,
        data: List[Dict],
        report: bool
    ) -> RResult:
        """
        SQL executor.

        Parameters
        ----------
        connection : Connection object.
        sql : TextClause object.
        data : Data set for filling.
        report : Whether report SQL execute information.

        Returns
        -------
        Result object.
        """

        # Create Transaction object.
        if self.begin_count == 0:
            self.rollback()
            self.begin = connection.begin()

        # Execute.

        ## Report.
        if report:
            result, report_runtime = wrap_runtime(connection.execute, sql, data, _return_report=True)
            report_info = (
                f"{report_runtime}\n"
                f"Row Count: {result.rowcount}"
            )
            sqls = [
                sql_part.strip()
                for sql_part in sql.text.split(";")
            ]
            if data == []:
                echo(report_info, *sqls, title="SQL")
            else:
                echo(report_info, *sqls, data, title="SQL")

        ## Not report.
        else:
            result = connection.execute(sql, data)

        # Count.
        syntaxes = self.get_syntax(sql)
        if objs_in(syntaxes, "INSERT", "UPDATE", "DELETE"):
            self.begin_count += 1

        return result


    def execute(
        self,
        sql: Union[str, TextClause],
        data: Optional[Table] = None,
        report: Optional[bool] = None,
        **kwdata: Any
    ) -> RResult:
        """
        Execute SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or `TextClause` object.
        data : Data set for filling.
        report : Whether report SQL execute information.
            - `None` : Use attribute `default_report`.
            - `bool` : Use this value.

        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.
        """

        # Get parameter by priority.
        report = get_first_notnull(report, self.default_report, default="exception")

        # Handle parameter.
        if sql.__class__ == str:
            sql = text(sql)
        if data is None:
            if kwdata == {}:
                data = []
            else:
                data = [kwdata]
        else:
            if data.__class__ == dict:
                data = [data]
            elif isinstance(data, CursorResult):
                data = fetch_table(data)
            elif data.__class__ == DataFrame:
                data = fetch_table(data)
            else:
                data = data.copy()
            for param in data:
                param.update(kwdata)

        # Handle data.
        data = self.handle_data(data, sql)

        # Execute.

        ## Can retry.
        if (
            self.retry
            and self.begin_count == 0
            and not self.is_multi_sql(sql)
        ):
            result = wrap_retry(
                self.executor,
                self.connection,
                sql,
                data,
                report,
                _report="Database Execute Operational Error",
                _exception=OperationalError
            )

        ## Cannot retry.
        else:
            result = self.executor(self.connection, sql, data, report)

        return result


    def commit(self) -> None:
        """
        Commit cumulative executions.
        """

        # Commit.
        if self.begin is not None:
            self.begin.commit()
            self.begin = None
            self.begin_count = 0


    def rollback(self) -> None:
        """
        Rollback cumulative executions.
        """

        # Rollback.
        if self.begin is not None:
            self.begin.rollback()
            self.begin = None
            self.begin_count = 0


    def close(self) -> None:
        """
        Close database connection.
        """

        # Close.
        self.connection.close()


    def __enter__(self) -> RDBConnection:
        """
        Enter syntax `with`.

        Returns
        -------
        Self.
        """

        # Return.
        return self


    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_instance: Optional[BaseException],
        exc_traceback: Optional[TracebackType]
    ) -> None:
        """
        Exit syntax `with`.

        Parameters
        ----------
        exc_type : Exception type.
        exc_instance : Exception instance.
        exc_traceback : Exception traceback instance.
        """

        # Commit.
        if exc_type is None:
            self.commit()

        # Close.
        else:
            self.close()


    __del__ = close