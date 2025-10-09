# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-09
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database methods.
"""


from typing import TypeVar, Generic, Self, Type
from functools import wraps as functools_wraps
from reykit.rbase import CallableT, Null, throw, warn

from .rbase import DatabaseBase
from .rengine import DatabaseEngine, DatabaseEngineAsync


__all__ = (
    'DatabaseSuper',
    'Database',
    'DatabaseAsync'
)


DatabaseEngineT = TypeVar('DatabaseEngineT', DatabaseEngine, DatabaseEngineAsync)


class DatabaseSuper(DatabaseBase, Generic[DatabaseEngineT]):
    """
    Database super type.
    """


    def __init__(self):
        """
        Build instance attributes.
        """

        # Build.
        self.__engine_dict: dict[str, DatabaseEngineT] = {}


    @classmethod
    def _wrap_add(
        cls_or_self,
        engine_type: Type[DatabaseEngine] | Type[DatabaseEngineAsync],
        type_hint: CallableT
    ) -> CallableT:
        """
        Decorator, create and add database engine.

        Parameters
        ----------
        engine_type : Database engine type.
        type_hint : Type hint.

        Returns
        -------
        Decorated method.
        """


        @functools_wraps(engine_type.__init__)
        def func(self: Self, *args, **kwargs):

            # Build.
            engine: DatabaseEngineT = engine_type(*args, **kwargs)

            # Warning.
            if engine.database in self.__engine_dict:
                warn(f'database engine "{engine.database}" re registered.')

            # Add.
            self.__engine_dict[engine.database] = engine

            return engine


        return func


    def __getattr__(self, database: str) -> DatabaseEngineT:
        """
        Get added database engine.

        Parameters
        ----------
        database : Database name.
        """

        # Get.
        engine = self.__engine_dict.get(database, Null)

        # Throw exception.
        if engine == Null:
            text = f"lack of database engine '{database}'"
            throw(AssertionError, text=text)

        return engine


    __getitem__ = __getattr__


    def __contains__(self, database: str) -> bool:
        """
        Whether the exist this database engine.

        Parameters
        ----------
        database : Database name.
        """

        # Judge.
        result = database in self.__engine_dict

        return result


class Database(DatabaseSuper[DatabaseEngine]):
    """
    Database type.
    """


    __call__ = DatabaseSuper._wrap_add(DatabaseEngine, DatabaseEngine.__init__)


class DatabaseAsync(DatabaseSuper[DatabaseEngineAsync]):
    """
    Asynchronous database type.
    """


    __call__ = DatabaseSuper._wrap_add(DatabaseEngineAsync, DatabaseEngineAsync.__init__)
