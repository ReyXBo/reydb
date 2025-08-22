# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-08-22 13:45:58
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database config methods.
"""


from typing import Any
from reykit.rbase import T, throw

from .rconn import DatabaseConnection
from .rdb import Database


__all__ = (
    'DatabaseConfig',
)


class DatabaseConfig(object):
    """
    Database config type.
    Can create database used `self.build` method.
    """


    def __init__(self, database: Database | DatabaseConnection) -> None:
        """
        Build instance attributes.
        """

        # SQLite.
        if database.backend == 'sqlite':
            text='not suitable for SQLite databases'
            throw(AssertionError, text=text)

        # Build.
        self.database = database

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
                        'type': 'json',
                        'constraint': 'NOT NULL',
                        'comment': 'Config value.'
                    },
                    {
                        'name': 'note',
                        'type': 'varchar(500)',
                        'comment': 'Config note.'
                    }
                ]
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
                            f'FROM `{self.db_names['base']}`.`{self.db_names['base.stats_config']}`'
                        ),
                        'comment': 'Config count.'
                    },
                    {
                        'name': 'last_create_time',
                        'select': (
                            'SELECT MAX(`create_time`)\n'
                            f'FROM `{self.db_names['base']}`.`{self.db_names['base.stats_config']}`'
                        ),
                        'comment': 'Config last record create time.'
                    },
                    {
                        'name': 'last_update_time',
                        'select': (
                            'SELECT MAX(`update_time`)\n'
                            f'FROM `{self.db_names['base']}`.`{self.db_names['base.stats_config']}`'
                        ),
                        'comment': 'Config last record update time.'
                    }
                ]

            }

        ]

        # Build.
        self.database.build.build(databases, tables, views_stats)


    def get(self, key: str, default: T | None = None) -> Any | T:
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
        result = self.database.execute_select(
            (self.db_names['base'], self.db_names['base.config']),
            'value',
            where,
            limit=1,
            key=key
        )
        value = result.scalar()

        # Default.
        if value is None:
            value = default

        return value


    def setdefault(self, key: str, default: T | None = None) -> Any | T:
        """
        Set config value.

        Parameters
        ----------
        key : Config key.
        default : Config default value.

        Returns
        -------
        Config value.
        """

        # Set.
        data = {'key': key, 'value': default}
        result = self.database.execute_insert(
            (self.db_names['base'], self.db_names['base.config']),
            data,
            'ignore'
        )

        # Get.
        if result.rowcount == 0:
            result = self[key]
        else:
            result = default

        return result


    def update(self, data: dict[str, Any]) -> None:
        """
        Update config values.

        Parameters
        ----------
        data : Config update data.
        """

        # Update.
        data = [
            {
                'key': key,
                'value': value
            }
            for key, value in data.items
        ]
        self.database.execute_insert(
            (self.db_names['base'], self.db_names['base.config']),
            data,
            'update'
        )


    def remove(self, key: str) -> None:
        """
        Remove config.

        Parameters
        ----------
        key : Config key.
        """

        # Remove.
        where = '`key` = :key'
        result = self.database.execute_delete(
            (self.db_names['base'], self.db_names['base.config']),
            where,
            limit=1,
            key=key
        )

        # Check.
        if result.rowcount == 0:
            throw(KeyError, key)


    def items(self) -> dict:
        """
        Get all config keys and values.

        Returns
        -------
        All config keys and values.
        """

        # Get.
        result = self.database.execute_select(
            (self.db_names['base'], self.db_names['base.config']),
            ['key', 'value']
        )

        # Convert.
        result = result.to_dict('key', 'value')

        return result


    def keys(self) -> list[str]:
        """
        Get all config keys.

        Returns
        -------
        All config keys.
        """

        # Get.
        result = self.database.execute_select(
            (self.db_names['base'], self.db_names['base.config']),
            'key'
        )

        # Convert.
        result = result.to_list()

        return result


    def values(self) -> list[Any]:
        """
        Get all config value.

        Returns
        -------
        All config values.
        """

        # Get.
        result = self.database.execute_select(
            (self.db_names['base'], self.db_names['base.config']),
            'value'
        )

        # Convert.
        result = result.to_list()

        return result


    def __getitem__(self, key: str) -> Any:
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
        value = self.get(key)

        # Check.
        if value is None:
            throw(KeyError, key)

        return value


    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set config value.

        Parameters
        ----------
        key : Config key.
        value : Config value.
        """

        # Set.
        data = {'key': key, 'value': value}
        self.database.execute_insert(
            (self.db_names['base'], self.db_names['base.config']),
            data,
            'update'
        )
