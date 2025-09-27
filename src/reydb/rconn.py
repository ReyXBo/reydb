# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database connection methods.
"""


from typing import Self
from sqlalchemy import Connection, Transaction
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncTransaction

from .rbase import DatabaseBase
from .rdb import Database


__all__ = (
    'DatabaseConnection',
    'DatabaseConnectionAsync'
)


class DatabaseConnection(DatabaseBase):
    """
    Database connection type.
    """


    def __init__(
        self,
        db: Database,
        autocommit: bool
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db : `Database` instance.
        autocommit: Whether automatic commit execute.
        """

        # Import.
        from .rexec import DatabaseExecute

        # Build.
        self.db = db
        self.autocommit = autocommit
        self.execute = DatabaseExecute(self)
        self.conn: Connection | None = None
        self.begin: Transaction | None = None


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
        id_ = result.scalar()

        return id_


class DatabaseConnectionAsync(DatabaseBase):
    """
    Asynchronous database connection type.
    """


    def __init__(
        self,
        db: Database,
        autocommit: bool
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db : `DatabaseAsync` instance.
        autocommit: Whether automatic commit execute.
        """

        # Import.
        from .rexec import DatabaseExecuteAsync

        # Build.
        self.db = db
        self.autocommit = autocommit
        self.aexecute = DatabaseExecuteAsync(self)
        self.aconn: AsyncConnection | None = None
        self.abegin: AsyncTransaction | None = None


    async def get_conn(self) -> AsyncConnection:
        """
        Asynchronous get `Connection` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.aconn is None:
            self.aconn = await self.db.aengine.connect()

        return self.aconn


    async def get_begin(self) -> AsyncTransaction:
        """
        Asynchronous get `Transaction` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.abegin is None:
            conn = await self.get_conn()
            self.abegin = await conn.begin()

        return self.abegin


    async def commit(self) -> None:
        """
        Asynchronous commit cumulative executions.
        """

        # Commit.
        if self.abegin is not None:
            await self.abegin.commit()
            self.abegin = None


    async def rollback(self) -> None:
        """
        Asynchronous rollback cumulative executions.
        """

        # Rollback.
        if self.abegin is not None:
            await self.abegin.rollback()
            self.abegin = None


    async def close(self) -> None:
        """
        Asynchronous close database connection.
        """

        # Close.
        if self.abegin is not None:
            await self.abegin.close()
            self.abegin = None
        if self.aconn is not None:
            await self.aconn.close()
            self.aconn = None


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
        result = await self.aexecute(sql)
        id_ = result.scalar()

        return id_
