# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database path methods.
"""


from typing import Any, Self
from reykit.rbase import throw
from reykit.rtable import TableData

from .rbase import BaseDatabase
from .rconn import Database, DBConnection, Result


__all__ = (
    'DBExecute',
)


class DBExecute(BaseDatabase):
    """
    Database execute type.

    Examples
    --------
    Select.
    >>> field = ['id', 'value']
    >>> where = '`id` = ids'
    >>> ids = (1, 2)
    >>> result = DBExecute.database.table(field, where, ids=ids)

    Insert.
    >>> data = [{'id': 1}, {'id': 2}]
    >>> duplicate = 'ignore'
    >>> result = DBExecute.database.table + data
    >>> result = DBExecute.database.table + (data, duplicate)
    >>> result = DBExecute.database.table + {'data': data, 'duplicate': duplicate}

    Update.
    >>> data = [{'name': 'a', 'id': 1}, {'name': 'b', 'id': 2}]
    >>> where_fields = 'id'
    >>> result = DBExecute.database.table & data
    >>> result = DBExecute.database.table & (data, where_fields)
    >>> result = DBExecute.database.table & {'data': data, 'where_fields': where_fields}

    Delete.
    >>> where = '`id` IN (1, 2)'
    >>> report = True
    >>> result = DBExecute.database.table - where
    >>> result = DBExecute.database.table - (where, report)
    >>> result = DBExecute.database.table - {'where': where, 'report': report}

    Copy.
    >>> where = '`id` IN (1, 2)'
    >>> limit = 1
    >>> result = DBExecute.database.table * where
    >>> result = DBExecute.database.table * (where, limit)
    >>> result = DBExecute.database.table * {'where': where, 'limit': limit}

    Exist.
    >>> where = '`id` IN (1, 2)'
    >>> report = True
    >>> result = where in DBExecute.database.table
    >>> result = (where, report) in DBExecute.database.table
    >>> result = {'where': where, 'report': report} in DBExecute.database.table

    Count.
    >>> result = len(DBExecute.database.table)

    Default database.
    >>> engine = Database(**server, database)
    >>> result = engine.exe.table()
    """


    def __init__(self, rdatabase: Database | DBConnection) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rdatabase : Database or DBConnection instance.
        """

        # Set parameter.
        self._rdatabase = rdatabase
        self._path: list[str] = []


    def __getattr__(self, name: str) -> Self:
        """
        Set database name or set table name.

        Parameters
        ----------
        name : Database name or table name.

        Returns
        -------
        Self.
        """

        # Check.
        if len(self._path) not in (0, 1):
            throw(AssertionError, self._path)

        # Set.
        self._path.append(name)

        return self


    @property
    def _get_path(self) -> tuple[str, str]:
        """
        Get database name and table name.

        Returns
        -------
        Database name and table name.
        """

        # Get.
        path_len = len(self._path)
        match path_len:
            case 1:
                database = self._rdatabase.database
                table = self._path[0]
            case 2:
                database = self._path[0]
                table = self._path[1]
            case _:
                throw(AssertionError, path_len)

        return database, table


    def __call__(
        self,
        *args: Any,
        **kwargs: Any
    ) -> Result:
        """
        Select the data of table in the datebase.

        Parameters
        ----------
        args : Position arguments.
        kwargs : Keyword arguments.

        Returns
        -------
        Result object.
        """

        # Selete.
        result = self._rdatabase.execute_select(self._get_path, *args, **kwargs)

        return result


    def __add__(
        self,
        params: tuple | dict | TableData
    ) -> Result:
        """
        Insert the data of table in the datebase.

        Parameters
        ----------
        params : Insert parameters.
            - `tuple`: Enter parameters in '(path, *params)' format.
            - `dict`: Enter parameters in '(path, **params)' format.
            - `TableData`: Enter parameters in '(path, params)' format.

        Returns
        -------
        Result object.
        """

        # Insert.
        match params:
            case tuple():
                result = self._rdatabase.execute_insert(self._get_path, *params)
            case dict():
                result = self._rdatabase.execute_insert(self._get_path, **params)
            case _:
                result = self._rdatabase.execute_insert(self._get_path, params)

        return result


    def __and__(
        self,
        params: tuple | dict | TableData
    ) -> Result:
        """
        Update the data of table in the datebase.

        Parameters
        ----------
        params : Update parameters.
            - `tuple`: Enter parameters in '(path, *params)' format.
            - `dict`: Enter parameters in '(path, **params)' format.
            - `TableData`: Enter parameters in '(path, params)' format.

        Returns
        -------
        Result object.
        """

        # Update.
        match params:
            case tuple():
                result = self._rdatabase.execute_update(self._get_path, *params)
            case dict():
                result = self._rdatabase.execute_update(self._get_path, **params)
            case _:
                result = self._rdatabase.execute_update(self._get_path, params)

        return result


    def __sub__(
        self,
        params: tuple | dict | str
    ) -> Result:
        """
        Delete the data of table in the datebase.

        Parameters
        ----------
        params : Update parameters.
            - `tuple`: Enter parameters in '(path, *params)' format.
            - `dict`: Enter parameters in '(path, **params)' format.
            - `str`: Enter parameters in '(path, params)' format.

        Returns
        -------
        Result object.
        """

        # Update.
        match params:
            case tuple():
                result = self._rdatabase.execute_delete(self._get_path, *params)
            case dict():
                result = self._rdatabase.execute_delete(self._get_path, **params)
            case _:
                result = self._rdatabase.execute_delete(self._get_path, params)

        return result


    def __mul__(
        self,
        params: tuple | dict | str
    ) -> Result:
        """
        Copy record of table in the datebase.

        Parameters
        ----------
        params : Update parameters.
            - `tuple`: Enter parameters in '(path, *params)' format.
            - `dict`: Enter parameters in '(path, **params)' format.
            - `str`: Enter parameters in '(path, params)' format.

        Returns
        -------
        Result object.
        """

        # Update.
        match params:
            case tuple():
                result = self._rdatabase.execute_copy(self._get_path, *params)
            case dict():
                result = self._rdatabase.execute_copy(self._get_path, **params)
            case _:
                result = self._rdatabase.execute_copy(self._get_path, params)

        return result


    def __contains__(
        self,
        params: tuple | dict | str
    ) -> bool:
        """
        Judge the exist of record.

        Parameters
        ----------
        params : Update parameters.
            - `tuple`: Enter parameters in '(path, *params)' format.
            - `dict`: Enter parameters in '(path, **params)' format.
            - `str`: Enter parameters in '(path, params)' format.

        Returns
        -------
        Result object.
        """

        # Update.
        match params:
            case tuple():
                result = self._rdatabase.execute_exist(self._get_path, *params)
            case dict():
                result = self._rdatabase.execute_exist(self._get_path, **params)
            case _:
                result = self._rdatabase.execute_exist(self._get_path, params)

        return result


    def __len__(
        self
    ) -> int:
        """
        Count records.

        Returns
        -------
        Record count.
        """

        # Update.
        result = self._rdatabase.execute_count(self._get_path)

        return result
