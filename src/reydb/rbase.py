# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-07-18 23:36:56
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Base methods.
"""


from typing import Any, TypedDict, Literal
from sqlalchemy.engine.base import Engine, Connection
from sqlalchemy.engine.url import URL
from reykit.rbase import Base, throw
from reykit.rre import search


__all__ = (
    'DatabaseBase',
    'extract_url',
    'extract_engine'
)


URLParameters = TypedDict(
    'URLParameters',
    {
        'drivername': str,
        'backend': str,
        'driver': str | None,
        'username': str | None,
        'password': str | None,
        'host': str | None,
        'port': str | None,
        'database': str | None,
        'query': dict[str, str] | None
    }
)


class DatabaseBase(Base):
    """
    Database base type.
    """


def extract_url(url: str | URL) -> URLParameters:
    """
    Extract parameters from URL of string.

    Parameters
    ----------
    url : URL of string.

    Returns
    -------
    URL parameters.
    """

    # Extract.
    match url:

        ## Type str.
        case str():
            pattern_remote = r'^([^+]+)\+?([^:]+)??://([^:]+):([^@]+)@([^:]+):(\d+)[/]?([^\?]+)?\??(\S+)?$'
            pattern_local = r'^([^+]+)\+?([^:]+)??:////?([^\?]+)[\?]?(\S+)?$'

            ### Server.
            if (result_remote := search(pattern_remote, url)) is not None:
                (
                    backend,
                    driver,
                    username,
                    password,
                    host,
                    port,
                    database,
                    query_str
                ) = result_remote
                port = int(port)

            ### SQLite.
            elif (result_local := search(pattern_local, url)) is not None:
                username = password = host = port = None
                (
                    backend,
                    driver,
                    database,
                    query_str
                ) = result_local

            ### Throw exception.
            else:
                throw(ValueError, url)

            if query_str is not None:
                query = {
                    key: value
                    for query_item_str in query_str.split('&')
                    for key, value in (query_item_str.split('=', 1),)
                }
            else:
                query = {}

        ## Type URL.
        case URL():
            drivername = url.drivername
            username = url.username
            password = url.password
            host = url.host
            port = url.port
            database = url.database
            query = dict(url.query)

    ## Drivername.
    if driver is None:
        drivername = backend
    else:
        drivername = f'{backend}+{driver}'

    # Generate parameter.
    params = {
        'drivername': drivername,
        'backend': backend,
        'driver': driver,
        'username': username,
        'password': password,
        'host': host,
        'port': port,
        'database': database,
        'query': query
    }

    return params


def extract_engine(engine: Engine | Connection) -> dict[
    Literal[
        'drivername', 'username', 'password', 'host', 'port', 'database', 'query',
        'pool_size', 'max_overflow', 'pool_timeout', 'pool_recycle'
    ],
    Any
]:
    """
    Extract parameters from `Engine` or `Connection` object.

    Parameters
    ----------
    engine : Engine or Connection object.

    Returns
    -------
    Extracted parameters.
    """

    ## Extract Engine object from Connection boject.
    if type(engine) == Connection:
        engine = engine.engine

    ## Extract.
    drivername: str = engine.url.drivername
    username: str | None = engine.url.username
    password: str | None = engine.url.password
    host: str | None = engine.url.host
    port: str | None = engine.url.port
    database: str | None = engine.url.database
    query: dict[str, str] = dict(engine.url.query)
    pool_size: int = engine.pool._pool.maxsize
    max_overflow: int = engine.pool._max_overflow
    pool_timeout: float = engine.pool._timeout
    pool_recycle: int = engine.pool._recycle

    # Generate parameter.
    params = {
        'drivername': drivername,
        'username': username,
        'password': password,
        'host': host,
        'port': port,
        'database': database,
        'query': query,
        'pool_size': pool_size,
        'max_overflow': max_overflow,
        'pool_timeout': pool_timeout,
        'pool_recycle': pool_recycle
    }

    return params
