# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-08-22 13:45:58
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database config methods.
"""


from typing import TypedDict, TypeVar
import datetime
from datetime import (
    datetime as Datetime,
    date as Date,
    time as Time,
    timedelta as Timedelta
)
from reykit.rbase import Null, throw

from . import rdb
from .rbase import DatabaseBase


__all__ = (
    'DatabaseConfig',
)


type ConfigValue = bool | str | int | float | list | tuple | dict | set | Datetime | Date | Time | Timedelta | None
ConfigRow = TypedDict('ConfigRow', {'key': str, 'value': ConfigValue, 'type': str, 'note': str | None})
type ConfigTable = list[ConfigRow]
ConfigValueT = TypeVar('T', bound=ConfigValue) # Any.


class DatabaseConfig(DatabaseBase):
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


    def __init__(self, db: 'rdb.Database') -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: Database instance.
        """

        # Build.
        self.db = db

        ## Database path name.
        self.db_names = {
            'base': 'base',
            'base.config': 'config',
            'base.stats_config': 'stats_config'
        }


    def build_db(self) -> None:
        """
        Check and build all standard databases and tables, by `self.db_names`.
        """

        # Set parameter.

        ## Database.
        databases = [
            {
                'name': self.db_names['base']
            }
        ]

        ## Table.
        tables = [

            ### 'config'.
            {
                'path': (self.db_names['base'], self.db_names['base.config']),
                'fields': [
                    {
                        'name': 'create_time',
                        'type': 'datetime',
                        'constraint': 'NOT NULL DEFAULT CURRENT_TIMESTAMP',
                        'comment': 'Config create time.'
                    },
                    {
                        'name': 'update_time',
                        'type': 'datetime',
                        'constraint': 'DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP',
                        'comment': 'Config update time.'
                    },
                    {
                        'name': 'key',
                        'type': 'varchar(50)',
                        'constraint': 'NOT NULL',
                        'comment': 'Config key.'
                    },
                    {
                        'name': 'value',
                        'type': 'text',
                        'constraint': 'NOT NULL',
                        'comment': 'Config value.'
                    },
                    {
                        'name': 'type',
                        'type': 'varchar(50)',
                        'constraint': 'NOT NULL',
                        'comment': 'Config value type.'
                    },
                    {
                        'name': 'note',
                        'type': 'varchar(500)',
                        'comment': 'Config note.'
                    }
                ],
                'primary': 'key',
                'indexes': [
                    {
                        'name': 'n_create_time',
                        'fields': 'create_time',
                        'type': 'noraml',
                        'comment': 'Config create time normal index.'
                    },
                    {
                        'name': 'n_update_time',
                        'fields': 'update_time',
                        'type': 'noraml',
                        'comment': 'Config update time normal index.'
                    }
                ],
                'comment': 'Config data table.'
            }

        ]

        ## View stats.
        views_stats = [

            ### 'stats_config'.
            {
                'path': (self.db_names['base'], self.db_names['base.stats_config']),
                'items': [
                    {
                        'name': 'count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['base']}`.`{self.db_names['base.config']}`'
                        ),
                        'comment': 'Config count.'
                    },
                    {
                        'name': 'last_create_time',
                        'select': (
                            'SELECT MAX(`create_time`)\n'
                            f'FROM `{self.db_names['base']}`.`{self.db_names['base.config']}`'
                        ),
                        'comment': 'Config last record create time.'
                    },
                    {
                        'name': 'last_update_time',
                        'select': (
                            'SELECT MAX(`update_time`)\n'
                            f'FROM `{self.db_names['base']}`.`{self.db_names['base.config']}`'
                        ),
                        'comment': 'Config last record update time.'
                    }
                ]

            }

        ]

        # Build.
        self.db.build.build(databases, tables, views_stats=views_stats)


    @property
    def data(self) -> ConfigTable:
        """
        Get config data table.

        Returns
        -------
        Config data table.
        """

        # Get.
        result = self.db.execute.select(
            (self.db_names['base'], self.db_names['base.config']),
            ['key', 'value', 'type', 'note'],
            order='IFNULL(`update_time`, `create_time`) DESC'
        )

        # Convert.
        global_dict = {'datetime': datetime}
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
        result = self.db.execute.select(
            (self.db_names['base'], self.db_names['base.config']),
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
            global_dict = {'datetime': datetime}
            value = eval(value, global_dict)

        return value


    def setdefault(
        self,
        key: str,
        default: ConfigValueT | None = None,
        default_note: str | None = None
    ) -> ConfigValue | ConfigValueT:
        """
        Set config value.

        Parameters
        ----------
        key : Config key.
        default : Config default value.
        default_note : Config default note.

        Returns
        -------
        Config value.
        """

        # Set.
        data = {
            'key': key,
            'value': repr(default),
            'type': type(default).__name__,
            'note': default_note
        }
        result = self.db.execute.insert(
            (self.db_names['base'], self.db_names['base.config']),
            data,
            'ignore'
        )

        # Get.
        if result.rowcount == 0:
            default = self.get(key)

        return default


    def update(self, data: dict[str, ConfigValue] | ConfigTable) -> None:
        """
        Update config values.

        Parameters
        ----------
        data : Config update data.
            - `dict[str, Any]`: Config key and value.
            - `ConfigTable`: Config key and value and note.
        """

        # Handle parameter.
        if type(data) == dict:
            data = [
                {
                    'key': key,
                    'value': repr(value),
                    'type': type(value).__name__
                }
                for key, value in data.items()
            ]
        else:
            data = data.copy()
            for row in data:
                row['value'] = repr(row['value'])
                row['type'] = type(row['value']).__name__

        # Update.
        self.db.execute.insert(
            (self.db_names['base'], self.db_names['base.config']),
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
        result = self.db.execute.delete(
            (self.db_names['base'], self.db_names['base.config']),
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
        result = self.db.execute.select(
            (self.db_names['base'], self.db_names['base.config']),
            ['key', 'value']
        )

        # Convert.
        global_dict = {'datetime': datetime}
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
        result = self.db.execute.select(
            (self.db_names['base'], self.db_names['base.config']),
            '`key`'
        )

        # Convert.
        global_dict = {'datetime': datetime}
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
        result = self.db.execute.select(
            (self.db_names['base'], self.db_names['base.config']),
            '`value`'
        )

        # Convert.
        global_dict = {'datetime': datetime}
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


    def __setitem__(self, key_note: str | tuple[str, str], value: ConfigValue) -> None:
        """
        Set config value.

        Parameters
        ----------
        key_note : Config key and note.
        value : Config value.
        """

        # Handle parameter.
        if type(key_note) != str:
            key, note = key_note
        else:
            key = key_note
            note = None

        # Set.
        data = {
            'key': key,
            'value': repr(value),
            'type': type(value).__name__,
            'note': note
        }
        self.db.execute.insert(
            (self.db_names['base'], self.db_names['base.config']),
            data,
            'update'
        )
