# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database methods.
"""


from urllib.parse import quote as urllib_quote
from pymysql.constants.CLIENT import MULTI_STATEMENTS
from sqlalchemy import create_engine as sqlalchemy_create_engine
from sqlalchemy.engine.base import Engine
from reykit.rtext import join_data_text

from .rbase import DatabaseBase, extract_url


__all__ = (
    'Database',
)


class Database(DatabaseBase):
    """
    Database type.
    Based `MySQL`.
    """

    # Whether default to report execution.
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
        pool_recycle: int | None = None,
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
            - `None`: Automatic select.
                When is remote server database, then is database variable `wait_timeout` value.
                When is local database file, then is `-1`.
            - `Literal[-1]`: No recycle.
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
        self.engine = self.__create_engine()

        # Server recycle time.
        if pool_recycle is None:
            wait_timeout = self.variables['wait_timeout']
            if wait_timeout is not None:
                self.pool_recycle = int(wait_timeout)
            self.engine.pool._recycle = self.pool_recycle


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


    def __create_engine(self) -> Engine:
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
        engine = sqlalchemy_create_engine(**engine_params)

        return engine


    @property
    def count_conn(self) -> tuple[int, int]:
        """
        Count number of keep open and allowed overflow connection.

        Returns
        -------
        Number of keep open and allowed overflow connection.
        """

        # Count.
        _overflow = self.engine.pool._overflow
        if _overflow < 0:
            keep_n = self.pool_size + _overflow
            overflow_n = 0
        else:
            keep_n = self.pool_size
            overflow_n = _overflow

        return keep_n, overflow_n


    def connect(self, autocommit: bool = False):
        """
        Build `DatabaseConnection` instance.

        Parameters
        ----------
        autocommit: Whether automatic commit connection.

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
        Build `database execute` instance.

        Returns
        -------
        Instance.
        """

        # Build.
        dbconn = self.connect(True)
        exec = dbconn.execute

        return exec


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
        for database_name in database_names:
            schema_dict[database_name] = None

        return schema_dict


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
        info['count'] = self.count_conn
        text = join_data_text(info)

        return text
