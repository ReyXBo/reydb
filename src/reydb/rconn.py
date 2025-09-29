# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database connection methods.
"""


from typing import Self, TypeVar, Generic
from sqlalchemy import Connection, Transaction
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncTransaction

from . import rdb, rexec
from .rbase import ConnectionT, TransactionT, DatabaseBase


__all__ = (
    'DatabaseConnectionSuper',
    'DatabaseConnection',
    'DatabaseConnectionAsync'
)


DatabaseT = TypeVar('DatabaseT', 'rdb.Database', 'rdb.DatabaseAsync')
DatabaseExecuteT = TypeVar('DatabaseExecuteT', 'rexec.DatabaseExecute', 'rexec.DatabaseExecuteAsync')


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
        self.connection: ConnectionT | None = None
        self.transaction: TransactionT | None = None


class DatabaseConnection(DatabaseConnectionSuper['rdb.Database', 'rexec.DatabaseExecute', Connection, Transaction]):
    """
    Database connection type.
    """


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


    def get_conn(self) -> Connection:
        """
        Get `Connection` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.connection is None:
            self.connection = self.db.engine.connect()

        return self.connection


    def get_begin(self) -> Transaction:
        """
        Get `Transaction` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.transaction is None:
            conn = self.get_conn()
            self.transaction = conn.begin()

        return self.transaction


    def commit(self) -> None:
        """
        Commit cumulative executions.
        """

        # Commit.
        if self.transaction is not None:
            self.transaction.commit()
            self.transaction = None


    def rollback(self) -> None:
        """
        Rollback cumulative executions.
        """

        # Rollback.
        if self.transaction is not None:
            self.transaction.rollback()
            self.transaction = None


    def close(self) -> None:
        """
        Close database connection.
        """

        # Close.
        if self.transaction is not None:
            self.transaction.close()
            self.transaction = None
        if self.connection is not None:
            self.connection.close()
            self.connection = None


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


    async def get_conn(self) -> AsyncConnection:
        """
        Asynchronous get `AsyncConnection` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.connection is None:
            self.connection = await self.db.engine.connect()

        return self.connection


    async def get_begin(self) -> AsyncTransaction:
        """
        Asynchronous get `AsyncTransaction` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.transaction is None:
            conn = await self.get_conn()
            self.transaction = await conn.begin()

        return self.transaction


    async def commit(self) -> None:
        """
        Asynchronous commit cumulative executions.
        """

        # Commit.
        if self.transaction is not None:
            await self.transaction.commit()
            self.transaction = None


    async def rollback(self) -> None:
        """
        Asynchronous rollback cumulative executions.
        """

        # Rollback.
        if self.transaction is not None:
            await self.transaction.rollback()
            self.transaction = None


    async def close(self) -> None:
        """
        Asynchronous close database connection.
        """

        # Close.
        if self.transaction is not None:
            await self.transaction.close()
            self.transaction = None
        if self.connection is not None:
            await self.connection.close()
            self.connection = None


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
