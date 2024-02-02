# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database execute methods.
"""


from __future__ import annotations
from typing import Any, List, Dict, Tuple, Union, Optional, Literal, overload
from reytool.rsystem import throw
from reytool.rtable import Table

from .rconnection import RDatabase, RDBConnection, RResult


__all__ = (
    "RDBExecute",
)


class RDBExecute(object):
    """
    Rey's `database execute` type.

    Examples
    --------
    Select.
    >>> field = ["id", "value"]
    >>> where = "`id` = ids"
    >>> ids = (1, 2)
    >>> result = RDBExecute.database.table(field, where, ids=ids)

    Insert.
    >>> data = [{'id': 1}, {'id': 2}]
    >>> duplicate = 'ignore'
    >>> result = RDBExecute.database.table + data
    >>> result = RDBExecute.database.table + (data, duplicate)
    >>> result = RDBExecute.database.table + {"data": data, "duplicate": duplicate}

    Update.
    >>> data = [{'name': 'a', 'id': 1}, {'name': 'b', 'id': 2}]
    >>> where_fields = 'id'
    >>> result = RDBExecute.database.table & data
    >>> result = RDBExecute.database.table & (data, where_fields)
    >>> result = RDBExecute.database.table & {"data": data, "where_fields": where_fields}

    Delete.
    >>> where = '`id` IN (1, 2)'
    >>> report = True
    >>> result = RDBExecute.database.table - where
    >>> result = RDBExecute.database.table - (where, report)
    >>> result = RDBExecute.database.table - {"where": where, "report": report}

    Copy.
    >>> where = '`id` IN (1, 2)'
    >>> limit = 1
    >>> result = RDBExecute.database.table * where
    >>> result = RDBExecute.database.table * (where, limit)
    >>> result = RDBExecute.database.table * {"where": where, "limit": limit}

    Exist.
    >>> where = '`id` IN (1, 2)'
    >>> report = True
    >>> result = where in RDBExecute.database.table
    >>> result = (where, report) in RDBExecute.database.table
    >>> result = {"where": where, "report": report} in RDBExecute.database.table

    Count.
    >>> result = len(RDBExecute.database.table)

    Default database.
    >>> field = ["id", "value"]
    >>> engine = RDatabase(**server, database)
    >>> result = engine.exe.table()
    """


    def __init__(self, rdatabase: Union[RDatabase, RDBConnection]) -> None:
        """
        Build `database execute` instance.

        Parameters
        ----------
        rdatabase : RDatabase or RDBConnection instance.
        """

        # Set parameter.
        self._rdatabase = rdatabase
        self._path: List[str] = []


    @overload
    def __getattr__(self, key: Literal["_rdatabase"]) -> Union[RDatabase, RDBConnection]: ...

    @overload
    def __getattr__(self, key: Literal["_path"]) -> List[str]: ...

    @overload
    def __getattr__(self, key: str) -> RDBExecute: ...

    def __getattr__(self, key: str) -> Union[
        Union[RDatabase, RDBConnection],
        List[str],
        RDBExecute
    ]:
        """
        Get attribute or set database name or set table name.

        Parameters
        ----------
        key : Attribute key or database name or table name.

        Returns
        -------
        Value of attribute or self.
        """

        # Filter private.
        if key in ("_rdatabase", "_path"):
            return self.__dict__[key]

        # Check parameter.
        if len(self._path) not in (0, 1):
            throw(AssertionError)

        # Set parameter.
        self._path.append(key)

        return self


    @property
    def _get_path(self) -> Tuple[str, str]:
        """
        Get database name and table name.

        Returns
        -------
        Database name and table name.
        """

        # Get.
        path_len = len(self._path)
        if path_len == 1:
            database = self._rdatabase.database
            table = self._path[0]
        elif path_len == 2:
            database = self._path[0]
            table = self._path[1]
        else:
            throw(AssertionError)

        return database, table


    def __call__(
        self,
        *args: Any,
        **kwargs: Any
    ) -> RResult:
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
        params: Union[Tuple, Dict, Table]
    ) -> RResult:
        """
        Insert the data of table in the datebase.

        Parameters
        ----------
        params : Insert parameters.
            - `Tuple` : Enter parameters in '(path, *params)' format.
            - `Dict` : Enter parameters in '(path, **params)' format.
            - `Table` : Enter parameters in '(path, params)' format.

        Returns
        -------
        Result object.
        """

        # Insert.
        if params.__class__ == tuple:
            result = self._rdatabase.execute_insert(self._get_path, *params)
        elif params.__class__ == dict:
            result = self._rdatabase.execute_insert(self._get_path, **params)
        else:
            result = self._rdatabase.execute_insert(self._get_path, params)

        return result


    def __and__(
        self,
        params: Union[Tuple, Dict, Table]
    ) -> RResult:
        """
        Update the data of table in the datebase.

        Parameters
        ----------
        params : Update parameters.
            - `Tuple` : Enter parameters in '(path, *params)' format.
            - `Dict` : Enter parameters in '(path, **params)' format.
            - `Table` : Enter parameters in '(path, params)' format.

        Returns
        -------
        Result object.
        """

        # Update.
        if params.__class__ == tuple:
            result = self._rdatabase.execute_update(self._get_path, *params)
        elif params.__class__ == dict:
            result = self._rdatabase.execute_update(self._get_path, **params)
        else:
            result = self._rdatabase.execute_update(self._get_path, params)

        return result


    def __sub__(
        self,
        params: Union[Tuple, Dict, str]
    ) -> RResult:
        """
        Delete the data of table in the datebase.

        Parameters
        ----------
        params : Update parameters.
            - `Tuple` : Enter parameters in '(path, *params)' format.
            - `Dict` : Enter parameters in '(path, **params)' format.
            - `str` : Enter parameters in '(path, params)' format.

        Returns
        -------
        Result object.
        """

        # Update.
        if params.__class__ == tuple:
            result = self._rdatabase.execute_delete(self._get_path, *params)
        elif params.__class__ == dict:
            result = self._rdatabase.execute_delete(self._get_path, **params)
        else:
            result = self._rdatabase.execute_delete(self._get_path, params)

        return result


    def __mul__(
        self,
        params: Union[Tuple, Dict, str]
    ) -> RResult:
        """
        Copy record of table in the datebase.

        Parameters
        ----------
        params : Update parameters.
            - `Tuple` : Enter parameters in '(path, *params)' format.
            - `Dict` : Enter parameters in '(path, **params)' format.
            - `str` : Enter parameters in '(path, params)' format.

        Returns
        -------
        Result object.
        """

        # Update.
        if params.__class__ == tuple:
            result = self._rdatabase.execute_copy(self._get_path, *params)
        elif params.__class__ == dict:
            result = self._rdatabase.execute_copy(self._get_path, **params)
        else:
            result = self._rdatabase.execute_copy(self._get_path, params)

        return result


    def __contains__(
        self,
        params: Union[Tuple, Dict, str]
    ) -> bool:
        """
        Judge the exist of record.

        Parameters
        ----------
        params : Update parameters.
            - `Tuple` : Enter parameters in '(path, *params)' format.
            - `Dict` : Enter parameters in '(path, **params)' format.
            - `str` : Enter parameters in '(path, params)' format.

        Returns
        -------
        Result object.
        """

        # Update.
        if params.__class__ == tuple:
            result = self._rdatabase.execute_exist(self._get_path, *params)
        elif params.__class__ == dict:
            result = self._rdatabase.execute_exist(self._get_path, **params)
        else:
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