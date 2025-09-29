# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-08-20 16:57:19
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database error methods.
"""


from typing import Any
from collections.abc import Callable
from traceback import StackSummary
from functools import wraps as functools_wraps
from reykit.rbase import T, Exit, catch_exc

from . import rdb
from .rbase import DatabaseBase


__all__ = (
    'DatabaseError',
)


class DatabaseError(DatabaseBase):
    """
    Database error type.
    Can create database used `self.build_db` method.
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
            'base.error': 'error',
            'base.stats_error': 'stats_error'
        }


    def build_db(self) -> None:
        """
        Check and build database tables, by `self.db_names`.
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

            ### 'error'.
            {
                'path': (self.db_names['base'], self.db_names['base.error']),
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
                        'name': 'n_create_time',
                        'fields': 'create_time',
                        'type': 'noraml',
                        'comment': 'Record create time normal index.'
                    },
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

            ### 'stats_error'.
            {
                'path': (self.db_names['base'], self.db_names['base.stats_error']),
                'items': [
                    {
                        'name': 'count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['base']}`.`{self.db_names['base.error']}`'
                        ),
                        'comment': 'Error log count.'
                    },
                    {
                        'name': 'past_day_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['base']}`.`{self.db_names['base.error']}`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) = 0'
                        ),
                        'comment': 'Error log count in the past day.'
                    },
                    {
                        'name': 'past_week_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['base']}`.`{self.db_names['base.error']}`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 6'
                        ),
                        'comment': 'Error log count in the past week.'
                    },
                    {
                        'name': 'past_month_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['base']}`.`{self.db_names['base.error']}`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 29'
                        ),
                        'comment': 'Error log count in the past month.'
                    },
                    {
                        'name': 'last_time',
                        'select': (
                            'SELECT MAX(`create_time`)\n'
                            f'FROM `{self.db_names['base']}`.`{self.db_names['base.error']}`'
                        ),
                        'comment': 'Error log last record create time.'
                    }
                ]

            }

        ]

        # Build.
        self.db.build.build(databases, tables, views_stats=views_stats)


    def record(
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
        self.db.execute.insert(
            self.db_names['base.error'],
            data=data
        )


    def wrap(
        self,
        func: Callable[..., T] | None = None,
        *,
        note: str | None = None,
        filter_type : BaseException | tuple[BaseException, ...] = Exit
    ) -> T | Callable[[Callable[..., T]], Callable[..., T]]:
        """
        Decorator, insert exception information into the table of database, throw exception.

        Parameters
        ----------
        func : Function.
        note : Exception note.
        filter_type : Exception type of not inserted, but still throw exception.

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
        if issubclass(filter_type, BaseException):
            filter_type = (filter_type,)


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
                    for type_ in filter_type:
                        if isinstance(exc, type_):
                            break
                    else:
                        self.record(exc, stack, note)

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

    __call__ = record
