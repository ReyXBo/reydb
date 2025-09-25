# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database connection methods.
"""


from typing import Self
from sqlalchemy import Transaction

from .rbase import DatabaseBase
from .rdb import Database


__all__ = (
    'DatabaseConnection',
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
        self.conn = db.engine.connect()
        self.exec = DatabaseExecute(self)
        self.begin: Transaction | None = None


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
        self.conn.close()


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
    def execute(self):
        """
        Build `database execute` instance.

        Returns
        -------
        Instance.
        """

        # Create transaction.
        if self.begin is None:
            self.begin = self.conn.begin()

        return self.exec


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
