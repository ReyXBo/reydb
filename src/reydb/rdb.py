# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database methods.
"""


from typing import Generic
from urllib.parse import quote as urllib_quote
from pymysql.constants.CLIENT import MULTI_STATEMENTS
from sqlalchemy import Engine, create_engine as sqlalchemy_create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine as sqlalchemy_create_async_engine
from reykit.rtext import join_data_text

from . import rbase, rbuild, rconfig, rconn, rerror, rexec, rfile, rinfo, rorm, rparam


__all__ = (
    'DatabaseSuper',
    'Database',
    'DatabaseAsync'
)


class DatabaseSuper(
    rbase.DatabaseBase,
    Generic[
        rbase.EngineT,
        rbase.DatabaseConnectionT,
        rbase.DatabaseExecuteT,
        rbase.DatabaseSchemaT
    ]
):
    """
    Database super type, based `MySQL`.
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
        report: bool = False,
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
        report : Whether report SQL execute information.
        query : Remote server database parameters.
        """

        # Handle parameter.
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
        self.report = report
        self.query = query

        ## Create engine.
        self.engine = self.__create_engine()


    def __str__(self) -> str:
        """
        Return connection information text.
        """

        # Generate.
        filter_key = (
            'engine',
            'connection',
            'rdatabase',
            'begin'
        )
        info = {
            key: value
            for key, value in self.__dict__.items()
            if key not in filter_key
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
            case Database():
                url_ = f'mysql+pymysql://{self.username}:{password}@{self.host}:{self.port}/{self.database}'
            case DatabaseAsync():
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

        # Handle parameter.
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
            case Database():
                engine = sqlalchemy_create_engine(**engine_params)
            case DatabaseAsync():
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


    def connect(self, autocommit: bool = False) -> rbase.DatabaseConnectionT:
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
            case Database():
                conn = rconn.DatabaseConnection(self, autocommit)
            case DatabaseAsync():
                conn = rconn.DatabaseConnectionAsync(self, autocommit)

        return conn


    @property
    def execute(self) -> rbase.DatabaseExecuteT:
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
    def orm(self):
        """
        Build database ORM instance.

        Returns
        -------
        Instance.
        """

        # Build.
        orm = rorm.DatabaseORM(self)

        return orm


    @property
    def build(self):
        """
        Build database build instance.

        Returns
        -------
        Instance.
        """

        # Build.
        dbbuild = rbuild.DatabaseBuild(self)

        return dbbuild


    @property
    def file(self):
        """
        Build database file instance.

        Returns
        -------
        Instance.
        """

        # Build.
        dbfile = rfile.DatabaseFile(self)

        return dbfile


    @property
    def error(self):
        """
        Build database error instance.

        Returns
        -------
        Instance.
        """

        # Build.
        dbfile = rerror.DatabaseError(self)

        return dbfile


    @property
    def config(self):
        """
        Build database config instance.

        Returns
        -------
        Instance.
        """

        # Build.
        dbconfig = rconfig.DatabaseConfig(self)

        return dbconfig


    @property
    def info(self):
        """
        Build database information schema instance.

        Returns
        -------
        Instance.

        Examples
        --------
        Get databases information of server.
        >>> databases_info = DatabaseInformationSchema()

        Get tables information of database.
        >>> tables_info = DatabaseInformationSchema.database()

        Get columns information of table.
        >>> columns_info = DatabaseInformationSchema.database.table()

        Get database attribute.
        >>> database_attr = DatabaseInformationSchema.database['attribute']

        Get table attribute.
        >>> database_attr = DatabaseInformationSchema.database.table['attribute']

        Get column attribute.
        >>> database_attr = DatabaseInformationSchema.database.table.column['attribute']
        """

        # Build.
        dbischema = rinfo.DatabaseInformationSchema(self)

        return dbischema


    @property
    def schema(self) -> rbase.DatabaseSchemaT:
        """
        Build database schema instance.

        Returns
        -------
        Instance.
        """

        # Build.
        match self:
            case Database():
                schema = rparam.DatabaseSchema(self)
            case DatabaseAsync():
                schema = rparam.DatabaseSchemaAsync(self)

        return schema


    @property
    def status(self):
        """
        Build database parameters status instance.

        Returns
        -------
        Instance.
        """

        # Build.
        dbps = rparam.DatabaseParametersStatus(self, False)

        return dbps


    @property
    def status_global(self):
        """
        Build global database parameters status instance.

        Returns
        -------
        Instance.
        """

        # Build.
        dbps = rparam.DatabaseParametersStatus(self, True)

        return dbps


    @property
    def variables(self):
        """
        Build database parameters variable instance.

        Returns
        -------
        Instance.
        """

        # Build.
        dbpv = rparam.DatabaseParametersVariable(self, False)

        return dbpv


    @property
    def variables_global(self):
        """
        Build global database parameters variable instance.

        Returns
        -------
        Instance.
        """

        # Build.

        ## SQLite.
        dbpv = rparam.DatabaseParametersVariable(self, True)

        return dbpv


class Database(
    DatabaseSuper[
        Engine,
        'rconn.DatabaseConnection',
        'rexec.DatabaseExecute',
        'rparam.DatabaseSchema'
    ]
):
    """
    Database type, based `MySQL`.
    """


class DatabaseAsync(
    DatabaseSuper[
        AsyncEngine,
        'rconn.DatabaseConnectionAsync',
        'rexec.DatabaseExecuteAsync',
        'rparam.DatabaseSchemaAsync'
    ]
):
    """
    Asynchronous database type, based `MySQL`.
    """


    async def dispose(self) -> None:
        """
        Dispose asynchronous connections.
        """

        # Dispose.
        await self.engine.dispose()
