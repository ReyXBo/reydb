# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database parameter methods.
"""


from typing import Literal, TypeVar, Generic, Final, overload

from . import rdb
from .rbase import DatabaseBase
from .rexec import Result


__all__ = (
    'DatabaseSchemaSuper',
    'DatabaseSchema',
    'DatabaseSchemaAsync',
    'DatabaseParametersSuper',
    'DatabaseParameters',
    'DatabaseParametersAsync',
    'DatabaseParametersVariables',
    'DatabaseParametersStatus',
    'DatabaseParametersVariablesGlobal',
    'DatabaseParametersStatusGlobal',
    'DatabaseParametersVariablesAsync',
    'DatabaseParametersStatusAsync',
    'DatabaseParametersVariablesGlobalAsync',
    'DatabaseParametersStatusGlobalAsync'
)


DatabaseT = TypeVar('DatabaseT', 'rdb.Database', 'rdb.DatabaseAsync')


class DatabaseSchemaSuper(DatabaseBase, Generic[DatabaseT]):
    """
    Database schema super type.
    """


    def __init__(self, db: DatabaseT) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: Database instance.
        """

        # Set parameter.
        self.db = db

    def handle_before__call__(self, filter_default: bool = True) -> tuple[str, tuple[str, ...]]:
        """
        Before handle method of call method.

        Parameters
        ----------
        filter_default : Whether filter default database.

        Returns
        -------
        Parameter `sql` and `filter_db`.
        """

        # Handle parameter.
        filter_db = (
            'information_schema',
            'performance_schema',
            'mysql',
            'sys'
        )
        if filter_default:
            where_database = 'WHERE `SCHEMA_NAME` NOT IN :filter_db\n'
            where_column = '    WHERE `TABLE_SCHEMA` NOT IN :filter_db\n'
        else:
            where_database = where_column = ''

        # Select.
        sql = (
            'SELECT GROUP_CONCAT(`SCHEMA_NAME`) AS `TABLE_SCHEMA`, NULL AS `TABLE_NAME`, NULL AS `COLUMN_NAME`\n'
            'FROM `information_schema`.`SCHEMATA`\n'
            f'{where_database}'
            'UNION ALL (\n'
            '    SELECT `TABLE_SCHEMA`, `TABLE_NAME`, `COLUMN_NAME`\n'
            '    FROM `information_schema`.`COLUMNS`\n'
            f'{where_column}'
            '    ORDER BY `TABLE_SCHEMA`, `TABLE_NAME`, `ORDINAL_POSITION`\n'
            ')'
        )

        return sql, filter_db


    def handle_after__call__(self, result: Result) -> dict[str, dict[str, list[str]]]:
        """
        After handle method of call method.

        Parameters
        ----------
        result : Database select result.

        Returns
        -------
        Parameter `schema_dict`.
        """

        # Convert.
        database_names, *_ = result.fetchone()
        database_names: list[str] = database_names.split(',')
        schema_dict = {}
        for database, table, column in result:
            if database in database_names:
                database_names.remove(database)

            ## Index database.
            if database not in schema_dict:
                schema_dict[database] = {table: [column]}
                continue
            table_dict: dict = schema_dict[database]

            ## Index table. 
            if table not in table_dict:
                table_dict[table] = [column]
                continue
            column_list: list = table_dict[table]

            ## Add column.
            column_list.append(column)

        ## Add empty database.
        for name in database_names:
            schema_dict[name] = None

        return schema_dict


    @overload
    def handle_exist(
        self,
        schema: dict[str, dict[str, list[str]]],
        database: str
    ) -> bool: ...

    @overload
    def handle_exist(
        self,
        schema: dict[str, dict[str, list[str]]],
        database: str,
        table: str
    ) -> bool: ...

    @overload
    def handle_exist(
        self,
        schema: dict[str, dict[str, list[str]]],
        database: str,
        table: str,
        column: str
    ) -> bool: ...

    def handle_exist(
        self,
        schema: dict[str, dict[str, list[str]]],
        database: str,
        table: str | None = None,
        column: str | None = None
    ) -> bool:
        """
        Handle method of judge database or table or column whether it exists.

        Parameters
        ----------
        schema : Schemata of databases and tables and columns.
        database : Database name.
        table : Table name.
        column : Column name.

        Returns
        -------
        Judge result.
        """

        # Handle parameter.

        # Judge.
        judge = (
            database in schema
            and (
                table is None
                or (
                    (database_info := schema.get(database)) is not None
                    and (table_info := database_info.get(table)) is not None
                )
            )
            and (
                column is None
                or column in table_info
            )
        )

        return judge


class DatabaseSchema(DatabaseSchemaSuper['rdb.Database']):
    """
    Database schema type.
    """


    def schema(self, filter_default: bool = True) -> dict[str, dict[str, list[str]]]:
        """
        Get schemata of databases and tables and columns.

        Parameters
        ----------
        filter_default : Whether filter default database.

        Returns
        -------
        Schemata of databases and tables and columns.
        """

        # Get.
        sql, filter_db = self.handle_before__call__(filter_default)
        result = self.db.execute(sql, filter_db=filter_db)
        schema = self.handle_after__call__(result)

        # Cache.
        if self.db._schema is None:
            self.db._schema = schema
        else:
            self.db._schema.update(schema)

        return schema


    __call__ = schema


    @overload
    def exist(
        self,
        database: str,
        *,
        refresh: bool = True
    ) -> bool: ...

    @overload
    def exist(
        self,
        database: str,
        *,
        table: str,
        refresh: bool = True
    ) -> bool: ...

    @overload
    def exist(
        self,
        database: str,
        table: str,
        column: str,
        refresh: bool = True
    ) -> bool: ...

    def exist(
        self,
        database: str,
        table: str | None = None,
        column: str | None = None,
        refresh: bool = True
    ) -> bool:
        """
        Judge database or table or column whether it exists.

        Parameters
        ----------
        database : Database name.
        table : Table name.
        column : Column name.
        refresh : Whether refresh cache data. Cache can improve efficiency.

        Returns
        -------
        Judge result.
        """

        # Handle parameter.
        if (
            refresh
            or self.db._schema is None
        ):
            schema = self.schema()
        else:
            schema = self.db._schema

        # Judge.
        result = self.handle_exist(schema, database, table, column)

        return result


class DatabaseSchemaAsync(DatabaseSchemaSuper['rdb.DatabaseAsync']):
    """
    Asynchronous database schema type.
    """


    async def schema(self, filter_default: bool = True) -> dict[str, dict[str, list[str]]]:
        """
        Asynchronous get schemata of databases and tables and columns.

        Parameters
        ----------
        filter_default : Whether filter default database.

        Returns
        -------
        Schemata of databases and tables and columns.
        """

        # Get.
        sql, filter_db = self.handle_before__call__(filter_default)
        result = await self.db.execute(sql, filter_db=filter_db)
        schema = self.handle_after__call__(result)

        # Cache.
        if self.db._schema is not None:
            self.db._schema.update(schema)

        return schema


    __call__ = schema


    @overload
    async def exist(
        self,
        database: str,
        *,
        refresh: bool = True
    ) -> bool: ...

    @overload
    async def exist(
        self,
        database: str,
        *,
        table: str,
        refresh: bool = True
    ) -> bool: ...

    @overload
    async def exist(
        self,
        database: str,
        table: str,
        column: str,
        refresh: bool = True
    ) -> bool: ...

    async def exist(
        self,
        database: str,
        table: str | None = None,
        column: str | None = None,
        refresh: bool = True
    ) -> bool:
        """
        Asynchronous judge database or table or column whether it exists.

        Parameters
        ----------
        database : Database name.
        table : Table name.
        column : Column name.
        refresh : Whether refresh cache data. Cache can improve efficiency.

        Returns
        -------
        Judge result.
        """

        # Handle parameter.
        if (
            refresh
            or self.db._schema is None
        ):
            schema = await self.schema()
        else:
            schema = self.db._schema

        # Judge.
        result = self.handle_exist(schema, database, table, column)

        return result


class DatabaseParametersSuper(DatabaseBase, Generic[DatabaseT]):
    """
    Database parameters super type.
    """

    mode: Literal['VARIABLES', 'STATUS']
    glob: bool


    def __init__(
        self,
        db: DatabaseT
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: Database instance.
        """

        # Set parameter.
        self.db = db


class DatabaseParameters(DatabaseParametersSuper['rdb.Database']):
    """
    Database parameters type.
    """


    def __getitem__(self, key: str) -> str | None:
        """
        Get item of parameter dictionary.

        Parameters
        ----------
        key : Parameter key.

        Returns
        -------
        Parameter value.
        """

        # Get.
        value = self.get(key)

        return value


    def __setitem__(self, key: str, value: str | float) -> None:
        """
        Set item of parameter dictionary.

        Parameters
        ----------
        key : Parameter key.
        value : Parameter value.
        """

        # Set.
        params = {key: value}

        # Update.
        self.update(params)


    @overload
    def get(self) -> dict[str, str]: ...

    @overload
    def get(self, key: str) -> str | None: ...

    def get(self, key: str | None = None) -> dict[str, str] | str | None:
        """
        Get parameter.

        Parameters
        ----------
        key : Parameter key.
            - `None`: Return dictionary of all parameters.
            - `str`: Return value of parameter.

        Returns
        -------
        Status of database.
        """

        # Generate SQL.
        sql = 'SHOW ' + (
            'GLOBAL '
            if self.glob
            else ''
        ) + self.mode

        # Execute SQL.

        ## Dictionary.
        if key is None:
            result = self.db.execute(sql, key=key)
            status = result.to_dict(val_field=1)

        ## Value.
        else:
            sql += ' LIKE :key'
            result = self.db.execute(sql, key=key)
            row = result.first()
            if row is None:
                status = None
            else:
                status = row['Value']

        return status


    def update(self, params: dict[str, str | float]) -> None:
        """
        Update parameter.

        Parameters
        ----------
        params : Update parameter key value pairs.
        """

        # Generate SQL.
        sql_set_list = [
            '%s = %s' % (
                key,
                (
                    value
                    if type(value) in (int, float)
                    else "'%s'" % value
                )
            )
            for key, value in params.items()
        ]
        sql_set = ',\n    '.join(sql_set_list)
        sql = 'SHOW ' + (
            'GLOBAL '
            if self.glob
            else ''
        ) + sql_set

        # Execute SQL.
        self.db.execute(sql)


class DatabaseParametersAsync(DatabaseParametersSuper['rdb.DatabaseAsync']):
    """
    Asynchrouous database parameters type.
    """


    async def __getitem__(self, key: str) -> str | None:
        """
        Asynchrouous get item of parameter dictionary.

        Parameters
        ----------
        key : Parameter key.

        Returns
        -------
        Parameter value.
        """

        # Get.
        value = await self.get(key)

        return value


    async def __setitem__(self, key: str, value: str | float) -> None:
        """
        Asynchrouous set item of parameter dictionary.

        Parameters
        ----------
        key : Parameter key.
        value : Parameter value.
        """

        # Set.
        params = {key: value}

        # Update.
        await self.update(params)


    @overload
    async def get(self) -> dict[str, str]: ...

    @overload
    async def get(self, key: str) -> str | None: ...

    async def get(self, key: str | None = None) -> dict[str, str] | str | None:
        """
        Asynchrouous get parameter.

        Parameters
        ----------
        key : Parameter key.
            - `None`: Return dictionary of all parameters.
            - `str`: Return value of parameter.

        Returns
        -------
        Status of database.
        """

        # Generate SQL.
        sql = 'SHOW ' + (
            'GLOBAL '
            if self.glob
            else ''
        ) + self.mode

        # Execute SQL.

        ## Dictionary.
        if key is None:
            result = await self.db.execute(sql, key=key)
            status = result.to_dict(val_field=1)

        ## Value.
        else:
            sql += ' LIKE :key'
            result = await self.db.execute(sql, key=key)
            row = result.first()
            if row is None:
                status = None
            else:
                status = row['Value']

        return status


    async def update(self, params: dict[str, str | float]) -> None:
        """
        Asynchrouous update parameter.

        Parameters
        ----------
        params : Update parameter key value pairs.
        """

        # Check.
        if self.mode == 'STATUS':
            raise AssertionError('database status not update')

        # Generate SQL.
        sql_set_list = [
            '%s = %s' % (
                key,
                (
                    value
                    if type(value) in (int, float)
                    else "'%s'" % value
                )
            )
            for key, value in params.items()
        ]
        sql_set = ',\n    '.join(sql_set_list)
        sql = 'SHOW ' + (
            'GLOBAL '
            if self.glob
            else ''
        ) + sql_set

        # Execute SQL.
        await self.db.execute(sql)


class DatabaseParametersVariables(DatabaseParameters):
    """
    Database variable parameters type.
    """

    mode: Final = 'VARIABLES'
    glob: Final = False


class DatabaseParametersStatus(DatabaseParameters):
    """
    Database status parameters type.
    """

    mode: Final = 'STATUS'
    glob: Final = False


class DatabaseParametersVariablesGlobal(DatabaseParameters):
    """
    Database global variable parameters type.
    """

    mode: Final = 'VARIABLES'
    glob: Final = True


class DatabaseParametersStatusGlobal(DatabaseParameters):
    """
    Database global status parameters type.
    """

    mode: Final = 'STATUS'
    glob: Final = True


class DatabaseParametersVariablesAsync(DatabaseParametersAsync):
    """
    Asynchrouous database variable parameters type.
    """

    mode: Final = 'VARIABLES'
    glob: Final = False


class DatabaseParametersStatusAsync(DatabaseParametersAsync):
    """
    Asynchrouous database status parameters type.
    """

    mode: Final = 'STATUS'
    glob: Final = False


class DatabaseParametersVariablesGlobalAsync(DatabaseParametersAsync):
    """
    Asynchrouous database global variable parameters type.
    """

    mode: Final = 'VARIABLES'
    glob: Final = True


class DatabaseParametersStatusGlobalAsync(DatabaseParametersAsync):
    """
    Asynchrouous database global status parameters type.
    """

    mode: Final = 'STATUS'
    glob: Final = True
