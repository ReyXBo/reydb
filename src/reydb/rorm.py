# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-09-23 00:50:32
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database ORM methods.
"""


from sqlmodel import SQLModel, Session

from .rbase import DatabaseBase
from .rdb import Database


__all__ = (
    'DatabaseORM',
)


class DatabaseORM(DatabaseBase):
    """
    Database ORM type.
    """


    def __init__(self, db: Database) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: Database instance.
        """

        # Build.
        self.db = db
