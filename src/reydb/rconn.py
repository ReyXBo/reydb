# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database connection methods.
"""


from typing import Self, Generic
from sqlalchemy import Connection, Transaction
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncTransaction

from . import rdb, rexec
from .rbase import DatabaseT, DatabaseExecuteT, ConnectionT, TransactionT, DatabaseBase


__all__ = (
    'DatabaseConnectionSuper',
    'DatabaseConnection',
    'DatabaseConnectionAsync'
)


class DatabaseConnectionSuper(DatabaseBase, Generic[DatabaseT, DatabaseExecuteT, ConnectionT, TransactionT]):
    """
    Database connection super type.
    """


    def __init__(
        self,
        db: DatabaseT,
        autocommit: bool
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db : Database instance.
        autocommit: Whether automatic commit execute.
        """

        # Build.
        self.db = db
        self.autocommit = autocommit
        match db:
            case rdb.Database():
                exec = rexec.DatabaseExecute(self)
            case rdb.DatabaseAsync():
                exec = rexec.DatabaseExecuteAsync(self)
        self.execute: DatabaseExecuteT = exec
        self.conn: ConnectionT | None = None
        self.begin: TransactionT | None = None


class DatabaseConnection(DatabaseConnectionSuper['rdb.Database', 'rexec.DatabaseExecute', Connection, Transaction]):
    """
    Database connection type.
    """


    def get_conn(self) -> Connection:
        """
        Get `Connection` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.conn is None:
            self.conn = self.db.engine.connect()

        return self.conn


    def get_begin(self) -> Transaction:
        """
        Get `Transaction` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.begin is None:
            conn = self.get_conn()
            self.begin = conn.begin()

        return self.begin


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
        if self.begin is not None:
            self.begin.close()
            self.begin = None
        if self.conn is not None:
            self.conn.close()
            self.conn = None


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
        self.close()


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
        insert_id = result.scalar()

        return insert_id


class DatabaseConnectionAsync(DatabaseConnectionSuper['rdb.DatabaseAsync', 'rexec.DatabaseExecuteAsync', AsyncConnection, AsyncTransaction]):
    """
    Asynchronous database connection type.
    """


    async def get_conn(self) -> AsyncConnection:
        """
        Asynchronous get `Connection` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.conn is None:
            self.conn = await self.db.engine.connect()

        return self.conn


    async def get_begin(self) -> AsyncTransaction:
        """
        Asynchronous get `Transaction` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.begin is None:
            conn = await self.get_conn()
            self.begin = await conn.begin()

        return self.begin


    async def commit(self) -> None:
        """
        Asynchronous commit cumulative executions.
        """

        # Commit.
        if self.begin is not None:
            await self.begin.commit()
            self.begin = None


    async def rollback(self) -> None:
        """
        Asynchronous rollback cumulative executions.
        """

        # Rollback.
        if self.begin is not None:
            await self.begin.rollback()
            self.begin = None


    async def close(self) -> None:
        """
        Asynchronous close database connection.
        """

        # Close.
        if self.begin is not None:
            await self.begin.close()
            self.begin = None
        if self.conn is not None:
            await self.conn.close()
            self.conn = None


    async def __aenter__(self):
        """
        Asynchronous enter syntax `async with`.

        Returns
        -------
        Self.
        """

        return self


    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        *_
    ) -> None:
        """
        Asynchronous exit syntax `async with`.

        Parameters
        ----------
        exc_type : Exception type.
        """

        # Commit.
        if exc_type is None:
            await self.commit()

        # Close.
        await self.close()
        await self.db.dispose()


    async def insert_id(self) -> int:
        """
        Asynchronous return last self increasing ID.

        Returns
        -------
        ID.
        """

        # Get.
        sql = 'SELECT LAST_INSERT_ID()'
        result = await self.execute(sql)
        id_ = result.scalar()

        return id_
