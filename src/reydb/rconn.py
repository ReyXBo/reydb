# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database connection methods.
"""


from typing import Self
from sqlalchemy.engine.base import Connection
from sqlalchemy.sql.elements import TextClause

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
        self.username = rdatabase.username
        self.password = rdatabase.password
        self.host = rdatabase.host
        self.port = rdatabase.port
        self.database = rdatabase.database
        self.query = rdatabase.query
        self.pool_recycle = rdatabase.pool_recycle


    def executor(
        self,
        sql: TextClause,
        data: list[dict],
        report: bool
    ) -> Result:
        """
        SQL executor.

        Parameters
        ----------
        sql : TextClause object.
        data : Data set for filling.
        report : Whether report SQL execute information.

        Returns
        -------
        Result object.
        """

        # Create transaction.
        if self.begin is None:
            self.begin = self.connection.begin()

        # Execute.

        ## Report.
        if report:
            result = self.executor_report(self.connection, sql, data)

        ## Not report.
        else:
            result = self.connection.execute(sql, data)

        return result


    def commit(self) -> None:
        """
        Commit cumulative executions.
        """

        # Commit.
        if self.begin is not None:
            self.begin.commit()
            self.begin = None


    def rollback(self) -> None:
        """
        Rollback cumulative executions.
        """

        # Rollback.
        if self.begin is not None:
            self.begin.rollback()
            self.begin = None


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


    @property
    def insert_id(self) -> int:
        """
        Return last self increasing ID.

        Returns
        -------
        ID.
        """

        # Get.
        sql = 'SELECT LAST_INSERT_ID()'
        result = self.execute(sql)
        id_ = result.scalar()

        return id_
