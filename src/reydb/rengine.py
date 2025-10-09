# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database engine methods.
"""


from typing import TypeVar, Generic, overload
from urllib.parse import quote as urllib_quote
from pymysql.constants.CLIENT import MULTI_STATEMENTS
from sqlalchemy import Engine, create_engine as sqlalchemy_create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine as sqlalchemy_create_async_engine
from reykit.rtext import join_data_text

from . import rbase, rbuild, rconfig, rconn, rerror, rexec, rinfo, rorm


__all__ = (
    'DatabaseEngineSuper',
    'DatabaseEngine',
    'DatabaseEngineAsync'
)


DatabaseConnectionT = TypeVar('DatabaseConnectionT', 'rconn.DatabaseConnection', 'rconn.DatabaseConnectionAsync')
DatabaseExecuteT = TypeVar('DatabaseExecuteT', 'rexec.DatabaseExecute', 'rexec.DatabaseExecuteAsync')
DatabaseORMT = TypeVar('DatabaseORMT', 'rorm.DatabaseORM', 'rorm.DatabaseORMAsync')
DatabaseBuildT = TypeVar('DatabaseBuildT', 'rbuild.DatabaseBuild', 'rbuild.DatabaseBuildAsync')
DatabaseConfigT = TypeVar('DatabaseConfigT', 'rconfig.DatabaseConfig', 'rconfig.DatabaseConfigAsync')
DatabaseInformationSchemaT = TypeVar(
    'DatabaseInformationSchemaT',
    'rinfo.DatabaseInformationSchema',
    'rinfo.DatabaseInformationSchemaAsync'
)
DatabaseInformationParameterVariablesT = TypeVar(
    'DatabaseInformationParameterVariablesT',
    'rinfo.DatabaseInformationParameterVariables',
    'rinfo.DatabaseInformationParameterVariablesAsync'
)
DatabaseInformationParameterStatusT = TypeVar(
    'DatabaseInformationParameterStatusT',
    'rinfo.DatabaseInformationParameterStatus',
    'rinfo.DatabaseInformationParameterStatusAsync'
)
DatabaseInformationParameterVariablesGlobalT = TypeVar(
    'DatabaseInformationParameterVariablesGlobalT',
    'rinfo.DatabaseInformationParameterVariablesGlobal',
    'rinfo.DatabaseInformationParameterVariablesGlobalAsync'
)
DatabaseInformationParameterStatusGlobalT = TypeVar(
    'DatabaseInformationParameterStatusGlobalT',
    'rinfo.DatabaseInformationParameterStatusGlobal',
    'rinfo.DatabaseInformationParameterStatusGlobalAsync'
)


class DatabaseEngineSuper(
    rbase.DatabaseBase,
    Generic[
        rbase.EngineT,
        DatabaseConnectionT,
        DatabaseExecuteT,
        DatabaseORMT,
        DatabaseBuildT,
        DatabaseConfigT,
        DatabaseInformationSchemaT,
        DatabaseInformationParameterVariablesT,
        DatabaseInformationParameterStatusT,
        DatabaseInformationParameterVariablesGlobalT,
        DatabaseInformationParameterStatusGlobalT
    ]
):
    """
    Database engine super type, based `MySQL`.
    """


    def __init__(
        self,
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
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
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
        if type(port) == str:
            port = int(port)

        # Build.
        self.username = username
        self.password = password
        self.host = host
        self.port: int | None = port
        self.database = database
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        if pool_recycle is None:
            self.pool_recycle = -1
        else:
            self.pool_recycle = pool_recycle
        self.echo = echo
        self.query = query

        ## Schema.
        self._schema: dict[str, dict[str, list[str]]] | None = None

        ## Create engine.
        self.engine = self.__create_engine()


    def __str__(self) -> str:
        """
        Return connection information text.
        """

        # Generate.
        filter_key = (
            'engine',
        )
        info = {
            key: value
            for key, value in self.__dict__.items()
            if (
                key not in filter_key
                and key[0] != '_'
            )
        }
        info['conn_count'] = self.conn_count
        text = join_data_text(info)

        return text


    @property
    def backend(self) -> str:
        """
        Database backend name.

        Returns
        -------
        Name.
        """

        # Get.
        url_params = rbase.extract_url(self.url)
        backend = url_params['backend']

        return backend


    @property
    def driver(self) -> str:
        """
        Database driver name.

        Returns
        -------
        Name.
        """

        # Get.
        url_params = rbase.extract_url(self.url)
        driver = url_params['driver']

        return driver


    @property
    def url(self) -> str:
        """
        Generate server URL.

        Returns
        -------
        Server URL.
        """

        # Generate URL.
        password = urllib_quote(self.password)
        match self:
            case DatabaseEngine():
                url_ = f'mysql+pymysql://{self.username}:{password}@{self.host}:{self.port}/{self.database}'
            case DatabaseEngineAsync():
                url_ = f'mysql+aiomysql://{self.username}:{password}@{self.host}:{self.port}/{self.database}'

        # Add Server parameter.
        if self.query != {}:
            query = '&'.join(
                [
                    f'{key}={value}'
                    for key, value in self.query.items()
                ]
            )
            url_ = f'{url_}?{query}'

        return url_


    def __create_engine(self) -> rbase.EngineT:
        """
        Create database `Engine` object.

        Returns
        -------
        Engine object.
        """

        # Parameter.
        engine_params = {
            'url': self.url,
            'pool_size': self.pool_size,
            'max_overflow': self.max_overflow,
            'pool_timeout': self.pool_timeout,
            'pool_recycle': self.pool_recycle,
            'connect_args': {'client_flag': MULTI_STATEMENTS}
        }

        # Create Engine.
        match self:
            case DatabaseEngine():
                engine = sqlalchemy_create_engine(**engine_params)
            case DatabaseEngineAsync():
                engine = sqlalchemy_create_async_engine(**engine_params)

        return engine


    @property
    def conn_count(self) -> tuple[int, int]:
        """
        Count number of keep open and allowed overflow connection.

        Returns
        -------
        Number of keep open and allowed overflow connection.
        """

        # Count.
        _overflow: int = self.engine.pool._overflow
        if _overflow < 0:
            keep_n = self.pool_size + _overflow
            overflow_n = 0
        else:
            keep_n = self.pool_size
            overflow_n = _overflow

        return keep_n, overflow_n


    def connect(self, autocommit: bool = False) -> DatabaseConnectionT:
        """
        Build database connection instance.

        Parameters
        ----------
        autocommit: Whether automatic commit execute.

        Returns
        -------
        Database connection instance.
        """

        # Build.
        match self:
            case DatabaseEngine():
                conn = rconn.DatabaseConnection(self, autocommit)
            case DatabaseEngineAsync():
                conn = rconn.DatabaseConnectionAsync(self, autocommit)

        return conn


    @property
    def execute(self) -> DatabaseExecuteT:
        """
        Build database execute instance.

        Returns
        -------
        Instance.
        """

        # Build.
        conn = self.connect(True)
        exec = conn.execute

        return exec


    @property
    def orm(self) -> DatabaseORMT:
        """
        Build database ORM instance.

        Returns
        -------
        Instance.
        """

        # Build.
        match self:
            case DatabaseEngine():
                orm = rorm.DatabaseORM(self)
            case DatabaseEngineAsync():
                orm = rorm.DatabaseORMAsync(self)

        return orm


    @property
    def build(self) -> DatabaseBuildT:
        """
        Build database build instance.

        Returns
        -------
        Instance.
        """

        # Build.
        match self:
            case DatabaseEngine():
                build = rbuild.DatabaseBuild(self)
            case DatabaseEngineAsync():
                build = rbuild.DatabaseBuildAsync(self)

        return build


    @property
    def error(self):
        """
        Build database error instance.

        Returns
        -------
        Instance.
        """

        # Build.
        match self:
            case DatabaseEngine():
                error = rerror.DatabaseError(self)
            case DatabaseEngineAsync():
                error = rerror.DatabaseErrorAsync(self)

        return error


    @property
    def config(self) -> DatabaseConfigT:
        """
        Build database config instance.

        Returns
        -------
        Instance.
        """

        # Build.
        match self:
            case DatabaseEngine():
                config = rconfig.DatabaseConfig(self)
            case DatabaseEngineAsync():
                config = rconfig.DatabaseConfigAsync(self)

        return config


    @property
    def schema(self) -> DatabaseInformationSchemaT:
        """
        Build database schema instance.

        Returns
        -------
        Instance.
        """

        # Build.
        match self:
            case DatabaseEngine():
                schema = rinfo.DatabaseInformationSchema(self)
            case DatabaseEngineAsync():
                schema = rinfo.DatabaseInformationSchemaAsync(self)

        return schema


    @property
    def var(self) -> DatabaseInformationParameterVariablesT:
        """
        Build database parameters variable instance.

        Returns
        -------
        Instance.
        """

        # Build.
        match self:
            case DatabaseEngine():
                var = rinfo.DatabaseInformationParameterVariables(self)
            case DatabaseEngineAsync():
                var = rinfo.DatabaseInformationParameterVariablesAsync(self)

        return var


    @property
    def stat(self) -> DatabaseInformationParameterVariablesT:
        """
        Build database parameters status instance.

        Returns
        -------
        Instance.
        """

        # Build.
        match self:
            case DatabaseEngine():
                stat = rinfo.DatabaseInformationParameterStatus(self)
            case DatabaseEngineAsync():
                stat = rinfo.DatabaseInformationParameterStatusAsync(self)

        return stat


    @property
    def glob_var(self) -> DatabaseInformationParameterVariablesGlobalT:
        """
        Build global database parameters variable instance.

        Returns
        -------
        Instance.
        """

        # Build.
        match self:
            case DatabaseEngine():
                var = rinfo.DatabaseInformationParameterVariablesGlobal(self)
            case DatabaseEngineAsync():
                var = rinfo.DatabaseInformationParameterVariablesGlobalAsync(self)

        return var


    @property
    def glob_stat(self) -> DatabaseInformationParameterStatusGlobalT:
        """
        Build global database parameters status instance.

        Returns
        -------
        Instance.
        """

        # Build.
        match self:
            case DatabaseEngine():
                stat = rinfo.DatabaseInformationParameterStatusGlobal(self)
            case DatabaseEngineAsync():
                stat = rinfo.DatabaseInformationParameterStatusGlobalAsync(self)

        return stat


class DatabaseEngine(
    DatabaseEngineSuper[
        Engine,
        'rconn.DatabaseConnection',
        'rexec.DatabaseExecute',
        'rorm.DatabaseORM',
        'rbuild.DatabaseBuild',
        'rconfig.DatabaseConfig',
        'rinfo.DatabaseInformationSchema',
        'rinfo.DatabaseInformationParameterVariables',
        'rinfo.DatabaseInformationParameterStatus',
        'rinfo.DatabaseInformationParameterVariablesGlobal',
        'rinfo.DatabaseInformationParameterStatusGlobal'
    ]
):
    """
    Database engine type, based `MySQL`.
    """


    @property
    def async_database(self) -> 'DatabaseEngineAsync':
        """
        Same engine `DatabaseEngineAsync` instance.
        """

        # Build.
        db = DatabaseEngineAsync(
            self.host,
            self.port,
            self.username,
            self.password,
            self.database,
            self.pool_size,
            self.max_overflow,
            self.pool_timeout,
            self.pool_recycle,
            self.echo,
            **self.query
        )

        return db


class DatabaseEngineAsync(
    DatabaseEngineSuper[
        AsyncEngine,
        'rconn.DatabaseConnectionAsync',
        'rexec.DatabaseExecuteAsync',
        'rorm.DatabaseORMAsync',
        'rbuild.DatabaseBuildAsync',
        'rconfig.DatabaseConfigAsync',
        'rinfo.DatabaseInformationSchemaAsync',
        'rinfo.DatabaseInformationParameterVariablesAsync',
        'rinfo.DatabaseInformationParameterStatusAsync',
        'rinfo.DatabaseInformationParameterVariablesGlobalAsync',
        'rinfo.DatabaseInformationParameterStatusGlobalAsync'
    ]
):
    """
    Asynchronous database engine type, based `MySQL`.
    """


    @property
    def sync_database(self) -> DatabaseEngine:
        """
        Same engine `Database` instance.
        """

        # Build.
        db = DatabaseEngine(
            self.host,
            self.port,
            self.username,
            self.password,
            self.database,
            self.pool_size,
            self.max_overflow,
            self.pool_timeout,
            self.pool_recycle,
            self.echo,
            **self.query
        )

        return db


    async def dispose(self) -> None:
        """
        Dispose asynchronous connections.
        """

        # Dispose.
        await self.engine.dispose()
