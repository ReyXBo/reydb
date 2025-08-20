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

from .rbase import DatabaseBase
from .rconn import DatabaseConnection
from .rdb import Database, Result


__all__ = (
    'DatabaseExecute',
)


class DatabaseExecute(DatabaseBase):
    """
    Database execute type.

    Examples
    --------
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
    >>> engine = Database(**server, database)
    >>> result = engine.exe.table()
    """


    def __init__(self, rdatabase: Database | DatabaseConnection) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rdatabase : Database or DatabaseConnection instance.
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
    def __get_path(self) -> tuple[str, str]:
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
        result = self._rdatabase.execute_select(self.__get_path, *args, **kwargs)

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
                result = self._rdatabase.execute_insert(self.__get_path, *params)
            case dict():
                result = self._rdatabase.execute_insert(self.__get_path, **params)
            case _:
                result = self._rdatabase.execute_insert(self.__get_path, params)

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
                result = self._rdatabase.execute_update(self.__get_path, *params)
            case dict():
                result = self._rdatabase.execute_update(self.__get_path, **params)
            case _:
                result = self._rdatabase.execute_update(self.__get_path, params)

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
                result = self._rdatabase.execute_delete(self.__get_path, *params)
            case dict():
                result = self._rdatabase.execute_delete(self.__get_path, **params)
            case _:
                result = self._rdatabase.execute_delete(self.__get_path, params)

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
                result = self._rdatabase.execute_copy(self.__get_path, *params)
            case dict():
                result = self._rdatabase.execute_copy(self.__get_path, **params)
            case _:
                result = self._rdatabase.execute_copy(self.__get_path, params)

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
                result = self._rdatabase.execute_exist(self.__get_path, *params)
            case dict():
                result = self._rdatabase.execute_exist(self.__get_path, **params)
            case _:
                result = self._rdatabase.execute_exist(self.__get_path, params)

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
        result = self._rdatabase.execute_count(self.__get_path)

        return result
