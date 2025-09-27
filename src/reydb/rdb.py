# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database methods.
"""


from typing import Literal, Final, overload
from urllib.parse import quote as urllib_quote
from pymysql.constants.CLIENT import MULTI_STATEMENTS
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine as sqlalchemy_create_async_engine
from reykit.rtext import join_data_text

from .rbase import DatabaseBase, extract_url


__all__ = (
    'Database',
)


class Database(DatabaseBase):
    """
    Database type, based `MySQL`.
    """

    default_report: bool = False


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
        self.query = query

        # Create engine.
        self.engine = self.__create_engine(False)
        self.aengine = self.__create_engine(True)


    @property
    def backend(self) -> str:
        """
        Database backend name.

        Returns
        -------
        Name.
        """

        # Get.
        url_params = extract_url(self.url)
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
        url_params = extract_url(self.url)
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
        if self.is_async:
            url_ = f'mysql+aiomysql://{self.username}:{password}@{self.host}:{self.port}/{self.database}'
        else:
            url_ = f'mysql+pymysql://{self.username}:{password}@{self.host}:{self.port}/{self.database}'

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


    @overload
    def __create_engine(self, is_async: Literal[False]) -> Engine: ...

    @overload
    def __create_engine(self, is_async: Literal[True]) -> AsyncEngine: ...

    def __create_engine(self, is_async: bool) -> Engine | AsyncEngine:
        """
        Create database `Engine` object.

        Parameters
        ----------
        is_async : Whether to use asynchronous engine.

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
        if is_async:
            engine = sqlalchemy_create_async_engine(**engine_params)
        else:
            engine = sqlalchemy_create_engine(**engine_params)

        return engine


    def __conn_count(self, is_async: bool) -> tuple[int, int]:
        """
        Count number of keep open and allowed overflow connection.

        Parameters
        ----------
        is_async : Whether to use asynchronous engine.

        Returns
        -------
        Number of keep open and allowed overflow connection.
        """

        # Handle parameter.
        if is_async:
            engine = self.aengine
        else:
            engine = self.engine

        # Count.
        _overflow: int = engine.pool._overflow
        if _overflow < 0:
            keep_n = self.pool_size + _overflow
            overflow_n = 0
        else:
            keep_n = self.pool_size
            overflow_n = _overflow

        return keep_n, overflow_n


    @property
    def conn_count(self) -> tuple[int, int]:
        """
        Count number of keep open and allowed overflow connection.

        Returns
        -------
        Number of keep open and allowed overflow connection.
        """

        # Count.
        keep_n, overflow_n = self.__conn_count(False)

        return keep_n, overflow_n


    @property
    def aconn_count(self) -> tuple[int, int]:
        """
        Count number of keep open and allowed overflow asynchronous connection.

        Returns
        -------
        Number of keep open and allowed overflow asynchronous connection.
        """

        # Count.
        keep_n, overflow_n = self.__conn_count(True)

        return keep_n, overflow_n


    def schema(self, filter_default: bool = True) -> dict[str, dict[str, list[str]]]:
        """
        Get schemata of databases and tables and columns.

        Parameters
        ----------
        filter_default : Whether filter default database.

        Returns
        -------
        Schemata of databases and tables and columns.
        """

        # Handle parameter.
        filter_db = (
            'information_schema',
            'performance_schema',
            'mysql',
            'sys'
        )
        if filter_default:
            where_database = 'WHERE `SCHEMA_NAME` NOT IN :filter_db\n'
            where_column = '    WHERE `TABLE_SCHEMA` NOT IN :filter_db\n'
        else:
            where_database = where_column = ''

        # Select.
        sql = (
            'SELECT GROUP_CONCAT(`SCHEMA_NAME`) AS `TABLE_SCHEMA`, NULL AS `TABLE_NAME`, NULL AS `COLUMN_NAME`\n'
            'FROM `information_schema`.`SCHEMATA`\n'
            f'{where_database}'
            'UNION ALL (\n'
            '    SELECT `TABLE_SCHEMA`, `TABLE_NAME`, `COLUMN_NAME`\n'
            '    FROM `information_schema`.`COLUMNS`\n'
            f'{where_column}'
            '    ORDER BY `TABLE_SCHEMA`, `TABLE_NAME`, `ORDINAL_POSITION`\n'
            ')'
        )
        result = self.execute(sql, filter_db=filter_db)

        # Convert.
        database_names, *_ = result.fetchone()
        database_names: list[str] = database_names.split(',')
        schema_dict = {}
        for database, table, column in result:
            if database in database_names:
                database_names.remove(database)

            ## Index database.
            if database not in schema_dict:
                schema_dict[database] = {table: [column]}
                continue
            table_dict: dict = schema_dict[database]

            ## Index table. 
            if table not in table_dict:
                table_dict[table] = [column]
                continue
            column_list: list = table_dict[table]

            ## Add column.
            column_list.append(column)

        ## Add empty database.
        for name in database_names:
            schema_dict[name] = None

        return schema_dict


    def connect(self, autocommit: bool = False):
        """
        Build `DatabaseConnection` instance.

        Parameters
        ----------
        autocommit: Whether automatic commit execute.

        Returns
        -------
        Database connection instance.
        """

        # Import.
        from .rconn import DatabaseConnection

        # Build.
        conn = DatabaseConnection(self, autocommit)

        return conn


    @property
    def execute(self):
        """
        Build `DatabaseExecute` instance.

        Returns
        -------
        Instance.
        """

        # Build.
        dbconn = self.connect(True)
        exec = dbconn.execute

        return exec


    def aconnect(self, autocommit: bool = False):
        """
        Build `DatabaseConnectionAsync` instance.

        Parameters
        ----------
        autocommit: Whether automatic commit execute.

        Returns
        -------
        Database connection instance.
        """

        # Import.
        from .rconn import DatabaseConnectionAsync

        # Build.
        conn = DatabaseConnectionAsync(self, autocommit)

        return conn


    @property
    def aexecute(self):
        """
        Build `DatabaseConnectionAsync` instance.

        Returns
        -------
        Instance.
        """

        # Build.
        dbconn = self.aconnect(True)
        exec = dbconn.execute

        return exec


    @property
    def orm(self):
        """
        Build `DatabaseORM` instance.

        Returns
        -------
        Instance.
        """

        # Import.
        from .rorm import DatabaseORM

        # Build.
        orm = DatabaseORM(self)

        return orm


    @property
    def info(self):
        """
        Build `DatabaseInformationSchema` instance.

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

        # Import.
        from .rinfo import DatabaseInformationSchema

        # Build.
        dbischema = DatabaseInformationSchema(self)

        return dbischema


    @property
    def build(self):
        """
        Build `DatabaseBuild` instance.

        Returns
        -------
        Instance.
        """

        # Import.
        from .rbuild import DatabaseBuild

        # Build.
        dbbuild = DatabaseBuild(self)

        return dbbuild


    @property
    def file(self):
        """
        Build `DatabaseFile` instance.

        Returns
        -------
        Instance.
        """

        # Import.
        from .rfile import DatabaseFile

        # Build.
        dbfile = DatabaseFile(self)

        return dbfile


    @property
    def error(self):
        """
        Build `DatabaseError` instance.

        Returns
        -------
        Instance.
        """

        # Import.
        from .rerror import DatabaseError

        # Build.
        dbfile = DatabaseError(self)

        return dbfile


    @property
    def config(self):
        """
        Build `DatabaseConfig` instance.

        Returns
        -------
        Instance.
        """

        # Import.
        from .rconfig import DatabaseConfig

        # Build.
        dbconfig = DatabaseConfig(self)

        return dbconfig


    @property
    def status(self):
        """
        Build `DatabaseParametersStatus` instance.

        Returns
        -------
        Instance.
        """

        # Import.
        from .rparam import DatabaseParametersStatus

        # Build.
        dbps = DatabaseParametersStatus(self, False)

        return dbps


    @property
    def global_status(self):
        """
        Build global `DatabaseParametersStatus` instance.

        Returns
        -------
        Instance.
        """

        # Import.
        from .rparam import DatabaseParametersStatus

        # Build.
        dbps = DatabaseParametersStatus(self, True)

        return dbps


    @property
    def variables(self):
        """
        Build `DatabaseParametersVariable` instance.

        Returns
        -------
        Instance.
        """

        # Import.
        from .rparam import DatabaseParametersVariable

        # Build.
        dbpv = DatabaseParametersVariable(self, False)

        return dbpv


    @property
    def global_variables(self):
        """
        Build global `DatabaseParametersVariable` instance.

        Returns
        -------
        Instance.
        """

        # Import.
        from .rparam import DatabaseParametersVariable

        # Build.

        ## SQLite.
        dbpv = DatabaseParametersVariable(self, True)

        return dbpv


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
        info['aconn_count'] = self.aconn_count
        text = join_data_text(info)

        return text
