# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-09
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database methods.
"""


from typing import Any, TypeVar, Generic, overload
from reykit.rbase import Null, throw

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


    @overload
    def __call__(
        self,
        name: str | None = None,
        *,
        host: str,
        port: int | str,
        username: str,
        password: str,
        database: str,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: float = 30.0,
        pool_recycle: int | None = 3600,
        echo: bool = False,
        **query: str
    ) -> DatabaseEngineT: ...

    def __call__(
        self,
        name: str | None = None,
        **kwargs: Any
    ) -> DatabaseEngineT:
        """
        Build instance attributes.

        Parameters
        ----------
        name : Database engine name, useed for index.
            - `None`: Use database name.
        host : Remote server database host.
        port : Remote server database port.
        username : Remote server database username.
        password : Remote server database password.
        database : Remote server database name.
        pool_size : Number of connections `keep open`.
        max_overflow : Number of connections `allowed overflow`.
        pool_timeout : Number of seconds `wait create` connection.
        pool_recycle : Number of seconds `recycle` connection.
            - `None | Literal[-1]`: No recycle.
            - `int`: Use this value.
        echo : Whether report SQL execute information, not include ORM execute.
        query : Remote server database parameters.
        """

        # Parameter.
        match self:
            case Database():
                engine_type = DatabaseEngine
            case DatabaseAsync():
                engine_type = DatabaseEngineAsync

        # Create.
        engine = engine_type(**kwargs)

        # Add.
        if name is None:
            name = engine.database
        self.__engine_dict[name] = engine

        return engine


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


class DatabaseAsync(DatabaseSuper[DatabaseEngineAsync]):
    """
    Asynchronous database type.
    """
