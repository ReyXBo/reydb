# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database parameter methods.
"""


from typing import Generic, overload

from . import rdb
from .rbase import DatabaseT, DatabaseBase
from .rexec import Result


__all__ = (
    'DatabaseSchema',
    'DatabaseParameters',
    'DatabaseParametersStatus',
    'DatabaseParametersVariable'
)


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


    def _call__before(self, filter_default: bool = True) -> tuple[str, tuple[str, ...]]:
        """
        Before handle of call method.

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


    def _call__after(self, result: Result) -> dict[str, dict[str, list[str]]]:
        """
        After handle of call method.

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


class DatabaseSchema(DatabaseSchemaSuper['rdb.Database']):
    """
    Database schema type.
    """


    def __call__(self, filter_default: bool = True) -> dict[str, dict[str, list[str]]]:
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
        sql, filter_db = self._call__before(filter_default)
        result = self.db.execute(sql, filter_db=filter_db)
        schema_dict = self._call__after(result)

        return schema_dict


class DatabaseSchemaAsync(DatabaseSchemaSuper['rdb.DatabaseAsync']):
    """
    Asynchronous database schema type.
    """


    async def __call__(self, filter_default: bool = True) -> dict[str, dict[str, list[str]]]:
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
        sql, filter_db = self._call__before(filter_default)
        result = await self.db.execute(sql, filter_db=filter_db)
        schema_dict = self._call__after(result)

        return schema_dict


class DatabaseParameters(DatabaseBase):
    """
    Database parameters type.
    """


    def __init__(
        self,
        db: 'rdb.Database',
        global_: bool
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: Database instance.
        global\\_ : Whether base global.
        """

        # Set parameter.
        self.db = db
        self.global_ = global_


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


class DatabaseParametersStatus(DatabaseParameters):
    """
    Database parameters status type.
    """


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

        ## Global.
        if self.global_:
            sql = 'SHOW GLOBAL STATUS'

        ## Not global.
        else:
            sql = 'SHOW STATUS'

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

        # Throw exception.
        raise AssertionError('database status not update')


class DatabaseParametersVariable(DatabaseParameters):
    """
    Database parameters variable type.
    """


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
        Variables of database.
        """

        # Generate SQL.

        ## Global.
        if self.global_:
            sql = 'SHOW GLOBAL VARIABLES'

        ## Not global.
        else:
            sql = 'SHOW VARIABLES'

        # Execute SQL.

        ## Dictionary.
        if key is None:
            result = self.db.execute(sql, key=key)
            variables = result.to_dict(val_field=1)

        ## Value.
        else:
            sql += ' LIKE :key'
            result = self.db.execute(sql, key=key)
            row = result.first()
            if row is None:
                variables = None
            else:
                variables = row['Value']

        return variables


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

        ## Global.
        if self.global_:
            sql = f'SET GLOBAL {sql_set}'

        ## Not global.
        else:
            sql = f'SET {sql_set}'

        # Execute SQL.
        self.db.execute(sql)
