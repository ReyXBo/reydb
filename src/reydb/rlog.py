# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-08-20 16:57:19
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database log methods.
"""


from typing import Any
from collections.abc import Callable
from traceback import StackSummary
from functools import wraps as functools_wraps
from reykit.rbase import T, Exit, throw, catch_exc

from .rbase import DatabaseBase
from .rconn import DatabaseConnection
from .rdb import Database


__all__ = (
    'DatabaseLog',
)


class DatabaseLog(DatabaseBase):
    """
    Database log type.
    Can create database used `self.build` method.
    """


    def __init__(self, database: Database | DatabaseConnection) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        database : Database or DatabaseConnection instance.
        """

        # SQLite.
        if database.backend == 'sqlite':
            text='not suitable for SQLite databases'
            throw(AssertionError, text=text)

        # Build.
        self.database = database

        ## Database path name.
        self.db_names = {
            'log': 'log',
            'log.error': 'error',
            'log.error_stats': 'error_stats'
        }


    def build_db(self) -> None:
        """
        Check and build all standard databases and tables, by `self.db_names`.
        """

        # Set parameter.

        ## Database.
        databases = [
            {
                'name': self.db_names['log']
            }
        ]

        ## Table.
        tables = [

            ### 'error'.
            {
                'path': (self.db_names['log'], self.db_names['log.error']),
                'fields': [
                    {
                        'name': 'create_time',
                        'type': 'datetime',
                        'constraint': 'NOT NULL DEFAULT CURRENT_TIMESTAMP',
                        'comment': 'Record create time.'
                    },
                    {
                        'name': 'id',
                        'type': 'int unsigned',
                        'constraint': 'NOT NULL AUTO_INCREMENT',
                        'comment': 'ID.'
                    },
                    {
                        'name': 'type',
                        'type': 'varchar(50)',
                        'constraint': 'NOT NULL',
                        'comment': 'Error type.'
                    },
                    {
                        'name': 'data',
                        'type': 'json',
                        'comment': 'Error data.'
                    },
                    {
                        'name': 'stack',
                        'type': 'json',
                        'comment': 'Error code traceback stack.'
                    },
                    {
                        'name': 'note',
                        'type': 'varchar(500)',
                        'comment': 'Error note.'
                    }
                ],
                'primary': 'id',
                'indexes': [
                    {
                        'name': 'n_type',
                        'fields': 'type',
                        'type': 'noraml',
                        'comment': 'Error type normal index.'
                    }
                ],
                'comment': 'Error log table.'
            },

        ]

        ## View stats.
        views_stats = [

            ### 'error_stats'.
            {
                'path': (self.db_names['log'], self.db_names['log.error_stats']),
                'items': [
                    {
                        'name': 'count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['log']}`.`{self.db_names['log.error']}`'
                        ),
                        'comment': 'Error log count.'
                    },
                    {
                        'name': 'past_day_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['log']}`.`{self.db_names['log.error']}`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) = 0'
                        ),
                        'comment': 'Error log count in the past day.'
                    },
                    {
                        'name': 'past_week_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['log']}`.`{self.db_names['log.error']}`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 6'
                        ),
                        'comment': 'Error log count in the past week.'
                    },
                    {
                        'name': 'past_month_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['log']}`.`{self.db_names['log.error']}`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 29'
                        ),
                        'comment': 'Error log count in the past month.'
                    },
                    {
                        'name': 'last_time',
                        'select': (
                            'SELECT MAX(`create_time`)\n'
                            f'FROM `{self.db_names['log']}`.`{self.db_names['log.error']}`'
                        ),
                        'comment': 'Error log last record create time.'
                    }
                ]

            }

        ]

        # Build.
        self.database.build.build(databases, tables, views_stats=views_stats)


    def error(
        self,
        exc: BaseException,
        stack: StackSummary,
        note: str | None = None
    ) -> None:
        """
        Insert exception information into the table of database.

        Parameters
        ----------
        exc : Exception instance.
        stack : Exception traceback stack instance.
        note : Exception note.
        """

        # Handle parameter.
        exc_type = type(exc).__name__
        exc_data = list(exc.args) or None
        exc_stack = [
            {
                'file': frame.filename,
                'line': frame.lineno,
                'frame': frame.name,
                'code': frame.line
            }
            for frame in stack
        ]
        data = {
            'type': exc_type,
            'data': exc_data,
            'stack': exc_stack,
            'note': note
        }

        # Insert.
        self.database.execute_insert(
            (self.db_names['log'], self.db_names['log.error']),
            data=data
        )


    def wrap_error(
        self,
        func: Callable[..., T] | None = None,
        *,
        note: str | None = None,
        filter_exc : BaseException | tuple[BaseException, ...] = Exit
    ) -> T | Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Decorator, insert exception information into the table of database, throw exception.

        Parameters
        ----------
        func : Function.
        note : Exception note.
        filter_exc : Exception type of not inserted, but still throw exception.

        Returns
        -------
        Decorated function or decorator with parameter.

        Examples
        --------
        Method one.
        >>> @wrap_error
        >>> def func(*args, **kwargs): ...

        Method two.
        >>> @wrap_error(**wrap_kwargs)
        >>> def func(*args, **kwargs): ...

        Method three.
        >>> def func(*args, **kwargs): ...
        >>> func = wrap_error(func, **wrap_kwargs)

        Method four.
        >>> def func(*args, **kwargs): ...
        >>> wrap_error = wrap_error(**wrap_kwargs)
        >>> func = wrap_error(func)

        >>> func(*args, **kwargs)
        """

        # Handle parameter.
        if issubclass(filter_exc, BaseException):
            filter_exc = (filter_exc,)


        def _wrap(func_: Callable[..., T]) -> Callable[..., T]:
            """
            Decorator, insert exception information into the table of database.

            Parameters
            ----------
            _func : Function.

            Returns
            -------
            Decorated function.
            """


            @functools_wraps(func_)
            def _func(*args, **kwargs) -> Any:
                """
                Decorated function.

                Parameters
                ----------
                args : Position arguments of function.
                kwargs : Keyword arguments of function.

                Returns
                -------
                Function return.
                """

                # Try execute.
                try:
                    result = func_(*args, **kwargs)

                # Log.
                except BaseException:
                    _, exc, stack = catch_exc()

                    ## Filter.
                    if type(exc) not in filter_exc:
                        self.error(exc, stack, note)

                    raise

                return result


            return _func


        # Decorator.
        if func is None:
            return _wrap

        # Decorated function.
        else:
            _func = _wrap(func)
            return _func
