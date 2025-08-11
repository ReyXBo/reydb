# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database information methods.
"""


from __future__ import annotations
from typing import Any, Literal, overload
from reykit.rbase import throw

from .rbase import BaseDatabase
from .rconn import Database, DBConnection


__all__ = (
    'DBInformation',
    'DBISchema',
    'DBIDatabase',
    'DBITable',
    'DBIColumn'
)


class DBInformation(BaseDatabase):
    """
    Database base information type.
    """


    @overload
    def __call__(self: DBISchema | DBISchema | DBIDatabase | DBITable) -> list[dict]: ...

    @overload
    def __call__(self: DBISchema, name: str) -> DBIDatabase: ...

    @overload
    def __call__(self: DBIDatabase, name: str) -> DBITable: ...

    @overload
    def __call__(self: DBITable, name: str) -> DBIColumn: ...

    @overload
    def __call__(self: DBIColumn) -> dict: ...

    def __call__(self, name: str | None = None) -> DBIDatabase | DBITable | DBIColumn | list[dict] | dict:
        """
        Get information table or subclass instance.

        Parameters
        ----------
        name : Subclass index name.

        Returns
        -------
        Information table or subclass instance.
        """

        # Information table.
        if name is None:

            ## Break.
            if not hasattr(self, '_get_info_table'):
                raise AssertionError("class '%s' does not have this method" % type(self).__name__)

            ## Get.
            result: list[dict] = self._get_info_table()

        # Subobject.
        else:

            ## Break.
            if not hasattr(self, '__getattr__'):
                raise AssertionError("class '%s' does not have this method" % type(self).__name__)

            ## Get.
            result = self.__getattr__(name)

        return result


    @overload
    def __getitem__(self, key: Literal['*', 'all', 'ALL']) -> dict: ...

    @overload
    def __getitem__(self, key: str) -> Any: ...

    def __getitem__(self, key: str) -> Any:
        """
        Get information attribute value or dictionary.

        Parameters
        ----------
        key : Attribute key. When key not exist, then try all caps key.
            - `Literal['*', 'all', 'ALL']`: Get attribute dictionary.
            - `str`: Get attribute value.

        Returns
        -------
        Information attribute value or dictionary.
        """

        # Break.
        if not hasattr(self, '_get_info_attrs'):
            raise AssertionError("class '%s' does not have this method" % type(self).__name__)

        # Get.
        info_attrs: dict = self._get_info_attrs()

        # Return.

        ## Dictionary.
        if key in ('*', 'all', 'ALL'):
            return info_attrs

        ## Value.
        info_attr = info_attrs.get(key)
        if info_attr is None:
            key_upper = key.upper()
            info_attr = info_attrs[key_upper]
        return info_attr


    @overload
    def __getattr__(self: DBISchema, name: str) -> DBIDatabase: ...

    @overload
    def __getattr__(self: DBIDatabase, name: str) -> DBITable: ...

    @overload
    def __getattr__(self: DBITable, name: str) -> DBIColumn: ...

    def __getattr__(self, name: str) -> DBIDatabase | DBITable | DBIColumn:
        """
        Build subclass instance.

        Parameters
        ----------
        key : Table name.

        Returns
        -------
        Subclass instance.
        """

        # Build.
        match self:
            case DBISchema():
                rtable = DBIDatabase(self._rdatabase, name)
            case DBIDatabase():
                rtable = DBITable(self._rdatabase, self._database_name, name)
            case DBITable():
                rtable = DBIColumn(self._rdatabase, self._database_name, self._table_name, name)
            case _:
                raise AssertionError("class '%s' does not have this method" % type(self).__name__)

        return rtable


class DBISchema(DBInformation):
    """
    Database information schema type.

    Examples
    --------
    Get databases information of server.
    >>> databases_info = DBISchema()

    Get tables information of database.
    >>> tables_info = DBISchema.database()

    Get columns information of table.
    >>> columns_info = DBISchema.database.table()

    Get column information.
    >>> column_info = DBISchema.database.table.column()

    Get database attribute.
    >>> database_attr = DBISchema.database['attribute']

    Get table attribute.
    >>> database_attr = DBISchema.database.table['attribute']

    Get column attribute.
    >>> database_attr = DBISchema.database.table.column['attribute']
    """


    def __init__(
        self,
        rdatabase: Database | DBConnection
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rdatabase : Database or DBConnection instance.
        """

        # Set parameter.
        self._rdatabase = rdatabase


    def _get_info_table(self) -> list[dict]:
        """
        Get information table.

        Returns
        -------
        Information table.
        """

        # SQLite.
        if self._rdatabase.backend == 'sqlite':
            throw(AssertionError, self._rdatabase.drivername)

        # Select.
        else:
            result = self._rdatabase.execute_select(
                'information_schema.SCHEMATA',
                order='`schema_name`'
            )

        # Convert.
        info_table = result.to_table()

        return info_table


class DBIDatabase(DBInformation):
    """
    Database information database type.

    Examples
    --------
    Get tables information of database.
    >>> tables_info = DBIDatabase()

    Get columns information of table.
    >>> columns_info = DBIDatabase.table()

    Get column information.
    >>> column_info = DBIDatabase.table.column()

    Get database attribute.
    >>> database_attr = DBIDatabase['attribute']

    Get table attribute.
    >>> database_attr = DBIDatabase.table['attribute']

    Get column attribute.
    >>> database_attr = DBIDatabase.table.column['attribute']
    """


    def __init__(
        self,
        rdatabase: Database | DBConnection,
        database_name: str
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rdatabase : Database or DBConnection instance.
        database_name : Database name.
        """

        # SQLite.
        if (
            rdatabase.backend == 'sqlite'
            and database_name != 'main'
        ):
            throw(ValueError, database_name)

        # Set parameter.
        self._rdatabase = rdatabase
        self._database_name = database_name


    def _get_info_attrs(self) -> dict:
        """
        Get information attribute dictionary.

        Returns
        -------
        Information attribute dictionary.
        """

        # SQLite.
        if self._rdatabase.backend == 'sqlite':
            throw(AssertionError, self._rdatabase.drivername)

        # Select.
        where = '`SCHEMA_NAME` = :database_name'
        result = self._rdatabase.execute_select(
            'information_schema.SCHEMATA',
            where=where,
            limit=1,
            database_name=self._database_name
        )

        # Convert.
        info_table = result.to_table()

        ## Check.
        assert len(info_table) != 0, "database '%s' not exist" % self._database_name

        info_attrs = info_table[0]

        return info_attrs


    def _get_info_table(self) -> list[dict]:
        """
        Get information table.

        Returns
        -------
        Information table.
        """

        # Select.

        ## SQLite.
        if self._rdatabase.backend == 'sqlite':
            result = self._rdatabase.execute_select('main.sqlite_master')

        ## Other.
        else:
            where = '`TABLE_SCHEMA` = :database_name'
            result = self._rdatabase.execute_select(
                'information_schema.TABLES',
                where=where,
                order='`TABLE_NAME`',
                database_name=self._database_name
            )

        # Convert.
        info_table = result.to_table()

        ## Check.
        assert len(info_table) != 0, "database '%s' not exist" % self._database_name

        return info_table


class DBITable(DBInformation):
    """
    Database information table type.

    Examples
    --------
    Get columns information of table.
    >>> columns_info = DBITable()

    Get column information.
    >>> column_info = DBITable.column()

    Get table attribute.
    >>> database_attr = DBITable['attribute']

    Get column attribute.
    >>> database_attr = DBITable.column['attribute']
    """


    def __init__(
        self,
        rdatabase: Database | DBConnection,
        database_name: str,
        table_name: str
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rdatabase : Database or DBConnection instance.
        database_name : Database name.
        table_name : Table name.
        """

        # Set parameter.
        self._rdatabase = rdatabase
        self._database_name = database_name
        self._table_name = table_name


    def _get_info_attrs(self) -> dict:
        """
        Get information attribute dictionary.

        Returns
        -------
        Information attribute dictionary.
        """

        # Select.

        ## SQLite.
        if self._rdatabase.backend == 'sqlite':
            where = '`name` = :name'
            result = self._rdatabase.execute_select(
                'main.sqlite_master',
                where=where,
                limit=1,
                name=self._table_name
            )

        ## Other.
        else:
            where = '`TABLE_SCHEMA` = :database_name AND `TABLE_NAME` = :table_name'
            result = self._rdatabase.execute_select(
                'information_schema.TABLES',
                where=where,
                limit=1,
                database_name=self._database_name,
                table_name=self._table_name
            )

        # Convert.
        info_table = result.to_table()

        ## Check.
        assert len(info_table) != 0, "database '%s' or table '%s' not exist" % (self._database_name, self._table_name)

        info_attrs = info_table[0]

        return info_attrs


    def _get_info_table(self) -> list[dict]:
        """
        Get information table.

        Returns
        -------
        Information table.
        """

        # Select.

        ## SQLite.
        if self._rdatabase.backend == 'sqlite':
            sql = f'PRAGMA table_info("%s")' % self._table_name
            result = self._rdatabase.execute(sql)

        ## Other.
        else:
            where = '`TABLE_SCHEMA` = :database_name AND `TABLE_NAME` = :table_name'
            result = self._rdatabase.execute_select(
                'information_schema.COLUMNS',
                where=where,
                order='`ORDINAL_POSITION`',
                database_name=self._database_name,
                table_name=self._table_name
            )

        # Convert.
        info_table = result.to_table()

        ## Check.
        assert len(info_table) != 0, "database '%s' or table '%s' not exist" % (self._database_name, self._table_name)

        return info_table


class DBIColumn(DBInformation):
    """
    Database information column type.

    Examples
    --------
    Get column information.
    >>> column_info = DBIColumn()

    Get column attribute.
    >>> database_attr = DBIColumn['attribute']
    """


    def __init__(
        self,
        rdatabase: Database | DBConnection,
        database_name: str,
        table_name: str,
        column_name: str
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rdatabase : Database or DBConnection instance.
        database_name : Database name.
        table_name : Table name.
        column_name : Column name.
        """

        # Set parameter.
        self._rdatabase = rdatabase
        self._database_name = database_name
        self._table_name = table_name
        self._column_name = column_name


    def _get_info_attrs(self) -> dict:
        """
        Get information attribute dictionary.

        Returns
        -------
        Information attribute dictionary.
        """

        # Select.

        ## SQLite.
        if self._rdatabase.backend == 'sqlite':
            sql = f'PRAGMA table_info("%s")' % self._table_name
            where = '`name` = :name'
            result = self._rdatabase.execute(
                sql,
                where=where,
                limit=1,
                name=self._column_name
            )

        ## Other.
        else:
            where = '`TABLE_SCHEMA` = :database_name AND `TABLE_NAME` = :table_name AND `COLUMN_NAME` = :column_name'
            result = self._rdatabase.execute_select(
                'information_schema.COLUMNS',
                where=where,
                limit=1,
                database_name=self._database_name,
                table_name=self._table_name,
                column_name=self._column_name
            )

        # Convert.
        info_table = result.to_table()

        ## Check.
        assert len(info_table) != 0, "database '%s' or table '%s' or column '%s' not exist" % (self._database_name, self._table_name, self._column_name)

        info_attrs = info_table[0]

        return info_attrs


    _get_info_table = _get_info_attrs
