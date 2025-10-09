# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-08-22
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database config methods.
"""


from typing import Any, TypedDict, TypeVar, Generic
from datetime import (
    datetime as Datetime,
    date as Date,
    time as Time,
    timedelta as Timedelta
)
from reykit.rbase import Null, throw

from . import rengine
from . import rorm
from .rbase import DatabaseBase


__all__ = (
    'DatabaseORMTableConfig',
    'DatabaseConfigSuper',
    'DatabaseConfig',
    'DatabaseConfigAsync'
)


type ConfigValue = bool | str | int | float | list | tuple | dict | set | Datetime | Date | Time | Timedelta | None
ConfigRow = TypedDict('ConfigRow', {'key': str, 'value': ConfigValue, 'note': str | None})
type ConfigTable = list[ConfigRow]
ConfigValueT = TypeVar('T', bound=ConfigValue) # Any.
DatabaseEngineT = TypeVar('DatabaseEngineT', 'rengine.DatabaseEngine', 'rengine.DatabaseEngineAsync')


class DatabaseORMTableConfig(rorm.Model, table=True):
    """
    Database `config` table ORM model.
    """

    __name__ = 'config'
    __comment__ = 'Config data table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Config create time.')
    update_time: rorm.Datetime = rorm.Field(field_default=':update_time', index_n=True, comment='Config update time.')
    key: str = rorm.Field(rorm.types.VARCHAR(50), key=True, comment='Config key.')
    value: str = rorm.Field(rorm.types.TEXT, not_null=True, comment='Config value.')
    type: str = rorm.Field(rorm.types.VARCHAR(50), not_null=True, comment='Config value type.')
    note: str = rorm.Field(rorm.types.VARCHAR(500), comment='Config note.')


class DatabaseConfigSuper(DatabaseBase, Generic[DatabaseEngineT]):
    """
    Database config super type.
    Can create database used `self.build_db` method.
    """

    _checked: bool = False


    def __init__(self, engine: DatabaseEngineT) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        engine: Database engine.
        """

        # Build.
        self.engine = engine

        # Build Database.
        if not self._checked:
            if type(self) == DatabaseConfig:
                self.build_db()
            elif type(self) == DatabaseConfigAsync:
                engine.sync_engine.config.build_db()
            self._checked = True


    def handle_build_db(self) -> tuple[list[type[DatabaseORMTableConfig]], list[dict[str, Any]]] :
        """
        Handle method of check and build database tables.

        Returns
        -------
        Build database parameter.
        """

        # Parameter.
        database = self.engine.database

        ## Table.
        tables = [DatabaseORMTableConfig]

        ## View stats.
        views_stats = [
            {
                'path': 'stats_config',
                'items': [
                    {
                        'name': 'count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{database}`.`config`'
                        ),
                        'comment': 'Config count.'
                    },
                    {
                        'name': 'last_create_time',
                        'select': (
                            'SELECT MAX(`create_time`)\n'
                            f'FROM `{database}`.`config`'
                        ),
                        'comment': 'Config last record create time.'
                    },
                    {
                        'name': 'last_update_time',
                        'select': (
                            'SELECT MAX(`update_time`)\n'
                            f'FROM `{database}`.`config`'
                        ),
                        'comment': 'Config last record update time.'
                    }
                ]
            }
        ]

        return tables, views_stats


class DatabaseConfig(DatabaseConfigSuper['rengine.DatabaseEngine']):
    """
    Database config type.
    Can create database used `self.build_db` method.

    Examples
    --------
    >>> config = DatabaseConfig()
    >>> config['key1'] = 1
    >>> config['key2', 'note'] = 2
    >>> config['key1'], config['key2']
    (1, 2)
    """


    def build_db(self) -> None:
        """
        Check and build database tables.
        """

        # Parameter.
        tables, views_stats = self.handle_build_db()

        # Build.
        self.engine.build.build(tables=tables, views_stats=views_stats, skip=True)


    def data(self) -> ConfigTable:
        """
        Get config data table.

        Returns
        -------
        Config data table.
        """

        # Get.
        result = self.engine.execute.select(
            'config',
            ['key', 'value', 'note'],
            order='IFNULL(`update_time`, `create_time`) DESC'
        )

        # Convert.
        global_dict = {'datetime': Datetime}
        result = [
            {
                'key': row['key'],
                'value': eval(row['value'], global_dict),
                'note': row['note']
            }
            for row in result
        ]

        return result


    def get(self, key: str, default: ConfigValueT | None = None) -> ConfigValue | ConfigValueT:
        """
        Get config value, when not exist, then return default value.

        Parameters
        ----------
        key : Config key.
        default : Config default value.

        Returns
        -------
        Config value.
        """

        # Get.
        where = '`key` = :key'
        result = self.engine.execute.select(
            'config',
            '`value`',
            where,
            limit=1,
            key=key
        )
        value = result.scalar()

        # Default.
        if value is None:
            value = default
        else:
            global_dict = {'datetime': Datetime}
            value = eval(value, global_dict)

        return value


    def setdefault(
        self,
        key: str,
        default: ConfigValueT | None = None,
        note: str | None = None
    ) -> ConfigValue | ConfigValueT:
        """
        Set config default value.

        Parameters
        ----------
        key : Config key.
        default : Config default value.
        note : Config default note.

        Returns
        -------
        Config value.
        """

        # Set.
        data = {
            'key': key,
            'value': repr(default),
            'type': type(default).__name__,
            'note': note
        }
        result = self.engine.execute.insert(
            'config',
            data,
            'ignore'
        )

        # Get.
        if result.rowcount == 0:
            default = self.get(key)

        return default


    def update(self, data: ConfigRow | ConfigTable) -> None:
        """
        Update config values.

        Parameters
        ----------
        data : Config update data.
            - `ConfigRow`: One config.
            - `ConfigTable`: Multiple configs.
        """

        # Parameter.
        if type(data) == dict:
            data = [data]
        data = data.copy()
        for row in data:
            row['value'] = repr(row['value'])
            row['type'] = type(row['value']).__name__

        # Update.
        self.engine.execute.insert(
            'config',
            data,
            'update'
        )


    def remove(self, key: str | list[str]) -> None:
        """
        Remove config.

        Parameters
        ----------
        key : Config key or key list.
        """

        # Remove.
        if type(key) == str:
            where = '`key` = :key'
            limit = 1
        else:
            where = '`key` in :key'
            limit = None
        result = self.engine.execute.delete(
            'config',
            where,
            limit=limit,
            key=key
        )

        # Check.
        if result.rowcount == 0:
            throw(KeyError, key)


    def items(self) -> dict[str, ConfigValue]:
        """
        Get all config keys and values.

        Returns
        -------
        All config keys and values.
        """

        # Get.
        result = self.engine.execute.select(
            'config',
            ['key', 'value']
        )

        # Convert.
        global_dict = {'datetime': Datetime}
        result = result.to_dict('key', 'value')
        result = {
            key: eval(value, global_dict)
            for key, value in result.items()
        }

        return result


    def keys(self) -> list[str]:
        """
        Get all config keys.

        Returns
        -------
        All config keys.
        """

        # Get.
        result = self.engine.execute.select(
            'config',
            '`key`'
        )

        # Convert.
        global_dict = {'datetime': Datetime}
        result = [
            eval(value, global_dict)
            for value in result
        ]

        return result


    def values(self) -> list[ConfigValue]:
        """
        Get all config value.

        Returns
        -------
        All config values.
        """

        # Get.
        result = self.engine.execute.select(
            'config',
            '`value`'
        )

        # Convert.
        global_dict = {'datetime': Datetime}
        result = [
            eval(value, global_dict)
            for value in result
        ]

        return result


    def __getitem__(self, key: str) -> ConfigValue:
        """
        Get config value.

        Parameters
        ----------
        key : Config key.

        Returns
        -------
        Config value.
        """

        # Get.
        value = self.get(key, Null)

        # Check.
        if value == Null:
            throw(KeyError, key)

        return value


    def __setitem__(
        self,
        key_and_note: str | tuple[str, str],
        value: ConfigValue
    ) -> None:
        """
        Set config value.

        Parameters
        ----------
        key_and_note : Config key and note.
        value : Config value.
        """

        # Parameter.
        if type(key_and_note) != str:
            key, note = key_and_note
        else:
            key = key_and_note
            note = None

        # Set.
        data = {
            'key': key,
            'value': repr(value),
            'note': note
        }
        self.update(data)


class DatabaseConfigAsync(DatabaseConfigSuper['rengine.DatabaseEngineAsync']):
    """
    Asynchronous database config type.
    Can create database used `self.build_db` method.

    Examples
    --------
    >>> config = DatabaseConfig()
    >>> await config['key1'] = 1
    >>> await config['key2', 'note'] = 2
    >>> await config['key1'], config['key2']
    (1, 2)
    """


    async def build_db(self) -> None:
        """
        Asynchronous check and build database tables.
        """

        # Parameter.
        tables, views_stats = self.handle_build_db()

        # Build.
        await self.engine.build.build(tables=tables, views_stats=views_stats, skip=True)


    async def data(self) -> ConfigTable:
        """
        Asynchronous get config data table.

        Returns
        -------
        Config data table.
        """

        # Get.
        result = await self.engine.execute.select(
            'config',
            ['key', 'value', 'note'],
            order='IFNULL(`update_time`, `create_time`) DESC'
        )

        # Convert.
        global_dict = {'datetime': Datetime}
        result = [
            {
                'key': row['key'],
                'value': eval(row['value'], global_dict),
                'note': row['note']
            }
            for row in result
        ]

        return result


    async def get(self, key: str, default: ConfigValueT | None = None) -> ConfigValue | ConfigValueT:
        """
        Asynchronous get config value, when not exist, then return default value.

        Parameters
        ----------
        key : Config key.
        default : Config default value.

        Returns
        -------
        Config value.
        """

        # Get.
        where = '`key` = :key'
        result = await self.engine.execute.select(
            'config',
            '`value`',
            where,
            limit=1,
            key=key
        )
        value = result.scalar()

        # Default.
        if value is None:
            value = default
        else:
            global_dict = {'datetime': Datetime}
            value = eval(value, global_dict)

        return value


    async def setdefault(
        self,
        key: str,
        default: ConfigValueT | None = None,
        note: str | None = None
    ) -> ConfigValue | ConfigValueT:
        """
        Asynchronous set config default value.

        Parameters
        ----------
        key : Config key.
        default : Config default value.
        note : Config default note.

        Returns
        -------
        Config value.
        """

        # Set.
        data = {
            'key': key,
            'value': repr(default),
            'type': type(default).__name__,
            'note': note
        }
        result = await self.engine.execute.insert(
            'config',
            data,
            'ignore'
        )

        # Get.
        if result.rowcount == 0:
            default = await self.get(key)

        return default


    async def update(self, data: ConfigRow | ConfigTable) -> None:
        """
        Asynchronous update config values.

        Parameters
        ----------
        data : Config update data.
            - `ConfigRow`: One config.
            - `ConfigTable`: Multiple configs.
        """

        # Parameter.
        if type(data) == dict:
            data = [data]
        data = data.copy()
        for row in data:
            row['value'] = repr(row['value'])
            row['type'] = type(row['value']).__name__

        # Update.
        await self.engine.execute.insert(
            'config',
            data,
            'update'
        )


    async def remove(self, key: str | list[str]) -> None:
        """
        Asynchronous remove config.

        Parameters
        ----------
        key : Config key or key list.
        """

        # Remove.
        if type(key) == str:
            where = '`key` = :key'
            limit = 1
        else:
            where = '`key` in :key'
            limit = None
        result = await self.engine.execute.delete(
            'config',
            where,
            limit=limit,
            key=key
        )

        # Check.
        if result.rowcount == 0:
            throw(KeyError, key)


    async def items(self) -> dict[str, ConfigValue]:
        """
        Asynchronous get all config keys and values.

        Returns
        -------
        All config keys and values.
        """

        # Get.
        result = await self.engine.execute.select(
            'config',
            ['key', 'value']
        )

        # Convert.
        global_dict = {'datetime': Datetime}
        result = result.to_dict('key', 'value')
        result = {
            key: eval(value, global_dict)
            for key, value in result.items()
        }

        return result


    async def keys(self) -> list[str]:
        """
        Asynchronous get all config keys.

        Returns
        -------
        All config keys.
        """

        # Get.
        result = await self.engine.execute.select(
            'config',
            '`key`'
        )

        # Convert.
        global_dict = {'datetime': Datetime}
        result = [
            eval(value, global_dict)
            for value in result
        ]

        return result


    async def values(self) -> list[ConfigValue]:
        """
        Asynchronous get all config value.

        Returns
        -------
        All config values.
        """

        # Get.
        result = await self.engine.execute.select(
            'config',
            '`value`'
        )

        # Convert.
        global_dict = {'datetime': Datetime}
        result = [
            eval(value, global_dict)
            for value in result
        ]

        return result


    async def __getitem__(self, key: str) -> ConfigValue:
        """
        Asynchronous get config value.

        Parameters
        ----------
        key : Config key.

        Returns
        -------
        Config value.
        """

        # Get.
        value = await self.get(key, Null)

        # Check.
        if value == Null:
            throw(KeyError, key)

        return value


    async def __setitem__(
        self,
        key_and_note: str | tuple[str, str],
        value: ConfigValue
    ) -> None:
        """
        Asynchronous set config value.

        Parameters
        ----------
        key_and_note : Config key and note.
        value : Config value.
        """

        # Parameter.
        if type(key_and_note) != str:
            key, note = key_and_note
        else:
            key = key_and_note
            note = None

        # Set.
        data = {
            'key': key,
            'value': repr(value),
            'note': note
        }
        await self.update(data)
