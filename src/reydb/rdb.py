# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database methods.
"""


from typing import Any, Literal, overload
from collections.abc import Iterable, Generator, Container
from enum import EnumType
from urllib.parse import quote as urllib_quote
from pymysql.constants.CLIENT import MULTI_STATEMENTS
from sqlalchemy import create_engine as sqlalchemy_create_engine, text as sqlalchemy_text
from sqlalchemy.engine.base import Engine, Connection
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.exc import OperationalError
from reykit.rbase import throw, is_iterable, get_first_notnone
from reykit.rdata import Generator, to_json
from reykit.rmonkey import monkey_sqlalchemy_result_more_fetch, monkey_sqlalchemy_row_index_field
from reykit.rre import search, findall
from reykit.rstdout import echo
from reykit.rtable import TableData, Table
from reykit.rtext import join_data_text
from reykit.rwrap import wrap_runtime, wrap_retry

from .rbase import DatabaseBase, extract_url


__all__ = (
    'Result',
    'Database'
)


# Monkey path.
Result_ = monkey_sqlalchemy_result_more_fetch()
Result = Result_
monkey_sqlalchemy_row_index_field()


class Database(DatabaseBase):
    """
    Database type.
    Based `MySQL` or `SQLite`.

    Examples
    --------
    >>> rdb = Database()
    >>> result = rdb.execute('SELECT 1 as `a`')
    >>> result.to_table()
    [{'a': 1}]
    """

    # Default value.
    default_report: bool = False


    @overload
    def __init__(
        self,
        host: str,
        port: int | str,
        username: str,
        password: str,
        database: str | None = None,
        *,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: int | None = None,
        retry: bool = False,
        **query: str
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        database: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: int | None = None,
        retry: bool = False,
        **query: str
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: int | None = None,
        retry: bool = False,
        **query: str
    ) -> None: ...


    def __init__(
        self,
        host: str | None = None,
        port: int | str | None = None,
        username: str | None = None,
        password: str | None = None,
        database: str | None = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: int | None = None,
        retry: bool = False,
        **query: str
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        host : Remote server database host.
        port : Remote server database port.
        username : Remote server database username.
        password : Remote server database password.
        database : Remote server database name or local database file path.
            - `None`: When parameters `host`, `port`, `username`, `password`, `database` are all `None`, then using memory store.
        pool_size : Number of connections `keep open`.
        max_overflow : Number of connections `allowed overflow`.
        pool_timeout : Number of seconds `wait create` connection.
        pool_recycle : Number of seconds `recycle` connection.
            - `None`: Automatic select.
                When is remote server database, then is database variable `wait_timeout` value.
                When is local database file, then is `-1`.
            - `Literal[-1]`: No recycle.
            - `int`: Use this value.
        retry : Whether retry execute.
        query : Remote server database parameters.
        """

        # Handle parameter.
        if type(port) == str:
            port = int(port)

        # Build.
        self.username = username
        self.password = password
        self.host = host
        self.port: int | None = port
        self.database = database
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        if pool_recycle is None:
            self.pool_recycle = -1
        else:
            self.pool_recycle = pool_recycle
        self.retry = retry
        self.query = query

        # Create engine.
        self.engine = self.__create_engine()

        # Server recycle time.
        if pool_recycle is None:
            if self.mode == 'server':
                wait_timeout = self.variables['wait_timeout']
                if wait_timeout is not None:
                    self.pool_recycle = int(wait_timeout)
            self.engine.pool._recycle = self.pool_recycle


    @overload
    def extract_path(
        self,
        path: str,
        main: Literal['table', 'database'] = 'table'
    ) -> tuple[str, str, str | None]: ...

    @overload
    def extract_path(
        self,
        path: tuple[str | None, str | None] | tuple[str | None, str | None, str | None],
        main: Literal['table', 'database'] = 'table'
    ) -> tuple[str, str | None, str | None]: ...

    def extract_path(
        self,
        path: str | tuple[str | None, str | None] | tuple[str | None, str | None, str | None],
        main: Literal['table', 'database'] = 'table'
    ) -> tuple[str, str | None, str | None]:
        """
        Extract table name and database name and column name from path.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str`: Automatic extract database name and table name.
                Not contain '.' or contain '`': Main name.
                Contain '.': Database name and table name, column name is optional. Example 'database.table[.column]'.
            - `tuple[str, str]`: Database name and table name.
            - `tuple[str, str | None, str | None]`: Database name and table name and column name.
        path : Automatic extract.
        main : Priority main name, 'table' or 'database'.

        Returns
        -------
        Database name and table name and column name.
        """

        # Type str.
        if type(path) == str:

            ## Single.
            if (
                '.' not in path
                or '`' in path
            ):
                name = path.replace('`', '')
                match main:
                    case 'table':
                        names = (self.database, name, None)
                    case 'database':
                        names = (name, None, None)
                    case _:
                        throw(ValueError, main)

            ## Multiple.
            else:
                names = path.split('.', 2)
                if len(names) == 2:
                    names.append(None)
                names = tuple(names)

        # Type tuple.
        else:
            if len(path) == 2:
                path += (None,)
            if path[0] is None:
                path = (self.database,) + names[1:]
            names = path

        # SQLite.
        if self.backend == 'sqlite':
            names = ('main',) + names[1:]

        # Check.
        if names[0] is None:
            throw(ValueError, names)

        return names


    @property
    def backend(self) -> str:
        """
        Database backend name.

        Returns
        -------
        Name.
        """

        # Get.
        url_params = extract_url(self.url)
        backend = url_params['backend']

        return backend


    @property
    def driver(self) -> str:
        """
        Database driver name.

        Returns
        -------
        Name.
        """

        # Get.
        url_params = extract_url(self.url)
        driver = url_params['driver']

        return driver


    @property
    def mode(self) -> Literal['server', 'file', 'memory']:
        """
        Database store mode.

        Returns
        -------
        Mode.
        """

        # Judge.
        if (
                self.username is not None
                and self.password is not None
                and self.host is not None
                and self.port is not None
        ):
            value = 'server'
        elif self.database not in (None, ':memory:'):
            value = 'file'
        else:
            value = 'memory'

        return value


    @property
    def url(self) -> str:
        """
        Generate server URL.

        Returns
        -------
        Server URL.
        """

        # Generate URL.

        ## Server.
        if self.mode == 'server':
            password = urllib_quote(self.password)
            url_ = f'mysql+pymysql://{self.username}:{password}@{self.host}:{self.port}'
            if self.database is not None:
                url_ = f'{url_}/{self.database}'

        ## File.
        elif self.mode == 'file':
            url_ = f'sqlite:///{self.database}'

        ## Memory.
        else:
            url_ = f'sqlite:///:memory:'

        # Add Server parameter.
        if self.query != {}:
            query = '&'.join(
                [
                    f'{key}={value}'
                    for key, value in self.query.items()
                ]
            )
            url_ = f'{url_}?{query}'

        return url_


    def __create_engine(self) -> Engine:
        """
        Create database `Engine` object.

        Returns
        -------
        Engine object.
        """

        # Handle parameter.
        if self.mode == 'memory':
            engine_params = {
                'url': self.url,
                'pool_recycle': self.pool_recycle
            }
        else:
            engine_params = {
                'url': self.url,
                'pool_size': self.pool_size,
                'max_overflow': self.max_overflow,
                'pool_timeout': self.pool_timeout,
                'pool_recycle': self.pool_recycle,
                'connect_args': {'client_flag': MULTI_STATEMENTS}
            }

        # Create Engine.
        engine = sqlalchemy_create_engine(**engine_params)

        return engine


    @property
    def count(self) -> tuple[int, int]:
        """
        Count number of keep open and allowed overflow connection.

        Returns
        -------
        Number of keep open and allowed overflow connection.
        """

        # Handle parameter.
        if hasattr(self, 'engine'):
            rdatabase = self
        else:
            rdatabase: Database = self.rdatabase

        # Count.
        _overflow = rdatabase.engine.pool._overflow
        if _overflow < 0:
            keep_n = rdatabase.pool_size + _overflow
            overflow_n = 0
        else:
            keep_n = rdatabase.pool_size
            overflow_n = _overflow

        return keep_n, overflow_n


    def handle_sql(self, sql: str | TextClause) -> TextClause:
        """
        Handle SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or TextClause object.

        Returns
        -------
        TextClause instance.
        """

        # Handle parameter.
        if type(sql) == TextClause:
            sql = sql.text

        # Handle.
        sql = sql.strip()
        if sql[-1] != ';':
            sql += ';'
        sql = sqlalchemy_text(sql)

        return sql


    def handle_data(
        self,
        data: list[dict],
        sql: str | TextClause,
    ) -> list[dict]:
        """
        Handle data based on the content of SQL.

        Parameters
        ----------
        data : Data set for filling.
        sql : SQL in method `sqlalchemy.text` format, or TextClause object.

        Returns
        -------
        Filled data.
        """

        # Handle parameter.
        if type(sql) == TextClause:
            sql = sql.text

        # Extract keys.
        pattern = '(?<!\\\\):(\\w+)'
        sql_keys = findall(pattern, sql)

        # Extract keys of syntax "in".
        pattern = '[iI][nN]\\s+(?<!\\\\):(\\w+)'
        sql_keys_in = findall(pattern, sql)

        # Loop.
        for row in data:
            if row == {}:
                continue
            for key in sql_keys:
                value = row.get(key)

                # Empty string.
                if value == '':
                    value = None

                # Convert.
                elif (
                    type(value) in (list, dict)
                    and key not in sql_keys_in
                ):
                    value = to_json(value)

                # Enum.
                elif isinstance(type(value), EnumType):
                    value = value.value

                row[key] = value

        return data


    def get_syntax(self, sql: str | TextClause) -> list[str]:
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
        if type(sql) == TextClause:
            sql = sql.text

        # Extract.
        syntax = [
            search('[a-zA-Z]+', sql_part).upper()
            for sql_part in sql.split(';')
            if sql_part != ''
        ]

        return syntax


    def is_multi_sql(self, sql: str | TextClause) -> bool:
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
        if type(sql) == TextClause:
            sql = sql.text

        # Judge.
        if ';' in sql.rstrip()[:-1]:
            return True
        return False


    def executor(
        self,
        connection: Connection,
        sql: TextClause,
        data: list[dict],
        report: bool
    ) -> Result:
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
                execute = wrap_runtime(connection.execute, to_return=True)
                result, report_runtime, *_ = execute(sql, data)
                report_info = (
                    f'{report_runtime}\n'
                    f'Row Count: {result.rowcount}'
                )
                sqls = [
                    sql_part.strip()
                    for sql_part in sql.text.split(';')
                    if sql_part != ''
                ]
                if data == []:
                    echo(report_info, *sqls, title='SQL')
                else:
                    echo(report_info, *sqls, data, title='SQL')

            ## Not report.
            else:
                result = connection.execute(sql, data)

        return result


    def execute(
        self,
        sql: str | TextClause,
        data: TableData | None = None,
        report: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Execute SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or `TextClause` object.
        data : Data set for filling.
        report : Whether report SQL execute information.
            - `None`: Use attribute `default_report`.
            - `bool`: Use this value.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.
        """

        # Handle parameter by priority.
        report = get_first_notnone(report, self.default_report)

        # Handle parameter.
        sql = self.handle_sql(sql)
        if data is None:
            if kwdata == {}:
                data = []
            else:
                data = [kwdata]
        else:
            data_table = Table(data)
            data = data_table.to_table()
            for row in data:
                row.update(kwdata)
        data = self.handle_data(data, sql)

        # Execute.

        ## Create Connection object.
        with self.engine.connect() as connection:

            ## Can retry.
            if (
                self.retry
                and not self.is_multi_sql(sql)
            ):
                text = 'Retrying...'
                title = 'Database Execute Operational Error'
                handler = lambda exc_text, *_: echo(exc_text, text, title=title, frame='top')
                executor = wrap_retry(self.executor, handler=handler, exception=OperationalError)
                result = executor(self.connection, sql, data, report)

            ## Cannot retry.
            else:
                result = self.executor(connection, sql, data, report)

        return result


    def execute_select(
        self,
        path: str | tuple[str, str],
        fields: str | Iterable[str] | None = None,
        where: str | None = None,
        group: str | None = None,
        having: str | None = None,
        order: str | None = None,
        limit: int | str | tuple[int, int] | None = None,
        report: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Execute select SQL.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str`: Automatic extract database name and table name.
            - `tuple[str, str]`: Database name and table name.
        fields : Select clause content.
            - `None`: Is `SELECT *`.
            - `str`: Join as `SELECT str`.
            - `Iterable[str]`, Join as `SELECT ``str``: ...`.
                `str and first character is ':'`: Use this syntax.
                `str`: Use this field.
        where : Clause `WHERE` content, join as `WHERE str`.
        group : Clause `GROUP BY` content, join as `GROUP BY str`.
        having : Clause `HAVING` content, join as `HAVING str`.
        order : Clause `ORDER BY` content, join as `ORDER BY str`.
        limit : Clause `LIMIT` content.
            - `int | str`: Join as `LIMIT int/str`.
            - `tuple[int, int]`: Join as `LIMIT int, int`.
        report : Whether report SQL execute information.
            - `None`, Use attribute `report_execute_info`: of object `ROption`.
            - `int`: Use this value.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `fields`.
        >>> fields = ['id', ':`id` + 1 AS `id_`']
        >>> result = Database.execute_select('database.table', fields)
        >>> print(result.to_table())
        [{'id': 1, 'id_': 2}, ...]

        Parameter `kwdata`.
        >>> fields = '`id`, `id` + :value AS `id_`'
        >>> result = Database.execute_select('database.table', fields, value=1)
        >>> print(result.to_table())
        [{'id': 1, 'id_': 2}, ...]
        """

        # Handle parameter.
        database, table, _ = self.extract_path(path)

        # Generate SQL.
        sql_list = []

        ## Part 'SELECT' syntax.
        if fields is None:
            fields = '*'
        elif type(fields) != str:
            fields = ', '.join(
                [
                    field[1:]
                    if (
                        field.startswith(':')
                        and field != ':'
                    )
                    else f'`{field}`'
                    for field in fields
                ]
            )
        sql_select = f'SELECT {fields}'
        sql_list.append(sql_select)

        ## Part 'FROM' syntax.
        sql_from = f'FROM `{database}`.`{table}`'
        sql_list.append(sql_from)

        ## Part 'WHERE' syntax.
        if where is not None:
            sql_where = f'WHERE {where}'
            sql_list.append(sql_where)

        ## Part 'GROUP BY' syntax.
        if group is not None:
            sql_group = f'GROUP BY {group}'
            sql_list.append(sql_group)

        ## Part 'GROUP BY' syntax.
        if having is not None:
            sql_having = f'HAVING {having}'
            sql_list.append(sql_having)

        ## Part 'ORDER BY' syntax.
        if order is not None:
            sql_order = f'ORDER BY {order}'
            sql_list.append(sql_order)

        ## Part 'LIMIT' syntax.
        if limit is not None:
            if type(limit) in (str, int):
                sql_limit = f'LIMIT {limit}'
            else:
                if len(limit) == 2:
                    sql_limit = f'LIMIT {limit[0]}, {limit[1]}'
                else:
                    throw(ValueError, limit)
            sql_list.append(sql_limit)

        ## Join sql part.
        sql = '\n'.join(sql_list)

        # Execute SQL.
        result = self.execute(sql, report=report, **kwdata)

        return result


    def execute_insert(
        self,
        path: str | tuple[str, str],
        data: TableData,
        duplicate: Literal['ignore', 'update'] | Container[str] | None = None,
        report: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Insert the data of table in the datebase.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str`: Automatic extract database name and table name.
            - `tuple[str, str]`: Database name and table name.
        data : Insert data.
        duplicate : Handle method when constraint error.
            - `None`: Not handled.
            - `ignore`: Use `UPDATE IGNORE INTO` clause.
            - `update`: Use `ON DUPLICATE KEY UPDATE` clause and update all fields.
            - `Container[str]`: Use `ON DUPLICATE KEY UPDATE` clause and update this fields.
        report : Whether report SQL execute information.
            - `None`, Use attribute `report_execute_info`: of object `ROption`.
            - `int`: Use this value.
        kwdata : Keyword parameters for filling.
            - `str and first character is ':'`: Use this syntax.
            - `Any`: Use this value.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `data` and `kwdata`.
        >>> data = [{'key': 'a'}, {'key': 'b'}]
        >>> kwdata = {'value1': 1, 'value2': ':(SELECT 2)'}
        >>> result = Database.execute_insert('database.table', data, **kwdata)
        >>> print(result.rowcount)
        2
        >>> result = Database.execute_select('database.table')
        >>> print(result.to_table())
        [{'key': 'a', 'value1': 1, 'value2': 2}, {'key': 'b', 'value1': 1, 'value2': 2}]
        """

        # Handle parameter.
        database, table, _ = self.extract_path(path)

        # Handle parameter.

        ## Data.
        data_table = Table(data)
        data = data_table.to_table()

        ## Check.
        if data in ([], [{}]):
            throw(ValueError, data)

        ## Keyword data.
        kwdata_method = {}
        kwdata_replace = {}
        for key, value in kwdata.items():
            if (
                type(value) == str
                and value.startswith(':')
                and value != ':'
            ):
                kwdata_method[key] = value[1:]
            else:
                kwdata_replace[key] = value

        # Generate SQL.

        ## Part 'fields' syntax.
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
        sql_fields = ', '.join(
            [
                f'`{field}`'
                for field in sql_fields_list
            ]
        )

        ## Part 'values' syntax.
        sql_values_list = (
            *kwdata_method.values(),
            *[
                ':' + field
                for field in (
                    *kwdata_replace,
                    *fields_replace
                )
            ]
        )
        sql_values = ', '.join(sql_values_list)

        ## Join sql part.
        match duplicate:

            ### Not handle.
            case None:
                sql = (
                    f'INSERT INTO `{database}`.`{table}`({sql_fields})\n'
                    f'VALUES({sql_values})'
                )

            ### Ignore.
            case 'ignore':
                sql = (
                    f'INSERT IGNORE INTO `{database}`.`{table}`({sql_fields})\n'
                    f'VALUES({sql_values})'
                )

            ### Update.
            case _:
                sql_fields_list_update = sql_fields_list
                if duplicate != 'update':
                    sql_fields_list_update = [
                        field
                        for field in sql_fields_list
                        if field in duplicate
                    ]
                update_content = ',\n    '.join(
                    [
                        f'`{field}` = VALUES(`{field}`)'
                        for field in sql_fields_list_update
                    ]
                )
                sql = (
                    f'INSERT INTO `{database}`.`{table}`({sql_fields})\n'
                    f'VALUES({sql_values})\n'
                    'ON DUPLICATE KEY UPDATE\n'
                    f'    {update_content}'
                )

        # Execute SQL.
        result = self.execute(sql, data, report, **kwdata_replace)

        return result


    def execute_update(
        self,
        path: str | tuple[str, str],
        data: TableData,
        where_fields: str | Iterable[str] | None = None,
        report: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Update the data of table in the datebase.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str`: Automatic extract database name and table name.
            - `tuple[str, str]`: Database name and table name.
        data : Update data, clause `SET` and `WHERE` and `ORDER BY` and `LIMIT` content.
            - `Key`: Table field.
                `literal['order']`: Clause `ORDER BY` content, join as `ORDER BY str`.
                `literal['limit']`: Clause `LIMIT` content, join as `LIMIT str`.
                `Other`: Clause `SET` and `WHERE` content.
            - `Value`: Table value.
                `list | tuple`: Join as `field IN :str`.
                `Any`: Join as `field = :str`.
        where_fields : Clause `WHERE` content fields.
            - `None`: The first key value pair of each item is judged.
            - `str`: This key value pair of each item is judged.
            - `Iterable[str]`: Multiple judged, `and`: relationship.
        report : Whether report SQL execute information.
            - `None`, Use attribute `report_execute_info`: of object `ROption`.
            - `int`: Use this value.
        kwdata : Keyword parameters for filling.
            - `str and first character is ':'`: Use this syntax.
            - `Any`: Use this value.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `data` and `kwdata`.
        >>> data = [{'key': 'a'}, {'key': 'b'}]
        >>> kwdata = {'value': 1, 'name': ':`key`'}
        >>> result = Database.execute_update('database.table', data, **kwdata)
        >>> print(result.rowcount)
        2
        >>> result = Database.execute_select('database.table')
        >>> print(result.to_table())
        [{'key': 'a', 'value': 1, 'name': 'a'}, {'key': 'b', 'value': 1, 'name': 'b'}]
        """

        # Handle parameter.
        database, table, _ = self.extract_path(path)

        # Handle parameter.

        ## Data.
        data_table = Table(data)
        data = data_table.to_table()

        ## Check.
        if data in ([], [{}]):
            throw(ValueError, data)

        ## Keyword data.
        kwdata_method = {}
        kwdata_replace = {}
        for key, value in kwdata.items():
            if (
                type(value) == str
                and value.startswith(':')
                and value != ':'
            ):
                kwdata_method[key] = value[1:]
            else:
                kwdata_replace[key] = value
        sql_set_list_kwdata = [
            f'`{key}` = {value}'
            for key, value in kwdata_method.items()
        ]
        sql_set_list_kwdata.extend(
            [
                f'`{key}` = :{key}'
                for key in kwdata_replace
            ]
        )

        # Generate SQL.
        data_flatten = kwdata_replace
        if where_fields is None:
            no_where = True
        else:
            no_where = False
            if type(where_fields) == str:
                where_fields = [where_fields]
        sqls_list = []
        sql_update = f'UPDATE `{database}`.`{table}`'
        for index, row in enumerate(data):
            sql_parts = [sql_update]
            for key, value in row.items():
                if key in ('order', 'limit'):
                    continue
                index_key = f'{index}_{key}'
                data_flatten[index_key] = value
            if no_where:
                for key in row:
                    where_fields = [key]
                    break

            ## Part 'SET' syntax.
            sql_set_list = sql_set_list_kwdata.copy()
            sql_set_list.extend(
                [
                    f'`{key}` = :{index}_{key}'
                    for key in row
                    if (
                        key not in where_fields
                        and key not in kwdata
                        and key not in ('order', 'limit')
                    )
                ]
            )
            sql_set = 'SET ' + ',\n    '.join(sql_set_list)
            sql_parts.append(sql_set)

            ## Part 'WHERE' syntax.
            sql_where_list = []
            for field in where_fields:
                index_field = f'{index}_{field}'
                index_value = data_flatten[index_field]
                if type(index_value) in (list, tuple):
                    sql_where_part = f'`{field}` IN :{index_field}'
                else:
                    sql_where_part = f'`{field}` = :{index_field}'
                sql_where_list.append(sql_where_part)
            sql_where = 'WHERE ' + '\n    AND '.join(sql_where_list)
            sql_parts.append(sql_where)

            ## Part 'ORDER BY' syntax.
            order = row.get('order')
            if order is not None:
                sql_order = f'ORDER BY {order}'
                sql_parts.append(sql_order)

            ## Part 'LIMIT' syntax.
            limit = row.get('limit')
            if limit is not None:
                sql_limit = f'LIMIT {limit}'
                sql_parts.append(sql_limit)

            ## Join sql part.
            sql = '\n'.join(sql_parts)
            sqls_list.append(sql)

        ## Join sqls.
        sqls = ';\n'.join(sqls_list)

        # Execute SQL.
        result = self.execute(sqls, data_flatten, report)

        return result


    def execute_delete(
        self,
        path: str | tuple[str, str],
        where: str | None = None,
        order: str | None = None,
        limit: int | str | None = None,
        report: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Delete the data of table in the datebase.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str`: Automatic extract database name and table name.
            - `tuple[str, str]`: Database name and table name.
        where : Clause `WHERE` content, join as `WHERE str`.
        order : Clause `ORDER BY` content, join as `ORDER BY str`.
        limit : Clause `LIMIT` content, join as `LIMIT int/str`.
        report : Whether report SQL execute information.
            - `None`, Use attribute `report_execute_info`: of object `ROption`.
            - `int`: Use this value.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `where` and `kwdata`.
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2)
        >>> result = Database.execute_delete('database.table', where, ids=ids)
        >>> print(result.rowcount)
        2
        """

        # Handle parameter.
        database, table, _ = self.extract_path(path)

        # Generate SQL.
        sqls = []

        ## Part 'DELETE' syntax.
        sql_delete = f'DELETE FROM `{database}`.`{table}`'
        sqls.append(sql_delete)

        ## Part 'WHERE' syntax.
        if where is not None:
            sql_where = f'WHERE {where}'
            sqls.append(sql_where)

        ## Part 'ORDER BY' syntax.
        if order is not None:
            sql_order = f'ORDER BY {order}'
            sqls.append(sql_order)

        ## Part 'LIMIT' syntax.
        if limit is not None:
            sql_limit = f'LIMIT {limit}'
            sqls.append(sql_limit)

        ## Join sqls.
        sqls = '\n'.join(sqls)

        # Execute SQL.
        result = self.execute(sqls, report=report, **kwdata)

        return result


    def execute_copy(
        self,
        path: str | tuple[str, str],
        where: str | None = None,
        limit: int | str | tuple[int, int] | None = None,
        report: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Copy record of table in the datebase.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str`: Automatic extract database name and table name.
            - `tuple[str, str]`: Database name and table name.
        where : Clause `WHERE` content, join as `WHERE str`.
        limit : Clause `LIMIT` content.
            - `int | str`: Join as `LIMIT int/str`.
            - `tuple[int, int]`: Join as `LIMIT int, int`.
        report : Whether report SQL execute information.
            - `None`, Use attribute `report_execute_info`: of object `ROption`.
            - `int`: Use this value.
        kwdata : Keyword parameters for filling.
            - `In 'WHERE' syntax`: Fill 'WHERE' syntax.
            - `Not in 'WHERE' syntax`: Fill 'INSERT' and 'SELECT' syntax.
                `str and first character is ':'`: Use this syntax.
                `Any`: Use this value.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `where` and `kwdata`.
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2, 3)
        >>> result = Database.execute_copy('database.table', where, 2, ids=ids, id=None, time=':NOW()')
        >>> print(result.rowcount)
        2
        """

        # Handle parameter.
        database, table, _ = self.extract_path(path)
        table_info: list[dict] = self.info(database)(table)()

        ## SQLite.
        if self.backend == 'sqlite':
            field_key = 'name'

        ## Other.
        else:
            field_key = 'COLUMN_NAME'

        fields = [
            row[field_key]
            for row in table_info
        ]
        pattern = '(?<!\\\\):(\\w+)'
        if type(where) == str:
            where_keys = findall(pattern, where)
        else:
            where_keys = ()

        # Generate SQL.
        sqls = []

        ## Part 'INSERT' syntax.
        sql_fields = ', '.join(
            f'`{field}`'
            for field in fields
            if field not in kwdata
        )
        if kwdata != {}:
            sql_fields_kwdata = ', '.join(
                f'`{field}`'
                for field in kwdata
                if field not in where_keys
            )
            sql_fields_filter = filter(
                lambda sql: sql != '',
                (
                    sql_fields,
                    sql_fields_kwdata
                )
            )
            sql_fields = ', '.join(sql_fields_filter)
        sql_insert = f'INSERT INTO `{database}`.`{table}`({sql_fields})'
        sqls.append(sql_insert)

        ## Part 'SELECT' syntax.
        sql_values = ', '.join(
            f'`{field}`'
            for field in fields
            if field not in kwdata
        )
        if kwdata != {}:
            sql_values_kwdata = ', '.join(
                value[1:]
                if (
                    type(value) == str
                    and value.startswith(':')
                    and value != ':'
                )
                else f':{field}'
                for field, value in kwdata.items()
                if field not in where_keys
            )
            sql_values_filter = filter(
                lambda sql: sql != '',
                (
                    sql_values,
                    sql_values_kwdata
                )
            )
            sql_values = ', '.join(sql_values_filter)
        sql_select = (
            f'SELECT {sql_values}\n'
            f'FROM `{database}`.`{table}`'
        )
        sqls.append(sql_select)

        ## Part 'WHERE' syntax.
        if where is not None:
            sql_where = f'WHERE {where}'
            sqls.append(sql_where)

        ## Part 'LIMIT' syntax.
        if limit is not None:
            if type(limit) in (str, int):
                sql_limit = f'LIMIT {limit}'
            else:
                if len(limit) == 2:
                    sql_limit = f'LIMIT {limit[0]}, {limit[1]}'
                else:
                    throw(ValueError, limit)
            sqls.append(sql_limit)

        ## Join.
        sql = '\n'.join(sqls)

        # Execute SQL.
        result = self.execute(sql, report=report, **kwdata)

        return result


    def execute_count(
        self,
        path: str | tuple[str, str],
        where: str | None = None,
        report: bool | None = None,
        **kwdata: Any
    ) -> int:
        """
        Count records.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str`: Automatic extract database name and table name.
            - `tuple[str, str]`: Database name and table name.
        where : Match condition, `WHERE` clause content, join as `WHERE str`.
            - `None`: Match all.
            - `str`: Match condition.
        report : Whether report SQL execute information.
            - `None`, Use attribute `report_execute_info`: of object `ROption`.
            - `int`: Use this value.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Record count.

        Examples
        --------
        Parameter `where` and `kwdata`.
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2)
        >>> result = Database.execute_count('database.table', where, ids=ids)
        >>> print(result)
        2
        """

        # Handle parameter.
        database, table, _ = self.extract_path(path)

        # Execute.
        result = self.execute_select((database, table), '1', where=where, report=report, **kwdata)
        count = len(tuple(result))

        return count


    def execute_exist(
        self,
        path: str | tuple[str, str],
        where: str | None = None,
        report: bool | None = None,
        **kwdata: Any
    ) -> bool:
        """
        Judge the exist of record.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.database`.
            - `str`: Automatic extract database name and table name.
            - `tuple[str, str]`: Database name and table name.
        where : Match condition, `WHERE` clause content, join as `WHERE str`.
            - `None`: Match all.
            - `str`: Match condition.
        report : Whether report SQL execute information.
            - `None`, Use attribute `report_execute_info`: of object `ROption`.
            - `int`: Use this value.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Judged result.

        Examples
        --------
        Parameter `where` and `kwdata`.
        >>> data = [{'id': 1}]
        >>> Database.execute_insert('database.table', data)
        >>> where = '`id` = :id_'
        >>> id_ = 1
        >>> result = Database.execute_exist('database.table', where, id_=id_)
        >>> print(result)
        True
        """

        # Handle parameter.
        database, table, _ = self.extract_path(path)

        # Execute.
        result = self.execute_count(path, where, report, **kwdata)

        # Judge.
        judge = result != 0

        return judge


    def execute_generator(
        self,
        sql: str | TextClause,
        data: TableData,
        report: bool | None = None,
        **kwdata: Any
    ) -> Generator[Result, Any, None]:
        """
        Return a generator that can execute SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or `TextClause` object.
        data : Data set for filling.
        report : Whether report SQL execute information.
            - `None`: Use attribute `default_report`.
            - `bool`: Use this value.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Generator.
        """

        # Instance.
        generator = Generator(
            self.execute,
            sql=sql,
            report=report,
            **kwdata
        )

        # Add.
        for row in data:
            generator(**row)

        return generator.generator


    def connect(self):
        """
        Build `DatabaseConnection` instance.

        Returns
        -------
        Database connection instance.
        """

        # Import.
        from .rconn import DatabaseConnection

        # Build.
        dbconnection = DatabaseConnection(
            self.engine.connect(),
            self
        )

        return dbconnection


    @property
    def exe(self):
        """
        Build `database path` instance.

        Returns
        -------
        Instance.

        Examples
        --------
        Execute.
        >>> sql = 'select :value'
        >>> result = DatabaseExecute(sql, value=1)

        Select.
        >>> field = ['id', 'value']
        >>> where = '`id` = ids'
        >>> ids = (1, 2)
        >>> result = DatabaseExecute.database.table(field, where, ids=ids)

        Insert.
        >>> data = [{'id': 1}, {'id': 2}]
        >>> duplicate = 'ignore'
        >>> result = DatabaseExecute.database.table + data
        >>> result = DatabaseExecute.database.table + (data, duplicate)
        >>> result = DatabaseExecute.database.table + {'data': data, 'duplicate': duplicate}

        Update.
        >>> data = [{'name': 'a', 'id': 1}, {'name': 'b', 'id': 2}]
        >>> where_fields = 'id'
        >>> result = DatabaseExecute.database.table & data
        >>> result = DatabaseExecute.database.table & (data, where_fields)
        >>> result = DatabaseExecute.database.table & {'data': data, 'where_fields': where_fields}

        Delete.
        >>> where = '`id` IN (1, 2)'
        >>> report = True
        >>> result = DatabaseExecute.database.table - where
        >>> result = DatabaseExecute.database.table - (where, report)
        >>> result = DatabaseExecute.database.table - {'where': where, 'report': report}

        Copy.
        >>> where = '`id` IN (1, 2)'
        >>> limit = 1
        >>> result = DatabaseExecute.database.table * where
        >>> result = DatabaseExecute.database.table * (where, limit)
        >>> result = DatabaseExecute.database.table * {'where': where, 'limit': limit}

        Exist.
        >>> where = '`id` IN (1, 2)'
        >>> report = True
        >>> result = where in DatabaseExecute.database.table
        >>> result = (where, report) in DatabaseExecute.database.table
        >>> result = {'where': where, 'report': report} in DatabaseExecute.database.table

        Count.
        >>> result = len(DatabaseExecute.database.table)

        Default database.
        >>> field = ['id', 'value']
        >>> engine = Database(**server, database)
        >>> result = engine.exe.table()
        """

        # Import.
        from .rexec import DatabaseExecute

        # Build.
        dbexecute = DatabaseExecute(self)

        return dbexecute


    def schema(self, filter_default: bool = True) -> dict[str, dict[str, list[str]]]:
        """
        Get schemata of databases and tables and columns.

        Parameters
        ----------
        filter_default : Whether filter default database.

        Returns
        -------
        Schemata of databases and tables and columns.
        """

        # Check.
        if self.backend == 'sqlite':
            text = 'not suitable for SQLite databases'
            throw(AssertionError, text=text)

        # Handle parameter.
        filter_db = (
            'information_schema',
            'performance_schema',
            'mysql',
            'sys'
        )
        if filter_default:
            where_database = 'WHERE `SCHEMA_NAME` NOT IN :filter_db\n'
            where_column = '    WHERE `TABLE_SCHEMA` NOT IN :filter_db\n'
        else:
            where_database = where_column = ''

        # Select.
        sql = (
            'SELECT GROUP_CONCAT(`SCHEMA_NAME`) AS `TABLE_SCHEMA`, NULL AS `TABLE_NAME`, NULL AS `COLUMN_NAME`\n'
            'FROM `information_schema`.`SCHEMATA`\n'
            f'{where_database}'
            'UNION ALL (\n'
            '    SELECT `TABLE_SCHEMA`, `TABLE_NAME`, `COLUMN_NAME`\n'
            '    FROM `information_schema`.`COLUMNS`\n'
            f'{where_column}'
            '    ORDER BY `TABLE_SCHEMA`, `TABLE_NAME`, `ORDINAL_POSITION`\n'
            ')'
        )
        result = self.execute(sql, filter_db=filter_db)

        # Convert.
        database_names, *_ = result.fetchone()
        database_names: list[str] = database_names.split(',')
        schema_dict = {}
        for database, table, column in result:
            if database in database_names:
                database_names.remove(database)

            ## Index database.
            if database not in schema_dict:
                schema_dict[database] = {table: [column]}
                continue
            table_dict: dict = schema_dict[database]

            ## Index table. 
            if table not in table_dict:
                table_dict[table] = [column]
                continue
            column_list: list = table_dict[table]

            ## Add column.
            column_list.append(column)

        ## Add empty database.
        for database_name in database_names:
            schema_dict[database_name] = None

        return schema_dict


    @property
    def info(self):
        """
        Build `DatabaseInformationSchema` instance.

        Returns
        -------
        Database schema information instance.

        Examples
        --------
        Get databases information of server.
        >>> databases_info = DatabaseInformationSchema()

        Get tables information of database.
        >>> tables_info = DatabaseInformationSchema.database()

        Get columns information of table.
        >>> columns_info = DatabaseInformationSchema.database.table()

        Get database attribute.
        >>> database_attr = DatabaseInformationSchema.database['attribute']

        Get table attribute.
        >>> database_attr = DatabaseInformationSchema.database.table['attribute']

        Get column attribute.
        >>> database_attr = DatabaseInformationSchema.database.table.column['attribute']
        """

        # Import.
        from .rinfo import DatabaseInformationSchema

        # Build.
        dbischema = DatabaseInformationSchema(self)

        return dbischema


    @property
    def build(self):
        """
        Build `DatabaseBuild` instance.

        Returns
        -------
        Database build instance.
        """

        # Import.
        from .rbuild import DatabaseBuild

        # Build.
        dbbuild = DatabaseBuild(self)

        return dbbuild


    @property
    def file(self):
        """
        Build `DatabaseFile` instance.

        Returns
        -------
        Database file instance.
        """

        # Import.
        from .rfile import DatabaseFile

        # Build.
        dbfile = DatabaseFile(self)

        return dbfile


    @property
    def error(self):
        """
        Build `DatabaseError` instance.

        Returns
        -------
        Database file instance.
        """

        # Import.
        from .rerror import DatabaseError

        # Build.
        dbfile = DatabaseError(self)

        return dbfile


    @property
    def config(self):
        """
        Build `DatabaseConfig` instance.

        Returns
        -------
        Database file instance.
        """

        # Import.
        from .rconfig import DatabaseConfig

        # Build.
        dbconfig = DatabaseConfig(self)

        return dbconfig


    @property
    def status(self):
        """
        Build `DatabaseParametersStatus` or `DatabaseParametersPragma` instance.

        Returns
        -------
        Database status parameters instance.
        """

        # Import.
        from .rparam import DatabaseParametersStatus, DatabaseParametersPragma

        # Build.

        ## SQLite.
        if self.backend == 'sqlite':
            dbp = DatabaseParametersPragma(self)

        ## Other.
        else:
            dbp = DatabaseParametersStatus(self, False)

        return dbp


    @property
    def global_status(self):
        """
        Build `DatabaseParametersStatus` or `DatabaseParametersPragma` instance.

        Returns
        -------
        Global database status parameters instance.
        """

        # Import.
        from .rparam import DatabaseParametersStatus, DatabaseParametersPragma

        # Build.

        ## SQLite.
        if self.backend == 'sqlite':
            dbp = DatabaseParametersPragma(self)

        ## Other.
        else:
            dbp = DatabaseParametersStatus(self, True)

        return dbp


    @property
    def variables(self):
        """
        Build `DatabaseParametersVariable` or `DatabaseParametersPragma` instance.

        Returns
        -------
        Database variable parameters instance.
        """

        # Import.
        from .rparam import DatabaseParametersVariable, DatabaseParametersPragma

        # Build.

        ## SQLite.
        if self.backend == 'sqlite':
            dbp = DatabaseParametersPragma(self)

        ## Other.
        else:
            dbp = DatabaseParametersVariable(self, False)

        return dbp


    @property
    def global_variables(self):
        """
        Build global `database variable parameters` instance.

        Returns
        -------
        Global database variable parameters instance.
        """

        # Import.
        from .rparam import DatabaseParametersVariable, DatabaseParametersPragma

        # Build.

        ## SQLite.
        if self.backend == 'sqlite':
            dbp = DatabaseParametersPragma(self)

        ## Other.
        else:
            dbp = DatabaseParametersVariable(self, True)

        return dbp


    __call__ = execute


    def __str__(self) -> str:
        """
        Return connection information text.
        """

        # Handle parameter.
        if hasattr(self, 'engine'):
            attr_dict = self.__dict__
        else:
            rdatabase: Database = self.rdatabase
            attr_dict = {
                **self.__dict__,
                **rdatabase.__dict__
            }

        # Generate.
        filter_key = (
            'engine',
            'connection',
            'rdatabase',
            'begin'
        )
        info = {
            key: value
            for key, value in attr_dict.items()
            if key not in filter_key
        }
        info['count'] = self.count
        text = join_data_text(info)

        return text
