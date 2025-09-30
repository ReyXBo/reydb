# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-09-22 22:12:33
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Execute methods.
"""


from typing import Any, Literal, TypeVar, Generic, overload
from collections.abc import Iterable, Generator, AsyncGenerator, Container
from datetime import timedelta as Timedelta
from sqlalchemy.sql.elements import TextClause
from reykit.rbase import throw, get_first_notnone
from reykit.rdata import FunctionGenerator
from reykit.rmonkey import monkey_sqlalchemy_result_more_fetch, monkey_sqlalchemy_row_index_field
from reykit.rrand import randn
from reykit.rre import findall
from reykit.rstdout import echo as recho
from reykit.rtable import TableData, Table
from reykit.rtime import TimeMark, time_to
from reykit.rwrap import wrap_runtime

from . import rconn
from .rbase import DatabaseBase, handle_sql, handle_data


__all__ = (
    'Result',
    'DatabaseExecuteSuper',
    'DatabaseExecute',
    'DatabaseExecuteAsync'
)


# Monkey path.
Result_ = monkey_sqlalchemy_result_more_fetch()
Result = Result_
monkey_sqlalchemy_row_index_field()


DatabaseConnectionT = TypeVar('DatabaseConnectionT', 'rconn.DatabaseConnection', 'rconn.DatabaseConnectionAsync')


class DatabaseExecuteSuper(DatabaseBase, Generic[DatabaseConnectionT]):
    """
    Database execute super type.
    """


    def __init__(self, dbconn: DatabaseConnectionT) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        dbconn : `DatabaseConnection` or `DatabaseConnectionAsync`instance.
        """

        # Build.
        self.conn = dbconn


    def handle_execute(
        self,
        sql: str | TextClause,
        data: TableData | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> tuple[TextClause, list[dict], bool]:
        """
        Handle method of execute SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or `TextClause` object.
        data : Data set for filling.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
            - `bool`: Use this value.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Parameter `sql` and `data` and `report`.
        """

        # Handle parameter.
        echo = get_first_notnone(echo, self.conn.db.echo)
        sql = handle_sql(sql)
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
        data = handle_data(data, sql)

        return sql, data, echo


    def handle_select(
        self,
        path: str | tuple[str, str],
        fields: str | Iterable[str] | None = None,
        where: str | None = None,
        group: str | None = None,
        having: str | None = None,
        order: str | None = None,
        limit: int | str | tuple[int, int] | None = None
    ) -> str:
        """
        Handle method of execute select SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
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

        Returns
        -------
        Parameter `sql`.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.conn.db.database, path
        else:
            database, table = path

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

        return sql


    def handle_insert(
        self,
        path: str | tuple[str, str],
        data: TableData,
        duplicate: Literal['ignore', 'update'] | Container[str] | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Handle method of execute insert SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        data : Insert data.
        duplicate : Handle method when constraint error.
            - `None`: Not handled.
            - `ignore`: Use `UPDATE IGNORE INTO` clause.
            - `update`: Use `ON DUPLICATE KEY UPDATE` clause and update all fields.
            - `Container[str]`: Use `ON DUPLICATE KEY UPDATE` clause and update this fields.
        kwdata : Keyword parameters for filling.
            - `str and first character is ':'`: Use this syntax.
            - `Any`: Use this value.

        Returns
        -------
        Parameter `sql` and `kwdata`.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.conn.db.database, path
        else:
            database, table = path

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

        return sql, kwdata_replace


    def handle_update(
        self,
        path: str | tuple[str, str],
        data: TableData,
        where_fields: str | Iterable[str] | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Execute update SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
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
        kwdata : Keyword parameters for filling.
            - `str and first character is ':'`: Use this syntax.
            - `Any`: Use this value.

        Returns
        -------
        Parameter `sql` and `data`.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.conn.db.database, path
        else:
            database, table = path

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

        return sqls, data_flatten


    def handle_delete(
        self,
        path: str | tuple[str, str],
        where: str | None = None,
        order: str | None = None,
        limit: int | str | None = None
    ) -> Result:
        """
        Execute delete SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        where : Clause `WHERE` content, join as `WHERE str`.
        order : Clause `ORDER BY` content, join as `ORDER BY str`.
        limit : Clause `LIMIT` content, join as `LIMIT int/str`.

        Returns
        -------
        Parameter `sql`.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.conn.db.database, path
        else:
            database, table = path

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

        return sqls


    def handle_copy(
        self,
        path: str | tuple[str, str],
        fields: str | Iterable[str] | None = None,
        where: str | None = None,
        limit: int | str | tuple[int, int] | None = None
    ) -> Result:
        """
        Execute inesrt SQL of copy records.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        fields : Select clause content.
            - `None`: Is `SELECT *`.
            - `str`: Join as `SELECT str`.
            - `Iterable[str]`: Join as `SELECT str`.
        where : Clause `WHERE` content, join as `WHERE str`.
        limit : Clause `LIMIT` content.
            - `int | str`: Join as `LIMIT int/str`.
            - `tuple[int, int]`: Join as `LIMIT int, int`.

        Returns
        -------
        Parameter `sql`.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.conn.db.database, path
        else:
            database, table = path
        if fields is None:
            fields = '*'
        elif type(fields) != str:
            fields = ', '.join(fields)

        # Generate SQL.
        sqls = []

        ## Part 'INSERT' syntax.
        sql_insert = f'INSERT INTO `{database}`.`{table}`'
        if fields != '*':
            sql_insert += f'({fields})'
        sqls.append(sql_insert)

        ## Part 'SELECT' syntax.
        sql_select = (
            f'SELECT {fields}\n'
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

        return sql


class DatabaseExecute(DatabaseExecuteSuper['rconn.DatabaseConnection']):
    """
    Database execute type.
    """


    def execute(
        self,
        sql: str | TextClause,
        data: TableData | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Execute SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or `TextClause` object.
        data : Data set for filling.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
            - `bool`: Use this value.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.
        """

        # Handle parameter.
        sql, data, echo = self.handle_execute(sql, data, echo, **kwdata)

        # Transaction.
        self.conn.get_begin()

        # Execute.

        ## Report.
        if echo:
            execute = wrap_runtime(self.conn.connection.execute, to_return=True, to_print=False)
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
                recho(report_info, *sqls, title='SQL')
            else:
                recho(report_info, *sqls, data, title='SQL')

        ## Not report.
        else:
            result = self.conn.connection.execute(sql, data)

        # Automatic commit.
        if self.conn.autocommit:
            self.conn.commit()
            self.conn.close()

        return result


    __call__ = execute


    def select(
        self,
        path: str | tuple[str, str],
        fields: str | Iterable[str] | None = None,
        where: str | None = None,
        group: str | None = None,
        having: str | None = None,
        order: str | None = None,
        limit: int | str | tuple[int, int] | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Execute select SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
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
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `fields`.
        >>> fields = ['id', ':`id` + 1 AS `id_`']
        >>> result = Database.execute.select('table', fields)
        >>> print(result.to_table())
        [{'id': 1, 'id_': 2}, ...]

        Parameter `kwdata`.
        >>> fields = '`id`, `id` + :value AS `id_`'
        >>> result = Database.execute.select('table', fields, value=1)
        >>> print(result.to_table())
        [{'id': 1, 'id_': 2}, ...]
        """

        # Handle parameter.
        sql = self.handle_select(path, fields, where, group, having, order, limit)

        # Execute SQL.
        result = self.execute(sql, echo=echo, **kwdata)

        return result


    def insert(
        self,
        path: str | tuple[str, str],
        data: TableData,
        duplicate: Literal['ignore', 'update'] | Container[str] | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Execute insert SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        data : Insert data.
        duplicate : Handle method when constraint error.
            - `None`: Not handled.
            - `ignore`: Use `UPDATE IGNORE INTO` clause.
            - `update`: Use `ON DUPLICATE KEY UPDATE` clause and update all fields.
            - `Container[str]`: Use `ON DUPLICATE KEY UPDATE` clause and update this fields.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.
            - `str and first character is ':'`: Use this syntax.
            - `Any`: Use this value.

        Returns
        -------
        Result object.

        Examples
        --------
        >>> data = [{'key': 'a'}, {'key': 'b'}]
        >>> kwdata = {'value1': 1, 'value2': ':(SELECT 2)'}
        >>> result = Database.execute.insert('table', data, **kwdata)
        >>> print(result.rowcount)
        2
        >>> result = Database.execute.select('table')
        >>> print(result.to_table())
        [{'key': 'a', 'value1': 1, 'value2': 2}, {'key': 'b', 'value1': 1, 'value2': 2}]
        """

        # Handle parameter.
        sql, kwdata = self.handle_insert(path, data, duplicate, **kwdata)

        # Execute SQL.
        result = self.execute(sql, data, echo, **kwdata)

        return result


    def update(
        self,
        path: str | tuple[str, str],
        data: TableData,
        where_fields: str | Iterable[str] | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Execute update SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
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
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.
            - `str and first character is ':'`: Use this syntax.
            - `Any`: Use this value.

        Returns
        -------
        Result object.

        Examples
        --------
        >>> data = [{'key': 'a'}, {'key': 'b'}]
        >>> kwdata = {'value': 1, 'name': ':`key`'}
        >>> result = Database.execute.update('table', data, **kwdata)
        >>> print(result.rowcount)
        2
        >>> result = Database.execute.select('table')
        >>> print(result.to_table())
        [{'key': 'a', 'value': 1, 'name': 'a'}, {'key': 'b', 'value': 1, 'name': 'b'}]
        """

        # Handle parameter.
        sql, data = self.handle_update(path, data, where_fields, **kwdata)

        # Execute SQL.
        result = self.execute(sql, data, echo)

        return result


    def delete(
        self,
        path: str | tuple[str, str],
        where: str | None = None,
        order: str | None = None,
        limit: int | str | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Execute delete SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        where : Clause `WHERE` content, join as `WHERE str`.
        order : Clause `ORDER BY` content, join as `ORDER BY str`.
        limit : Clause `LIMIT` content, join as `LIMIT int/str`.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.

        Examples
        --------
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2)
        >>> result = Database.execute.delete('table', where, ids=ids)
        >>> print(result.rowcount)
        2
        """

        # Handle parameter.
        sql = self.handle_delete(path, where, order, limit)

        # Execute SQL.
        result = self.execute(sql, echo=echo, **kwdata)

        return result


    def copy(
        self,
        path: str | tuple[str, str],
        fields: str | Iterable[str] | None = None,
        where: str | None = None,
        limit: int | str | tuple[int, int] | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Execute inesrt SQL of copy records.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        fields : Select clause content.
            - `None`: Is `SELECT *`.
            - `str`: Join as `SELECT str`.
            - `Iterable[str]`: Join as `SELECT str`.
        where : Clause `WHERE` content, join as `WHERE str`.
        limit : Clause `LIMIT` content.
            - `int | str`: Join as `LIMIT int/str`.
            - `tuple[int, int]`: Join as `LIMIT int, int`.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.

        Examples
        --------
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2, 3)
        >>> result = Database.execute.copy('table', where, 2, ids=ids, id=None, time=':NOW()')
        >>> print(result.rowcount)
        2
        """

        # Handle parameter.
        sql = self.handle_copy(path, fields, where, limit)

        # Execute SQL.
        result = self.execute(sql, echo=echo, **kwdata)

        return result


    def count(
        self,
        path: str | tuple[str, str],
        where: str | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> int:
        """
        Execute inesrt SQL of count records.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        where : Match condition, `WHERE` clause content, join as `WHERE str`.
            - `None`: Match all.
            - `str`: Match condition.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Record count.

        Examples
        --------
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2)
        >>> result = Database.execute.count('table', where, ids=ids)
        >>> print(result)
        2
        """

        # Execute.
        result = self.select(path, '1', where=where, echo=echo, **kwdata)
        count = len(tuple(result))

        return count


    def exist(
        self,
        path: str | tuple[str, str],
        where: str | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> bool:
        """
        Execute inesrt SQL of Judge the exist of record.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        where : Match condition, `WHERE` clause content, join as `WHERE str`.
            - `None`: Match all.
            - `str`: Match condition.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Judged result.

        Examples
        --------
        >>> data = [{'id': 1}]
        >>> Database.execute.insert('table', data)
        >>> where = '`id` = :id_'
        >>> id_ = 1
        >>> result = Database.execute.exist('table', where, id_=id_)
        >>> print(result)
        True
        """

        # Execute.
        result = self.count(path, where, echo, **kwdata)

        # Judge.
        judge = result != 0

        return judge


    def generator(
        self,
        sql: str | TextClause,
        data: TableData,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Generator[Result, Any, None]:
        """
        Return a generator that can execute SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or `TextClause` object.
        data : Data set for filling.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
            - `bool`: Use this value.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Generator.
        """

        # Instance.
        func_generator = FunctionGenerator(
            self.execute,
            sql=sql,
            echo=echo,
            **kwdata
        )

        # Add.
        for row in data:
            func_generator(**row)

        # Create.
        generator = func_generator.generator()

        return generator


    @overload
    def sleep(self, echo: bool | None = None) -> int: ...

    @overload
    def sleep(self, second: int, echo: bool | None = None) -> int: ...

    @overload
    def sleep(self, low: int = 0, high: int = 10, echo: bool | None = None) -> int: ...

    @overload
    def sleep(self, *thresholds: float, echo: bool | None = None) -> float: ...

    @overload
    def sleep(self, *thresholds: float, precision: Literal[0], echo: bool | None = None) -> int: ...

    @overload
    def sleep(self, *thresholds: float, precision: int, echo: bool | None = None) -> float: ...

    def sleep(self, *thresholds: float, precision: int | None = None, echo: bool | None = None) -> float:
        """
        Let the database wait random seconds.

        Parameters
        ----------
        thresholds : Low and high thresholds of random range, range contains thresholds.
            - When `length is 0`, then low and high thresholds is `0` and `10`.
            - When `length is 1`, then low and high thresholds is `0` and `thresholds[0]`.
            - When `length is 2`, then low and high thresholds is `thresholds[0]` and `thresholds[1]`.
        precision : Precision of random range, that is maximum decimal digits of return value.
            - `None`: Set to Maximum decimal digits of element of parameter `thresholds`.
            - `int`: Set to this value.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
            - `bool`: Use this value.

        Returns
        -------
        Random seconds.
            - When parameters `precision` is `0`, then return int.
            - When parameters `precision` is `greater than 0`, then return float.
        """

        # Handle parameter.
        if len(thresholds) == 1:
            second = thresholds[0]
        else:
            second = randn(*thresholds, precision=precision)

        # Sleep.
        sql = f'SELECT SLEEP({second})'
        self.execute(sql, echo=echo)

        return second


class DatabaseExecuteAsync(DatabaseExecuteSuper['rconn.DatabaseConnectionAsync']):
    """
    Asynchronous database execute type.
    """


    async def execute(
        self,
        sql: str | TextClause,
        data: TableData | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Asynchronous execute SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or `TextClause` object.
        data : Data set for filling.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.
        """

        # Handle parameter.
        sql, data, echo = self.handle_execute(sql, data, echo, **kwdata)

        # Transaction.
        await self.conn.get_begin()

        # Execute.

        ## Report.
        if echo:
            tm = TimeMark()
            tm()
            result = await self.conn.connection.execute(sql, data)
            tm()

            ### Generate report.
            start_time = tm.records[0]['datetime']
            spend_time: Timedelta = tm.records[1]['timedelta']
            end_time = tm.records[1]['datetime']
            start_str = time_to(start_time, True)[:-3]
            spend_str = time_to(spend_time, True)[:-3]
            end_str = time_to(end_time, True)[:-3]
            report_runtime = 'Start: %s -> Spend: %ss -> End: %s' % (
                start_str,
                spend_str,
                end_str
            )
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
                recho(report_info, *sqls, title='SQL')
            else:
                recho(report_info, *sqls, data, title='SQL')

        ## Not report.
        else:
            result = await self.conn.connection.execute(sql, data)

        # Automatic commit.
        if self.conn.autocommit:
            await self.conn.commit()
            await self.conn.close()
            await self.conn.db.dispose()

        return result


    __call__ = execute


    async def select(
        self,
        path: str | tuple[str, str],
        fields: str | Iterable[str] | None = None,
        where: str | None = None,
        group: str | None = None,
        having: str | None = None,
        order: str | None = None,
        limit: int | str | tuple[int, int] | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Asynchronous execute select SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
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
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.

        Examples
        --------
        Parameter `fields`.
        >>> fields = ['id', ':`id` + 1 AS `id_`']
        >>> result = await Database.execute.select('table', fields)
        >>> print(result.to_table())
        [{'id': 1, 'id_': 2}, ...]

        Parameter `kwdata`.
        >>> fields = '`id`, `id` + :value AS `id_`'
        >>> result = await Database.execute.select('table', fields, value=1)
        >>> print(result.to_table())
        [{'id': 1, 'id_': 2}, ...]
        """

        # Handle parameter.
        sql = self.handle_select(path, fields, where, group, having, order, limit)

        # Execute SQL.
        result = await self.execute(sql, echo=echo, **kwdata)

        return result


    async def insert(
        self,
        path: str | tuple[str, str],
        data: TableData,
        duplicate: Literal['ignore', 'update'] | Container[str] | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Asynchronous execute insert SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        data : Insert data.
        duplicate : Handle method when constraint error.
            - `None`: Not handled.
            - `ignore`: Use `UPDATE IGNORE INTO` clause.
            - `update`: Use `ON DUPLICATE KEY UPDATE` clause and update all fields.
            - `Container[str]`: Use `ON DUPLICATE KEY UPDATE` clause and update this fields.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.
            - `str and first character is ':'`: Use this syntax.
            - `Any`: Use this value.

        Returns
        -------
        Result object.

        Examples
        --------
        >>> data = [{'key': 'a'}, {'key': 'b'}]
        >>> kwdata = {'value1': 1, 'value2': ':(SELECT 2)'}
        >>> result = await Database.execute.insert('table', data, **kwdata)
        >>> print(result.rowcount)
        2
        >>> result = await Database.execute.select('table')
        >>> print(result.to_table())
        [{'key': 'a', 'value1': 1, 'value2': 2}, {'key': 'b', 'value1': 1, 'value2': 2}]
        """

        # Handle parameter.
        sql, kwdata = self.handle_insert(path, data, duplicate, **kwdata)

        # Execute SQL.
        result = await self.execute(sql, data, echo, **kwdata)

        return result


    async def update(
        self,
        path: str | tuple[str, str],
        data: TableData,
        where_fields: str | Iterable[str] | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Asynchronous execute update SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
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
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.
            - `str and first character is ':'`: Use this syntax.
            - `Any`: Use this value.

        Returns
        -------
        Result object.

        Examples
        --------
        >>> data = [{'key': 'a'}, {'key': 'b'}]
        >>> kwdata = {'value': 1, 'name': ':`key`'}
        >>> result = await Database.execute.update('table', data, **kwdata)
        >>> print(result.rowcount)
        2
        >>> result = await Database.execute.select('table')
        >>> print(result.to_table())
        [{'key': 'a', 'value': 1, 'name': 'a'}, {'key': 'b', 'value': 1, 'name': 'b'}]
        """

        # Handle parameter.
        sql, data = self.handle_update(path, data, where_fields, **kwdata)

        # Execute SQL.
        result = await self.execute(sql, data, echo)

        return result


    async def delete(
        self,
        path: str | tuple[str, str],
        where: str | None = None,
        order: str | None = None,
        limit: int | str | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Asynchronous execute delete SQL.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        where : Clause `WHERE` content, join as `WHERE str`.
        order : Clause `ORDER BY` content, join as `ORDER BY str`.
        limit : Clause `LIMIT` content, join as `LIMIT int/str`.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.

        Examples
        --------
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2)
        >>> result = await Database.execute.delete('table', where, ids=ids)
        >>> print(result.rowcount)
        2
        """

        # Handle parameter.
        sql = self.handle_delete(path, where, order, limit)

        # Execute SQL.
        result = await self.execute(sql, echo=echo, **kwdata)

        return result


    async def copy(
        self,
        path: str | tuple[str, str],
        fields: str | Iterable[str] | None = None,
        where: str | None = None,
        limit: int | str | tuple[int, int] | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> Result:
        """
        Asynchronous execute inesrt SQL of copy records.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        fields : Select clause content.
            - `None`: Is `SELECT *`.
            - `str`: Join as `SELECT str`.
            - `Iterable[str]`: Join as `SELECT str`.
        where : Clause `WHERE` content, join as `WHERE str`.
        limit : Clause `LIMIT` content.
            - `int | str`: Join as `LIMIT int/str`.
            - `tuple[int, int]`: Join as `LIMIT int, int`.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Result object.

        Examples
        --------
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2, 3)
        >>> result = await Database.execute.copy('table', ['name', 'value'], where, 2, ids=ids)
        >>> print(result.rowcount)
        2
        """

        # Handle parameter.
        sql = self.handle_copy(path, fields, where, limit)

        # Execute SQL.
        result = await self.execute(sql, echo=echo, **kwdata)

        return result


    async def count(
        self,
        path: str | tuple[str, str],
        where: str | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> int:
        """
        Asynchronous execute inesrt SQL of count records.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        where : Match condition, `WHERE` clause content, join as `WHERE str`.
            - `None`: Match all.
            - `str`: Match condition.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Record count.

        Examples
        --------
        >>> where = '`id` IN :ids'
        >>> ids = (1, 2)
        >>> result = await Database.execute.count('table', where, ids=ids)
        >>> print(result)
        2
        """

        # Execute.
        result = await self.select(path, '1', where=where, echo=echo, **kwdata)
        count = len(tuple(result))

        return count


    async def exist(
        self,
        path: str | tuple[str, str],
        where: str | None = None,
        echo: bool | None = None,
        **kwdata: Any
    ) -> bool:
        """
        Asynchronous execute inesrt SQL of Judge the exist of record.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        where : Match condition, `WHERE` clause content, join as `WHERE str`.
            - `None`: Match all.
            - `str`: Match condition.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        Judged result.

        Examples
        --------
        >>> data = [{'id': 1}]
        >>> Database.execute.insert('table', data)
        >>> where = '`id` = :id_'
        >>> id_ = 1
        >>> result = await Database.execute.exist('table', where, id_=id_)
        >>> print(result)
        True
        """

        # Execute.
        result = await self.count(path, where, echo, **kwdata)

        # Judge.
        judge = result != 0

        return judge


    async def generator(
        self,
        sql: str | TextClause,
        data: TableData,
        echo: bool | None = None,
        **kwdata: Any
    ) -> AsyncGenerator[Result, Any]:
        """
        Asynchronous return a generator that can execute SQL.

        Parameters
        ----------
        sql : SQL in method `sqlalchemy.text` format, or `TextClause` object.
        data : Data set for filling.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.
        kwdata : Keyword parameters for filling.

        Returns
        -------
        AsyncGenerator.
        """

        # Instance.
        func_generator = FunctionGenerator(
            self.execute,
            sql=sql,
            echo=echo,
            **kwdata
        )

        # Add.
        for row in data:
            func_generator(**row)

        # Create.
        agenerator = func_generator.agenerator()

        return agenerator


    @overload
    async def sleep(self, echo: bool | None = None) -> int: ...

    @overload
    async def sleep(self, second: int, echo: bool | None = None) -> int: ...

    @overload
    async def sleep(self, low: int = 0, high: int = 10, echo: bool | None = None) -> int: ...

    @overload
    async def sleep(self, *thresholds: float, echo: bool | None = None) -> float: ...

    @overload
    async def sleep(self, *thresholds: float, precision: Literal[0], echo: bool | None = None) -> int: ...

    @overload
    async def sleep(self, *thresholds: float, precision: int, echo: bool | None = None) -> float: ...

    async def sleep(self, *thresholds: float, precision: int | None = None, echo: bool | None = None) -> float:
        """
        Asynchronous let the database wait random seconds.

        Parameters
        ----------
        thresholds : Low and high thresholds of random range, range contains thresholds.
            - When `length is 0`, then low and high thresholds is `0` and `10`.
            - When `length is 1`, then low and high thresholds is `0` and `thresholds[0]`.
            - When `length is 2`, then low and high thresholds is `thresholds[0]` and `thresholds[1]`.
        precision : Precision of random range, that is maximum decimal digits of return value.
            - `None`: Set to Maximum decimal digits of element of parameter `thresholds`.
            - `int`: Set to this value.
        echo : Whether report SQL execute information.
            - `None`: Use attribute `Database.echo`.

        Returns
        -------
        Random seconds.
            - When parameters `precision` is `0`, then return int.
            - When parameters `precision` is `greater than 0`, then return float.
        """

        # Handle parameter.
        if len(thresholds) == 1:
            second = thresholds[0]
        else:
            second = randn(*thresholds, precision=precision)

        # Sleep.
        sql = f'SELECT SLEEP({second})'
        await self.execute(sql, echo=echo)

        return second
