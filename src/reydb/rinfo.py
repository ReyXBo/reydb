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

from .rbase import DatabaseBase
from .rconn import DatabaseConnection
from .rdb import Database


__all__ = (
    'DatabaseInformation',
    'DatabaseInformationSchema',
    'DatabaseInformationDatabase',
    'DatabaseInformationTable',
    'DatabaseInformationColumn'
)


class DatabaseInformation(DatabaseBase):
    """
    Database base information type.
    """


    @overload
    def __call__(self: DatabaseInformationSchema | DatabaseInformationSchema | DatabaseInformationDatabase | DatabaseInformationTable) -> list[dict]: ...

    @overload
    def __call__(self: DatabaseInformationSchema, name: str) -> DatabaseInformationDatabase: ...

    @overload
    def __call__(self: DatabaseInformationDatabase, name: str) -> DatabaseInformationTable: ...

    @overload
    def __call__(self: DatabaseInformationTable, name: str) -> DatabaseInformationColumn: ...

    @overload
    def __call__(self: DatabaseInformationColumn) -> dict: ...

    def __call__(self, name: str | None = None) -> DatabaseInformationDatabase | DatabaseInformationTable | DatabaseInformationColumn | list[dict] | dict:
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
    def __getattr__(self: DatabaseInformationSchema, name: str) -> DatabaseInformationDatabase: ...

    @overload
    def __getattr__(self: DatabaseInformationDatabase, name: str) -> DatabaseInformationTable: ...

    @overload
    def __getattr__(self: DatabaseInformationTable, name: str) -> DatabaseInformationColumn: ...

    def __getattr__(self, name: str) -> DatabaseInformationDatabase | DatabaseInformationTable | DatabaseInformationColumn:
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
            case DatabaseInformationSchema():
                table = DatabaseInformationDatabase(self._rdatabase, name)
            case DatabaseInformationDatabase():
                table = DatabaseInformationTable(self._rdatabase, self._database_name, name)
            case DatabaseInformationTable():
                table = DatabaseInformationColumn(self._rdatabase, self._database_name, self._table_name, name)
            case _:
                raise AssertionError("class '%s' does not have this method" % type(self).__name__)

        return table


class DatabaseInformationSchema(DatabaseInformation):
    """
    Database information schema type.

    Examples
    --------
    Get databases information of server.
    >>> databases_info = DatabaseInformationSchema()

    Get tables information of database.
    >>> tables_info = DatabaseInformationSchema.database()

    Get columns information of table.
    >>> columns_info = DatabaseInformationSchema.database.table()

    Get column information.
    >>> column_info = DatabaseInformationSchema.database.table.column()

    Get database attribute.
    >>> database_attr = DatabaseInformationSchema.database['attribute']

    Get table attribute.
    >>> database_attr = DatabaseInformationSchema.database.table['attribute']

    Get column attribute.
    >>> database_attr = DatabaseInformationSchema.database.table.column['attribute']
    """


    def __init__(
        self,
        rdatabase: Database | DatabaseConnection
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rdatabase : Database or DatabaseConnection instance.
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


class DatabaseInformationDatabase(DatabaseInformation):
    """
    Database information database type.

    Examples
    --------
    Get tables information of database.
    >>> tables_info = DatabaseInformationDatabase()

    Get columns information of table.
    >>> columns_info = DatabaseInformationDatabase.table()

    Get column information.
    >>> column_info = DatabaseInformationDatabase.table.column()

    Get database attribute.
    >>> database_attr = DatabaseInformationDatabase['attribute']

    Get table attribute.
    >>> database_attr = DatabaseInformationDatabase.table['attribute']

    Get column attribute.
    >>> database_attr = DatabaseInformationDatabase.table.column['attribute']
    """


    def __init__(
        self,
        rdatabase: Database | DatabaseConnection,
        database_name: str
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rdatabase : Database or DatabaseConnection instance.
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


class DatabaseInformationTable(DatabaseInformation):
    """
    Database information table type.

    Examples
    --------
    Get columns information of table.
    >>> columns_info = DatabaseInformationTable()

    Get column information.
    >>> column_info = DatabaseInformationTable.column()

    Get table attribute.
    >>> database_attr = DatabaseInformationTable['attribute']

    Get column attribute.
    >>> database_attr = DatabaseInformationTable.column['attribute']
    """


    def __init__(
        self,
        rdatabase: Database | DatabaseConnection,
        database_name: str,
        table_name: str
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rdatabase : Database or DatabaseConnection instance.
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


class DatabaseInformationColumn(DatabaseInformation):
    """
    Database information column type.

    Examples
    --------
    Get column information.
    >>> column_info = DatabaseInformationColumn()

    Get column attribute.
    >>> database_attr = DatabaseInformationColumn['attribute']
    """


    def __init__(
        self,
        rdatabase: Database | DatabaseConnection,
        database_name: str,
        table_name: str,
        column_name: str
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rdatabase : Database or DatabaseConnection instance.
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
