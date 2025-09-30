# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-07-18 23:36:56
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Base methods.
"""


from typing import Any, TypedDict, Literal, TypeVar
from enum import EnumType
from sqlalchemy import Engine, Connection, Transaction, text as sqlalchemy_text
from sqlalchemy.orm import Session, SessionTransaction
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection, AsyncTransaction, AsyncSession, AsyncSessionTransaction
from sqlalchemy.engine.url import URL
from sqlalchemy.sql.elements import TextClause
from reykit.rbase import Base, throw
from reykit.rre import search
from reykit.rdata import to_json
from reykit.rre import findall


__all__ = (
    'DatabaseBase',
    'handle_sql',
    'handle_data',
    'extract_url',
    'extract_engine',
    'get_syntax',
    'is_multi_sql'
)


EngineT = TypeVar('EngineT', Engine, AsyncEngine)
ConnectionT = TypeVar('ConnectionT', Connection, AsyncConnection)
TransactionT = TypeVar('TransactionT', Transaction, AsyncTransaction)
SessionT = TypeVar('SessionT', Session, AsyncSession)
SessionTransactionT = TypeVar('SessionTransactionT', SessionTransaction, AsyncSessionTransaction)


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


def handle_sql(sql: str | TextClause) -> TextClause:
    """
    Handle SQL.

    Parameters
    ----------
    sql : SQL in method `sqlalchemy.text` format, or TextClause object.

    Returns
    -------
    TextClause instance.
    """

    # Handle parameter.
    if type(sql) == TextClause:
        sql = sql.text

    # Handle.
    sql = sql.strip()
    if sql[-1] != ';':
        sql += ';'
    sql = sqlalchemy_text(sql)

    return sql


def handle_data(data: list[dict], sql: str | TextClause) -> list[dict]:
    """
    Handle data based on the content of SQL.

    Parameters
    ----------
    data : Data set for filling.
    sql : SQL in method `sqlalchemy.text` format, or TextClause object.

    Returns
    -------
    Filled data.
    """

    # Handle parameter.
    if type(sql) == TextClause:
        sql = sql.text

    # Extract keys.
    pattern = '(?<!\\\\):(\\w+)'
    sql_keys = findall(pattern, sql)

    # Extract keys of syntax "in".
    pattern = '[iI][nN]\\s+(?<!\\\\):(\\w+)'
    sql_keys_in = findall(pattern, sql)

    # Loop.
    for row in data:
        if row == {}:
            continue
        for key in sql_keys:
            value = row.get(key)

            # Empty string.
            if value == '':
                value = None

            # Convert.
            elif (
                type(value) in (list, dict)
                and key not in sql_keys_in
            ):
                value = to_json(value)

            # Enum.
            elif isinstance(type(value), EnumType):
                value = value.value

            row[key] = value

    return data


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


def get_syntax(self, sql: str | TextClause) -> list[str]:
    """
    Extract SQL syntax type for each segment form SQL.

    Parameters
    ----------
    sql : SQL text or TextClause object.

    Returns
    -------
    SQL syntax type for each segment.
    """

    # Handle parameter.
    if type(sql) == TextClause:
        sql = sql.text

    # Extract.
    syntax = [
        search('[a-zA-Z]+', sql_part).upper()
        for sql_part in sql.split(';')
        if sql_part != ''
    ]

    return syntax


def is_multi_sql(self, sql: str | TextClause) -> bool:
    """
    Judge whether it is multi segment SQL.

    Parameters
    ----------
    sql : SQL text or TextClause object.

    Returns
    -------
    Judgment result.
    """

    # Handle parameter.
    if type(sql) == TextClause:
        sql = sql.text

    # Judge.
    if ';' in sql.rstrip()[:-1]:
        return True
    return False
