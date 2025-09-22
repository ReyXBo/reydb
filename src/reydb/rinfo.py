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

from .rbase import DatabaseBase
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
                table = DatabaseInformationDatabase(self.db, name)
            case DatabaseInformationDatabase():
                table = DatabaseInformationTable(self.db, self.database, name)
            case DatabaseInformationTable():
                table = DatabaseInformationColumn(self.db, self.database, self.table, name)
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
        db: Database
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: Database instance.
        """

        # Set parameter.
        self.db = db


    def _get_info_table(self) -> list[dict]:
        """
        Get information table.

        Returns
        -------
        Information table.
        """

        # Select.
        result = self.db.execute.select(
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
        db: Database,
        database: str
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: Database instance.
        database : Database name.
        """

        # Set parameter.
        self.db = db
        self.database = database


    def _get_info_attrs(self) -> dict:
        """
        Get information attribute dictionary.

        Returns
        -------
        Information attribute dictionary.
        """

        # Select.
        where = '`SCHEMA_NAME` = :database'
        result = self.db.execute.select(
            'information_schema.SCHEMATA',
            where=where,
            limit=1,
            database=self.database
        )

        # Convert.
        info_table = result.to_table()

        ## Check.
        assert len(info_table) != 0, "database '%s' not exist" % self.database

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
        where = '`TABLE_SCHEMA` = :database'
        result = self.db.execute.select(
            'information_schema.TABLES',
            where=where,
            order='`TABLE_NAME`',
            database=self.database
        )

        # Convert.
        info_table = result.to_table()

        ## Check.
        assert len(info_table) != 0, "database '%s' not exist" % self.database

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
        db: Database,
        database: str,
        table: str
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: Database instance.
        database : Database name.
        table : Table name.
        """

        # Set parameter.
        self.db = db
        self.database = database
        self.table = table


    def _get_info_attrs(self) -> dict:
        """
        Get information attribute dictionary.

        Returns
        -------
        Information attribute dictionary.
        """

        # Select.
        where = '`TABLE_SCHEMA` = :database AND `TABLE_NAME` = :table_'
        result = self.db.execute.select(
            'information_schema.TABLES',
            where=where,
            limit=1,
            database=self.database,
            table_=self.table
        )

        # Convert.
        info_table = result.to_table()

        ## Check.
        assert len(info_table) != 0, "database '%s' or table '%s' not exist" % (self.database, self.table)

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
        where = '`TABLE_SCHEMA` = :database AND `TABLE_NAME` = :table_'
        result = self.db.execute.select(
            'information_schema.COLUMNS',
            where=where,
            order='`ORDINAL_POSITION`',
            database=self.database,
            table_=self.table
        )

        # Convert.
        info_table = result.to_table()

        ## Check.
        assert len(info_table) != 0, "database '%s' or table '%s' not exist" % (self.database, self.table)

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
        db: Database,
        database: str,
        table: str,
        column: str
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: Database instance.
        database : Database name.
        table : Table name.
        column : Column name.
        """

        # Set parameter.
        self.db = db
        self.database = database
        self.table = table
        self.column = column


    def _get_info_attrs(self) -> dict:
        """
        Get information attribute dictionary.

        Returns
        -------
        Information attribute dictionary.
        """

        # Select.
        where = '`TABLE_SCHEMA` = :database AND `TABLE_NAME` = :table_ AND `COLUMN_NAME` = :column'
        result = self.db.execute.select(
            'information_schema.COLUMNS',
            where=where,
            limit=1,
            database=self.database,
            table_=self.table,
            column=self.column
        )

        # Convert.
        info_table = result.to_table()

        ## Check.
        assert len(info_table) != 0, "database '%s' or table '%s' or column '%s' not exist" % (self.database, self.table, self.column)

        info_attrs = info_table[0]

        return info_attrs


    _get_info_table = _get_info_attrs
