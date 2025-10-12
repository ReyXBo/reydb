# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-09
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database methods.
"""


from typing import Any, TypeVar, Generic, overload
from collections.abc import Iterable, Sequence
from reykit.rbase import Null, throw
from reykit.rtask import ThreadPool, async_gather

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
        name: str | Sequence[str] | None = None,
        *,
        host: str,
        port: int | str,
        username: str,
        password: str,
        database: str,
        max_pool: int = 15,
        max_keep: int = 5,
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
            - `str` : Use this name.
            - `Sequence[str]`: Use multiple names.
        host : Remote server database host.
        port : Remote server database port.
        username : Remote server database username.
        password : Remote server database password.
        database : Remote server database name.
        max_pool : Maximum number of connections in the pool.
        max_keep : Maximum number of connections keeped.
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
            name = (engine.database,)
        elif type(name) == str:
            name = (name,)
        for n in name:
            self.__engine_dict[n] = engine

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


    @overload
    def __getitem__(self, database: str) -> DatabaseEngineT: ...

    __getitem__ = __getattr__


    def __contains__(self, name: str) -> bool:
        """
        Whether the exist this database engine.

        Parameters
        ----------
        name : Database engine name.
        """

        # Judge.
        result = name in self.__engine_dict

        return result


    def __iter__(self) -> Iterable[str]:
        """
        Iterable of database engine names.
        """

        # Generate.
        names = iter(self.__engine_dict)

        return names


class Database(DatabaseSuper[DatabaseEngine]):
    """
    Database type.
    """


    def warm_all(self, num: int | None = None) -> None:
        """
        Pre create connection to warm all pool.

        Parameters
        ----------
        num : Create number.
            - `None`: Use `self.max_keep` value.
        """

        # Parameter.
        engines = set(
            [
                self[name]
                for name in self
            ]
        )

        # Warm.

        ## Create.
        func = lambda engine: engine.connect().close()
        pool = ThreadPool(func, _max_workers=num)
        for engine in engines:
            engine_num = num or engine.max_keep
            for _ in range(engine_num):
                pool.one(engine.engine)

        ## Wait.
        pool.join()


class DatabaseAsync(DatabaseSuper[DatabaseEngineAsync]):
    """
    Asynchronous database type.
    """


    async def warm_all(self, num: int | None = None) -> None:
        """
        Asynchronous pre create connection to warm all pool.

        Parameters
        ----------
        num : Create number.
            - `None`: Use `self.max_keep` value.
        """

        # Parameter.
        engines = set(
            [
                self[name]
                for name in self
            ]
        )

        # Warm.
        coroutines = [
            engine.warm(num)
            for engine in engines
        ]
        await async_gather(*coroutines)


    async def dispose_all(self) -> None:
        """
        Dispose asynchronous connections of all database.
        """

        # Parameter.
        engines = set(
            [
                self[name]
                for name in self
            ]
        )

        # Dispose.
        coroutines = [
            engine.dispose()
            for engine in engines
        ]
        await async_gather(*coroutines)
