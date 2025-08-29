# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database connection methods.
"""


from typing import Any, Self
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.exc import OperationalError
from reykit.rbase import get_first_notnone
from reykit.rdata import objs_in
from reykit.rstdout import echo
from reykit.rtable import TableData, Table
from reykit.rwrap import wrap_runtime, wrap_retry

from .rdb import Result, Database


__all__ = (
    'DatabaseConnection',
)


class DatabaseConnection(Database):
    """
    Database connection type.
    """


    def __init__(
        self,
        connection: Connection,
        rdatabase: Database
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        connection : Connection object.
        rdatabase : Database object.
        """

        # Set parameter.
        self.connection = connection
        self.rdatabase = rdatabase
        self.begin = None
        self.begin_count = 0
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
        if self.begin_count == 0:
            self.rollback()
            self.begin = connection.begin()

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

        # Count.
        syntaxes = self.get_syntax(sql)
        if objs_in(syntaxes, 'INSERT', 'UPDATE', 'DELETE'):
            self.begin_count += 1

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

        ## Can retry.
        if (
            self.retry
            and self.begin_count == 0
            and not self.is_multi_sql(sql)
        ):
            text = 'Retrying...'
            title = 'Database Execute Operational Error'
            handler = lambda exc_text, *_: echo(exc_text, text, title=title, frame='top')
            executor = wrap_retry(self.executor, handler=handler, exception=OperationalError)
            result = executor(self.connection, sql, data, report)

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


    def __enter__(self) -> Self:
        """
        Enter syntax `with`.

        Returns
        -------
        Self.
        """

        return self


    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        *_
    ) -> None:
        """
        Exit syntax `with`.

        Parameters
        ----------
        exc_type : Exception type.
        """

        # Commit.
        if exc_type is None:
            self.commit()

        # Close.
        else:
            self.close()


    __del__ = close
