# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database information methods.
"""


from __future__ import annotations
from typing import Any, List, Dict, Union, Literal, Optional, overload

from .rconnection import RDatabase, RDBConnection


__all__ = (
    "RDBInformation",
    "RDBISchema",
    "RDBIDatabase",
    "RDBITable",
    "RDBIColumn"
)


class RDBInformation(object):
    """
    Rey's `database base information` type.
    """


    @overload
    def __call__(self: RDBISchema, name: Optional[str] = None) -> Union[RDBIDatabase, List[Dict]]: ...

    @overload
    def __call__(self: RDBIDatabase, name: Optional[str] = None) -> Union[RDBITable, List[Dict]]: ...

    @overload
    def __call__(self: RDBITable, name: Optional[str] = None) -> Union[RDBIColumn, List[Dict]]: ...

    @overload
    def __call__(self: RDBIColumn, name: Optional[str] = None) -> Dict: ...

    def __call__(self, name: Optional[str] = None) -> Union[
        RDBIDatabase,
        RDBITable,
        RDBIColumn,
        List[Dict],
        Dict
    ]:
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
            if not hasattr(self, "_get_info_table"):
                raise AssertionError("class '%s' does not have this method" % self.__class__.__name__)

            ## Get.
            result: List[Dict] = self._get_info_table()

        # Subobject.
        else:

            ## Break.
            if not hasattr(self, "__getattr__"):
                raise AssertionError("class '%s' does not have this method" % self.__class__.__name__)

            ## Get.
            result = self.__getattr__(name)

        return result


    @overload
    def __getitem__(self, key: Literal["*", "all", "ALL"]) -> Dict: ...

    @overload
    def __getitem__(self, key: str) -> Any: ...

    def __getitem__(self, key: str) -> Any:
        """
        Get information attribute value or dictionary.

        Parameters
        ----------
        key : Attribute key. When key not exist, then try all caps key.
            - `Literal['*', 'all', 'ALL']` : Get attribute dictionary.
            - `str` : Get attribute value.

        Returns
        -------
        Information attribute value or dictionary.
        """

        # Break.
        if not hasattr(self, "_get_info_attrs"):
            raise AssertionError("class '%s' does not have this method" % self.__class__.__name__)

        # Get.
        info_attrs: Dict = self._get_info_attrs()

        # Return.

        ## Dictionary.
        if key in ("*", "all", "ALL"):
            return info_attrs

        ## Value.
        info_attr = info_attrs.get(key)
        if info_attr is None:
            key_upper = key.upper()
            info_attr = info_attrs[key_upper]
        return info_attr


    @overload
    def __getattr__(self, key: Literal["_rdatabase"]) -> Union[RDatabase, RDBConnection]: ...

    @overload
    def __getattr__(self, key: Literal["_database_name", "_table_name"]) -> str: ...

    @overload
    def __getattr__(self: RDBISchema, key: str) -> RDBIDatabase: ...

    @overload
    def __getattr__(self: RDBIDatabase, key: str) -> RDBITable: ...

    @overload
    def __getattr__(self: RDBITable, key: str) -> RDBIColumn: ...

    def __getattr__(self, key: str) -> Union[
        Union[RDatabase, RDBConnection],
        str,
        RDBIDatabase,
        RDBITable,
        RDBIColumn
    ]:
        """
        Get attribute or build subclass instance.

        Parameters
        ----------
        key : Attribute key or table name.

        Returns
        -------
        Attribute or subclass instance.
        """

        # Filter private
        if key in ("_rdatabase", "_database_name", "_table_name"):
            return self.__dict__[key]

        # Build.
        if self.__class__ == RDBISchema:
            rtable = RDBIDatabase(self._rdatabase, key)
        elif self.__class__ == RDBIDatabase:
            rtable = RDBITable(self._rdatabase, self._database_name, key)
        elif self.__class__ == RDBITable:
            rtable = RDBIColumn(self._rdatabase, self._database_name, self._table_name, key)
        else:
            raise AssertionError("class '%s' does not have this method" % self.__class__.__name__)

        return rtable


class RDBISchema(RDBInformation):
    """
    Rey's `database information schema` type.

    Examples
    --------
    Get databases information of server.
    >>> databases_info = RDBISchema()

    Get tables information of database.
    >>> tables_info = RDBISchema.database()

    Get columns information of table.
    >>> columns_info = RDBISchema.database.table()

    Get column information.
    >>> column_info = RDBISchema.database.table.column()

    Get database attribute.
    >>> database_attr = RDBISchema.database["attribute"]

    Get table attribute.
    >>> database_attr = RDBISchema.database.table["attribute"]

    Get column attribute.
    >>> database_attr = RDBISchema.database.table.column["attribute"]
    """


    def __init__(
        self,
        rdatabase: Union[RDatabase, RDBConnection]
    ) -> None:
        """
        Build `database information schema` instance.

        Parameters
        ----------
        rdatabase : RDatabase or RDBConnection instance.
        """

        # Set parameter.
        self._rdatabase = rdatabase


    def _get_info_table(self) -> List[Dict]:
        """
        Get information table.

        Returns
        -------
        Information table.
        """

        # Select.
        result = self._rdatabase.execute_select(
            "information_schema.SCHEMATA",
            order="`schema_name`"
        )

        # Convert.
        info_table = result.fetch_table()

        return info_table


class RDBIDatabase(RDBInformation):
    """
    Rey's `database information database` type.

    Examples
    --------
    Get tables information of database.
    >>> tables_info = RDBIDatabase()

    Get columns information of table.
    >>> columns_info = RDBIDatabase.table()

    Get column information.
    >>> column_info = RDBIDatabase.table.column()

    Get database attribute.
    >>> database_attr = RDBIDatabase["attribute"]

    Get table attribute.
    >>> database_attr = RDBIDatabase.table["attribute"]

    Get column attribute.
    >>> database_attr = RDBIDatabase.table.column["attribute"]
    """


    def __init__(
        self,
        rdatabase: Union[RDatabase, RDBConnection],
        database_name: str
    ) -> None:
        """
        Build `database information database` instance.

        Parameters
        ----------
        rdatabase : RDatabase or RDBConnection instance.
        database_name : Database name.
        """

        # Set parameter.
        self._rdatabase = rdatabase
        self._database_name = database_name


    def _get_info_attrs(self) -> Dict:
        """
        Get information attribute dictionary.

        Returns
        -------
        Information attribute dictionary.
        """

        # Select.
        where = "`SCHEMA_NAME` = :database_name"
        result = self._rdatabase.execute_select(
            "information_schema.SCHEMATA",
            where=where,
            limit=1,
            database_name=self._database_name
        )

        # Check.
        assert result.exist, "database '%s' not exist" % self._database_name

        # Convert.
        info_table = result.fetch_table()
        info_attrs = info_table[0]

        return info_attrs


    def _get_info_table(self) -> List[Dict]:
        """
        Get information table.

        Returns
        -------
        Information table.
        """

        # Select.
        where = "`TABLE_SCHEMA` = :database_name"
        result = self._rdatabase.execute_select(
            "information_schema.TABLES",
            where=where,
            order="`TABLE_NAME`",
            database_name=self._database_name
        )

        # Check.
        assert result.exist, "database '%s' not exist" % self._database_name

        # Convert.
        info_table = result.fetch_table()

        return info_table


class RDBITable(RDBInformation):
    """
    Rey's `database information table` type.

    Examples
    --------
    Get columns information of table.
    >>> columns_info = RDBITable()

    Get column information.
    >>> column_info = RDBITable.column()

    Get table attribute.
    >>> database_attr = RDBITable["attribute"]

    Get column attribute.
    >>> database_attr = RDBITable.column["attribute"]
    """


    def __init__(
        self,
        rdatabase: Union[RDatabase, RDBConnection],
        database_name: str,
        table_name: str
    ) -> None:
        """
        Build `database information table` instance.

        Parameters
        ----------
        rdatabase : RDatabase or RDBConnection instance.
        database_name : Database name.
        table_name : Table name.
        """

        # Set parameter.
        self._rdatabase = rdatabase
        self._database_name = database_name
        self._table_name = table_name


    def _get_info_attrs(self) -> Dict:
        """
        Get information attribute dictionary.

        Returns
        -------
        Information attribute dictionary.
        """

        # Select.
        where = "`TABLE_SCHEMA` = :database_name AND `TABLE_NAME` = :table_name"
        result = self._rdatabase.execute_select(
            "information_schema.TABLES",
            where=where,
            limit=1,
            database_name=self._database_name,
            table_name=self._table_name
        )

        # Check.
        assert result.exist, "database '%s' or table '%s' not exist" % (self._database_name, self._table_name)

        # Convert.
        info_table = result.fetch_table()
        info_attrs = info_table[0]

        return info_attrs


    def _get_info_table(self) -> List[Dict]:
        """
        Get information table.

        Returns
        -------
        Information table.
        """

        # Select.
        where = "`TABLE_SCHEMA` = :database_name AND `TABLE_NAME` = :table_name"
        result = self._rdatabase.execute_select(
            "information_schema.COLUMNS",
            where=where,
            order="`ORDINAL_POSITION`",
            database_name=self._database_name,
            table_name=self._table_name
        )

        # Check.
        assert result.exist, "database '%s' or table '%s' not exist" % (self._database_name, self._table_name)

        # Convert.
        info_table = result.fetch_table()

        return info_table


class RDBIColumn(RDBInformation):
    """
    Rey's `database information column` type.

    Examples
    --------
    Get column information.
    >>> column_info = RDBIColumn()

    Get column attribute.
    >>> database_attr = RDBIColumn["attribute"]
    """


    def __init__(
        self,
        rdatabase: Union[RDatabase, RDBConnection],
        database_name: str,
        table_name: str,
        column_name: str
    ) -> None:
        """
        Build `database information column` instance.

        Parameters
        ----------
        rdatabase : RDatabase or RDBConnection instance.
        database_name : Database name.
        table_name : Table name.
        column_name : Column name.
        """

        # Set parameter.
        self._rdatabase = rdatabase
        self._database_name = database_name
        self._table_name = table_name
        self._column_name = column_name


    def _get_info_attrs(self) -> Dict:
        """
        Get information attribute dictionary.

        Returns
        -------
        Information attribute dictionary.
        """

        # Select.
        where = "`TABLE_SCHEMA` = :database_name AND `TABLE_NAME` = :table_name AND `COLUMN_NAME` = :column_name"
        result = self._rdatabase.execute_select(
            "information_schema.COLUMNS",
            where=where,
            limit=1,
            database_name=self._database_name,
            table_name=self._table_name,
            column_name=self._column_name
        )

        # Check.
        assert result.exist, "database '%s' or table '%s' or column '%s' not exist" % (self._database_name, self._table_name, self._column_name)

        # Convert.
        info_table = result.fetch_table()
        info_attrs = info_table[0]

        return info_attrs


    _get_info_table = _get_info_attrs