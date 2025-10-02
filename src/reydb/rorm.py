# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-09-23 00:50:32
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database ORM methods.
"""


from typing import Self, Any, Type, Literal, TypeVar, Generic, Final, NoReturn, overload
from collections.abc import Callable
from functools import wraps as functools_wraps
from inspect import iscoroutinefunction as inspect_iscoroutinefunction
from pydantic import ConfigDict, field_validator as pydantic_field_validator, model_validator as pydantic_model_validator
from sqlalchemy import types, text as sqlalchemy_text
from sqlalchemy.orm import SessionTransaction, load_only
from sqlalchemy.orm.strategy_options import _AttrType
from sqlalchemy.sql import func as sqlalchemy_func
from sqlalchemy.sql.dml import Insert, Update, Delete
from sqlalchemy.sql.sqltypes import TypeEngine
from sqlalchemy.ext.asyncio import AsyncSessionTransaction
from sqlalchemy.dialects.mysql import types as types_mysql
from sqlmodel import SQLModel, Session, Table
from sqlmodel.main import SQLModelMetaclass, FieldInfo, default_registry
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.sql._expression_select_cls import SelectOfScalar as Select
from datetime import datetime, date, time, timedelta
from reykit.rbase import CallableT, Null, throw, is_instance

from . import rdb
from .rbase import (
    SessionT,
    SessionTransactionT,
    DatabaseBase
)


__all__ = (
    'DatabaseORMBase',
    'DatabaseORMModelMeta',
    'DatabaseORMModelField',
    'DatabaseORMModel',
    'DatabaseORMModelMethod',
    'DatabaseORMSuper',
    'DatabaseORM',
    'DatabaseORMAsync',
    'DatabaseORMSessionSuper',
    'DatabaseORMSession',
    'DatabaseORMSessionAsync',
    'DatabaseORMStatementSuper',
    'DatabaseORMStatement',
    'DatabaseORMStatementAsync',
    'DatabaseORMStatementSelect',
    'DatabaseORMStatementInsert',
    'DatabaseORMStatementUpdate',
    'DatabaseORMStatementDelete',
    'DatabaseORMStatementSelectAsync',
    'DatabaseORMStatementInsertAsync',
    'DatabaseORMStatementUpdateAsync',
    'DatabaseORMStatementDeleteAsync'
)


DatabaseT = TypeVar('DatabaseT', 'rdb.Database', 'rdb.DatabaseAsync')
DatabaseORMModelT = TypeVar('DatabaseORMModelT', bound='DatabaseORMModel')
DatabaseORMT = TypeVar('DatabaseORMT', 'DatabaseORM', 'DatabaseORMAsync')
DatabaseORMSessionT = TypeVar('DatabaseORMSessionT', 'DatabaseORMSession', 'DatabaseORMSessionAsync')
DatabaseORMStatementReturn = TypeVar('DatabaseORMStatementReturn')
DatabaseORMStatementSelectT = TypeVar('DatabaseORMStatementSelectT', 'DatabaseORMStatementSelect', 'DatabaseORMStatementSelectAsync')
DatabaseORMStatementInsertT = TypeVar('DatabaseORMStatementInsertT', 'DatabaseORMStatementInsert', 'DatabaseORMStatementInsertAsync')
DatabaseORMStatementUpdateT = TypeVar('DatabaseORMStatementUpdateT', 'DatabaseORMStatementUpdate', 'DatabaseORMStatementUpdateAsync')
DatabaseORMStatementDeleteT = TypeVar('DatabaseORMStatementDeleteT', 'DatabaseORMStatementDelete', 'DatabaseORMStatementDeleteAsync')


class DatabaseORMBase(DatabaseBase):
    """
    Database ORM base type.
    """


class DatabaseORMModelMeta(DatabaseORMBase, SQLModelMetaclass):
    """
    Database ORM base meta type.
    """


    def __new__(
        cls,
        name: str,
        bases: tuple[Type],
        attrs: dict[str, Any],
        **kwargs: Any
    ) -> Type:
        """
        Create type.

        Parameters
        ----------
        name : Type name.
        bases : Type base types.
        attrs : Type attributes and methods dictionary.
        kwargs : Type other key arguments.
        """

        # Set parameter.
        if '__annotations__' in attrs:
            table_args = attrs.setdefault('__table_args__', {})
            table_args['quote'] = True
            table_name = name.lower()

            ## Charset.
            attrs.setdefault('__charset__', 'utf8mb4')
            table_args['mysql_charset'] = attrs.pop('__charset__')

            ## Name.
            if '__name__' in attrs:
                attrs['__tablename__'] = table_name = attrs.pop('__name__')

            ## Comment.
            if '__comment__' in attrs:
                table_args['comment'] = attrs.pop('__comment__')

            ## Field.
            for attr_name in attrs['__annotations__']:
                attr_name: str
                if attr_name in attrs:
                    field = attrs[attr_name]
                    if type(field) != DatabaseORMModelField:
                        field = attrs[attr_name] = DatabaseORMModelField(field)
                else:
                    field = attrs[attr_name] = DatabaseORMModelField()
                sa_column_kwargs: dict = field.sa_column_kwargs
                sa_column_kwargs.setdefault('name', attr_name)

            ## Replace.
            table = default_registry.metadata.tables.get(table_name)
            if table is not None:
                default_registry.metadata.remove(table)

        # Super.
        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)

        return new_cls


    def __init__(
        cls,
        name: str,
        bases: tuple[Type],
        attrs: dict[str, Any],
        **kwargs: Any
    ) -> None:
        """
        Build type attributes.
        """

        # Super.
        super().__init__(name, bases, attrs, **kwargs)

        # Set parameter.
        if (
            '__annotations__' in attrs
            and hasattr(cls, '__table__')
        ):
            table: Table = cls.__table__
            for index in table.indexes:
                index_name = '_'.join(
                    column.key
                    for column in index.expressions
                )
                index.name = index_name


class DatabaseORMModelField(DatabaseORMBase, FieldInfo):
    """
    Database ORM model filed type.

    Examples
    --------
    >>> class Foo(DatabaseORMModel, table=True):
    ...     key: int = DatabaseORMModelField(key=True, commment='Field commment.')
    """


    @overload
    def __init__(
        self,
        field_type: TypeEngine | None = None,
        *,
        field_default: str | Literal[':time'] | Literal[':create_time'] | Literal[':update_time'] = None,
        arg_default: Any | Callable[[], Any] | Null.Type = Null,
        arg_update: Any | Callable[[], Any] = None,
        name: str | None = None,
        key: bool = False,
        key_auto: bool = False,
        not_null: bool = False,
        index_n: bool = False,
        index_u: bool = False,
        comment: str | None = None,
        unique: bool = False,
        re: str | None = None,
        len_min: int | None = None,
        len_max: int | None = None,
        num_gt: float | None = None,
        num_ge: float | None = None,
        num_lt: float | None = None,
        num_le: float | None = None,
        num_multiple: float | None = None,
        num_places: int | None = None,
        num_places_dec: int | None = None,
        **kwargs: Any
    ) -> None: ...

    def __init__(
        self,
        field_type: TypeEngine | None = None,
        **kwargs: Any
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        field_type : Database field type.
            - `None`: Based type annotation automatic judgment.
        field_default : Database field defualt value.
            - `Literal[':time']`: Set SQL syntax 'DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'.
            - `Literal[':create_time']`: Set SQL syntax 'DEFAULT CURRENT_TIMESTAMP'.
            - `Literal[':update_time']`: Set SQL syntax 'ON UPDATE CURRENT_TIMESTAMP'.
        arg_default : Call argument default value.
            - `Callable[[], Any]`: Call function and use return value.
        arg_update : In `Session` management, When commit update record, then default value is this value.
            - `Callable[[], Any]`: Call function and use return value.
        name : Call argument name and database field name.
            - `None`: Same as attribute name.
        key : Whether the field is primary key.
        key_auto : Whether the field is primary key and automatic increment.
        not_null : Whether the field is not null constraint.
            - `Litreal[False]`: When argument `arg_default` is `Null`, then set argument `arg_default` is `None`.
        index_n : Whether the field add normal index.
        index_u : Whether the field add unique index.
        comment : Field commment.
        unique : Require the sequence element if is all unique.
        re : Require the partial string if is match regular expression.
        len_min : Require the sequence or string minimum length.
        len_max : Require the sequence or string maximum length.
        num_gt : Require the number greater than this value. (i.e. `number > num_gt`)
        num_lt : Require the number less than this value. (i.e. `number < num_lt`)
        num_ge : Require the number greater than and equal to this value. (i.e. `number >= num_ge`)
        num_le : Require the number less than and equal to this value. (i.e. `number <= num_le`)
        num_multiple : Require the number to be multiple of this value. (i.e. `number % num_multiple == 0`)
        num_places : Require the number digit places maximum length.
        num_places_dec : Require the number decimal places maximum length.
        **kwargs : Other key arguments.
        """

        # Set parameter.
        kwargs = {
            key: value
            for key, value in kwargs.items()
            if value not in (None, False)
        }
        kwargs.setdefault('sa_column_kwargs', {})
        kwargs['sa_column_kwargs']['quote'] = True

        ## Convert argument name.
        mapping_keys = {
            'key': 'primary_key',
            'index_n': 'index',
            'index_u': 'unique',
            're': 'pattern',
            'len_min': ('min_length', 'min_items'),
            'len_max': ('max_length', 'max_items'),
            'num_gt': 'gt',
            'num_ge': 'ge',
            'num_lt': 'lt',
            'num_le': 'le',
            'num_multiple': 'multiple_of',
            'num_places': 'max_digits',
            'num_places_dec': 'decimal_places'
        }
        for key_old, key_new in mapping_keys.items():
            if type(key_new) != tuple:
                key_new = (key_new,)
            if key_old in kwargs:
                value = kwargs.pop(key_old)
                for key in key_new:
                    kwargs[key] = value

        ## Field type.
        if field_type is not None:
            kwargs['sa_type'] = field_type

        ## Name.
        if 'name' in kwargs:
            kwargs['alias'] = kwargs['sa_column_kwargs']['name'] = kwargs.pop('field_name')

        ## Key auto.
        if kwargs.get('key_auto'):
            kwargs['sa_column_kwargs']['autoincrement'] = True
            kwargs['primary_key'] = True
        else:
            kwargs['sa_column_kwargs']['autoincrement'] = False

        ## Key.
        if kwargs.get('primary_key'):
            kwargs['nullable'] = False

        ## Non null.
        if 'not_null' in kwargs:
            kwargs['nullable'] = not kwargs.pop('not_null')
        else:
            kwargs['nullable'] = True

        ## Field default.
        if 'field_default' in kwargs:
            field_default: str = kwargs.pop('field_default')
            if field_default == ':time':
                field_default = sqlalchemy_text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')
            if field_default == ':create_time':
                field_default = sqlalchemy_text('CURRENT_TIMESTAMP')
            elif field_default == ':update_time':
                if kwargs['nullable']:
                    field_default = sqlalchemy_text('NULL ON UPDATE CURRENT_TIMESTAMP')
                else:
                    field_default = sqlalchemy_text('NOT NULL ON UPDATE CURRENT_TIMESTAMP')
            kwargs['sa_column_kwargs']['server_default'] = field_default

        ## Argument default.
        arg_default = kwargs.pop('arg_default', Null)
        if arg_default == Null:
            if kwargs['nullable']:
                kwargs['default'] = None
        elif callable(arg_default):
            kwargs['default_factory'] = arg_default
        else:
            kwargs['default'] = arg_default

        ## Argument update.
        if 'arg_update' in kwargs:
            arg_update = kwargs.pop('arg_update')
            kwargs['sa_column_kwargs']['onupdate'] = arg_update

        ## Comment.
        if 'comment' in kwargs:
            kwargs['sa_column_kwargs']['comment'] = kwargs.pop('comment')

        # Super.
        super().__init__(**kwargs)


model_metaclass: SQLModelMetaclass = DatabaseORMModelMeta


class DatabaseORMModel(DatabaseORMBase, SQLModel, metaclass=model_metaclass):
    """
    Database ORM model type.

    Examples
    --------
    >>> class Foo(DatabaseORMModel, table=True):
    ...     __name__ = 'Table name, default is class name.'
    ...     __comment__ = 'Table comment.'
    ...     ...
    """


    @classmethod
    def _get_table(cls_or_self) -> Table:
        """
        Return mapping database table instance.

        Returns
        -------
        Table instance.
        """

        # Get.
        table: Table = cls_or_self.__table__

        return table


    @classmethod
    def _set_name(cls_or_self, name: str) -> None:
        """
        Set database table name.
        """

        # Get.
        table = cls_or_self._get_table()
        table.name = name


    @classmethod
    def _set_comment(cls_or_self, comment: str) -> None:
        """
        Set database table comment.
        """

        # Get.
        table = cls_or_self._get_table()
        table.comment = comment


    @property
    def _m(self):
        """
        Build database ORM model method instance.

        Returns
        -------
        Instance.
        """

        # Build.
        method = DatabaseORMModelMethod(self)

        return method


class DatabaseORMModelMethod(DatabaseORMBase):
    """
    Database ORM model method type.
    """


    def __init__(self, model: DatabaseORMModel) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        model : Database ORM model instance.
        """

        # Build.
        self.model = model


    @property
    def data(self) -> dict[str, Any]:
        """
        All attributes data.

        Returns
        -------
        data.
        """

        # Get.
        data = self.model.model_dump()

        return data


    def update(self, data: 'DatabaseORMModel | dict[dict, Any]') -> None:
        """
        Update attributes.

        Parameters
        ----------
        data : `DatabaseORMModel` or `dict`.
        """

        # Update.
        self.model.sqlmodel_update(data)


    def validate(self) -> Self:
        """
        Validate all attributes, and copy self instance to new instance.
        """

        # Validate.
        model = self.model.model_validate(self.model)

        return model


    def copy(self) -> Self:
        """
        Copy self instance to new instance.

        Returns
        -------
        New instance.
        """

        # Copy.
        data = self.data
        instance = self.model.__class__(**data)

        return instance


class DatabaseORMSuper(DatabaseORMBase, Generic[DatabaseT, DatabaseORMSessionT]):
    """
    Database ORM super type.
    """


    def __init__(self, db: DatabaseT) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: Database instance.
        """

        # Build.
        self.db = db
        self.__sess = self.session(True)

        ## Method.
        self.create = self.__sess.create
        self.drop = self.__sess.drop
        self.get = self.__sess.get
        self.gets = self.__sess.gets
        self.all = self.__sess.all
        self.add = self.__sess.add
        self.select = self.__sess.select
        self.insert = self.__sess.insert
        self.update = self.__sess.update
        self.delete = self.__sess.delete


    def session(self, autocommit: bool = False) -> DatabaseORMSessionT:
        """
        Build DataBase ORM session instance.

        Parameters
        ----------
        autocommit: Whether automatic commit execute.

        Returns
        -------
        Instance.
        """

        # Build.
        match self:
            case DatabaseORM():
                sess = DatabaseORMSession(self, autocommit)
            case DatabaseORMAsync():
                sess = DatabaseORMSessionAsync(self, autocommit)

        return sess


class DatabaseORM(DatabaseORMSuper['rdb.Database', 'DatabaseORMSession']):
    """
    Database ORM type.

    Attributes
    ----------
    metaData : Registry metadata instance.
    DatabaseModel : Database ORM model type.
    Field : Database ORM model field type.
    Config : Database ORM model config type.
    types : Database ORM model filed types module.
    wrap_validate_model : Create decorator of validate database ORM model.
    wrap_validate_filed : Create decorator of validate database ORM model field.
    """


class DatabaseORMAsync(DatabaseORMSuper['rdb.DatabaseAsync', 'DatabaseORMSessionAsync']):
    """
    Asynchronous database ORM type.

    Attributes
    ----------
    metaData : Registry metadata instance.
    DatabaseModel : Database ORM model type.
    Field : Database ORM model field type.
    Config : Database ORM model config type.
    types : Database ORM model filed types module.
    wrap_validate_model : Create decorator of validate database ORM model.
    wrap_validate_filed : Create decorator of validate database ORM model field.
    """


class DatabaseORMSessionSuper(
    DatabaseORMBase,
    Generic[
        DatabaseORMT,
        SessionT,
        SessionTransactionT,
        DatabaseORMStatementSelectT,
        DatabaseORMStatementInsertT,
        DatabaseORMStatementUpdateT,
        DatabaseORMStatementDeleteT
    ]
):
    """
    Database ORM session super type.
    """


    def __init__(
        self,
        orm: DatabaseORMT,
        autocommit: bool = False
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        orm : Database ORM instance.
        autocommit: Whether automatic commit execute.
        """

        # Build.
        self.orm = orm
        self.autocommit = autocommit
        self.sess: SessionT | None = None
        self.begin: SessionTransactionT | None = None


    def select(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT) -> DatabaseORMStatementSelectT:
        """
        Build database ORM select instance.

        Parameters
        ----------
        model : ORM model instance.

        Returns
        -------
        Instance.
        """

        # Set parameter.
        if is_instance(model):
            model = type(model)

        # Build.
        match self:
            case DatabaseORMSession():
                select = DatabaseORMStatementSelect(self, model)
            case DatabaseORMSessionAsync():
                select = DatabaseORMStatementSelectAsync(self, model)

        return select


    def insert(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT) -> DatabaseORMStatementInsertT:
        """
        Build database ORM insert instance.

        Parameters
        ----------
        model : ORM model instance.

        Returns
        -------
        Instance.
        """
        print(model)
        # Set parameter.
        if is_instance(model):
            model = type(model)

        # Build.
        match self:
            case DatabaseORMSession():
                insert = DatabaseORMStatementInsert(self, model)
            case DatabaseORMSessionAsync():
                insert = DatabaseORMStatementInsertAsync(self, model)

        return insert


    def update(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT) -> DatabaseORMStatementUpdateT:
        """
        Build database ORM update instance.

        Parameters
        ----------
        model : ORM model instance.

        Returns
        -------
        Instance.
        """

        # Set parameter.
        if is_instance(model):
            model = type(model)

        # Build.
        match self:
            case DatabaseORMSession():
                update = DatabaseORMStatementUpdate(self, model)
            case DatabaseORMSessionAsync():
                update = DatabaseORMStatementUpdateAsync(self, model)

        return update


    def delete(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT) -> DatabaseORMStatementDeleteT:
        """
        Build database ORM delete instance.

        Parameters
        ----------
        model : ORM model instance.

        Returns
        -------
        Instance.
        """

        # Set parameter.
        if is_instance(model):
            model = type(model)

        # Build.
        match self:
            case DatabaseORMSession():
                delete = DatabaseORMStatementDelete(self, model)
            case DatabaseORMSessionAsync():
                delete = DatabaseORMStatementDeleteAsync(self, model)

        return delete


class DatabaseORMSession(
    DatabaseORMSessionSuper[
        DatabaseORM,
        Session,
        SessionTransaction,
        'DatabaseORMStatementSelect',
        'DatabaseORMStatementInsert',
        'DatabaseORMStatementUpdate',
        'DatabaseORMStatementDelete'
    ]
):
    """
    Database ORM session type.
    """


    def __enter__(self) -> Self:
        """
        Enter syntax `with`.

        Returns
        -------
        Self.
        """

        return self


    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        *_
    ) -> None:
        """
        Exit syntax `with`.

        Parameters
        ----------
        exc_type : Exception type.
        """

        # Commit.
        if exc_type is None:
            self.commit()

        # Close.
        self.close()


    def get_sess(self) -> Session:
        """
        Get `Session` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.sess is None:
            self.sess = Session(self.orm.db.engine)

        return self.sess


    def get_begin(self) -> SessionTransaction:
        """
        Get `SessionTransaction` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.begin is None:
            conn = self.get_sess()
            self.begin = conn.begin()

        return self.begin


    def commit(self) -> None:
        """
        Commit cumulative executions.
        """

        # Commit.
        if self.begin is not None:
            self.begin.commit()
            self.begin = None


    def rollback(self) -> None:
        """
        Rollback cumulative executions.
        """

        # Rollback.
        if self.begin is not None:
            self.begin.rollback()
            self.begin = None


    def close(self) -> None:
        """
        Close database session.
        """

        # Close.
        if self.begin is not None:
            self.begin.close()
            self.begin = None
        if self.sess is not None:
            self.sess.close()
            self.sess = None


    def wrap_transact(method: CallableT) -> CallableT:
        """
        Decorator, automated transaction.

        Parameters
        ----------
        method : Method.

        Returns
        -------
        Decorated method.
        """


        # Define.
        @functools_wraps(method)
        def wrap(self: 'DatabaseORMSession', *args, **kwargs):

            # Session.
            if self.sess is None:
                self.sess = Session(self.orm.db.engine)

            # Begin.
            if self.begin is None:
                self.begin = self.sess.begin()

            # Execute.
            result = method(self, *args, **kwargs)

            # Autucommit.
            if self.autocommit:
                self.commit()
                self.close()

            return result


        return wrap


    @wrap_transact
    def create(
        self,
        *models: Type[DatabaseORMModel] | DatabaseORMModel,
        skip: bool = False
    ) -> None:
        """
        Create tables.

        Parameters
        ----------
        models : ORM model instances.
        skip : Whether skip existing table.
        """

        # Set parameter.
        tables = [
            model._get_table()
            for model in models
        ]

        ## Check.
        if None in tables:
            throw(ValueError, tables)

        # Create.
        metadata.create_all(self.orm.db.engine, tables, skip)


    @wrap_transact
    def drop(
        self,
        *models: Type[DatabaseORMModel] | DatabaseORMModel,
        skip: bool = False
    ) -> None:
        """
        Delete tables.

        Parameters
        ----------
        models : ORM model instances.
        skip : Skip not exist table.
        """

        # Set parameter.
        tables = [
            model._get_table()
            for model in models
        ]

        ## Check.
        if None in tables:
            throw(ValueError, tables)

        # Drop.
        metadata.drop_all(self.orm.db.engine, tables, skip)


    @wrap_transact
    def get(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT, key: Any | tuple[Any]) -> DatabaseORMModelT | None:
        """
        Select records by primary key.

        Parameters
        ----------
        model : ORM model type or instance.
        key : Primary key.
            - `Any`: Single primary key.
            - `tuple[Any]`: Composite primary key.

        Returns
        -------
        With records ORM model instance or null.
        """

        # Set parameter.
        if is_instance(model):
            model = type(model)

        # Get.
        result = self.sess.get(model, key)

        # Autucommit.
        if (
            self.autocommit
            and result is not None
        ):
            self.sess.expunge(result)

        return result


    @wrap_transact
    def gets(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT, *keys: Any | tuple[Any]) -> list[DatabaseORMModelT]:
        """
        Select records by primary key sequence.

        Parameters
        ----------
        model : ORM model type or instance.
        keys : Primary key sequence.
            - `Any`: Single primary key.
            - `tuple[Any]`: Composite primary key.

        Returns
        -------
        With records ORM model instance list.
        """

        # Set parameter.
        if is_instance(model):
            model = type(model)

        # Get.
        results = [
            result
            for key in keys
            if (result := self.sess.get(model, key)) is not None
        ]

        return results


    @wrap_transact
    def all(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT) -> list[DatabaseORMModelT]:
        """
        Select all records.

        Parameters
        ----------
        model : ORM model type or instance.

        Returns
        -------
        With records ORM model instance list.
        """

        # Set parameter.
        if is_instance(model):
            model = type(model)

        # Get.
        select = Select(model)
        models = self.sess.exec(select)
        models = list(models)

        return models


    @wrap_transact
    def add(self, *models: DatabaseORMModel) -> None:
        """
        Insert records.

        Parameters
        ----------
        models : ORM model instances.
        """

        # Add.
        self.sess.add_all(models)


    @wrap_transact
    def rm(self, *models: DatabaseORMModel) -> None:
        """
        Delete records.

        Parameters
        ----------
        models : ORM model instances.
        """

        # Delete.
        for model in models:
            self.sess.delete(model)


    @wrap_transact
    def refresh(self, *models: DatabaseORMModel) -> None:
        """
        Refresh records.

        Parameters
        ----------
        models : ORM model instances.
        """ 

        # Refresh.
        for model in models:
            self.sess.refresh(model)


    @wrap_transact
    def expire(self, *models: DatabaseORMModel) -> None:
        """
        Mark records to expire, refresh on next call.

        Parameters
        ----------
        models : ORM model instances.
        """ 

        # Refresh.
        for model in models:
            self.sess.expire(model)


    @overload
    def select(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT) -> 'DatabaseORMStatementSelect[list[DatabaseORMModelT]]': ...

    select = DatabaseORMSessionSuper.select


class DatabaseORMSessionAsync(
    DatabaseORMSessionSuper[
        DatabaseORMAsync,
        AsyncSession,
        AsyncSessionTransaction,
        'DatabaseORMStatementSelectAsync',
        'DatabaseORMStatementInsertAsync',
        'DatabaseORMStatementUpdateAsync',
        'DatabaseORMStatementDeleteAsync'
    ]
):
    """
    Asynchronous database ORM session type.
    """


    async def __aenter__(self) -> Self:
        """
        Asynchronous enter syntax `with`.

        Returns
        -------
        Self.
        """

        return self


    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        *_
    ) -> None:
        """
        Asynchronous exit syntax `with`.

        Parameters
        ----------
        exc_type : Exception type.
        """

        # Commit.
        if exc_type is None:
            await self.commit()

        # Close.
        await self.close()
        await self.orm.db.dispose()


    def get_sess(self) -> AsyncSession:
        """
        Get `AsyncSession` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.sess is None:
            self.sess = AsyncSession(self.orm.db.engine)

        return self.sess


    async def get_begin(self) -> AsyncSessionTransaction:
        """
        Asynchronous get `AsyncSessionTransaction` instance.

        Returns
        -------
        Instance.
        """

        # Create.
        if self.begin is None:
            sess = self.get_sess()
            self.begin = await sess.begin()

        return self.begin


    async def commit(self) -> None:
        """
        Asynchronous commit cumulative executions.
        """

        # Commit.
        if self.begin is not None:
            await self.begin.commit()
            self.begin = None


    async def rollback(self) -> None:
        """
        Asynchronous rollback cumulative executions.
        """

        # Rollback.
        if self.begin is not None:
            await self.begin.rollback()
            self.begin = None


    async def close(self) -> None:
        """
        Asynchronous close database session.
        """

        # Close.
        if self.begin is not None:
            await self.begin.rollback()
            self.begin = None
        if self.sess is not None:
            await self.sess.close()
            self.sess = None


    def wrap_transact(method: CallableT) -> CallableT:
        """
        Asynchronous decorator, automated transaction.

        Parameters
        ----------
        method : Method.

        Returns
        -------
        Decorated method.
        """


        # Define.
        @functools_wraps(method)
        async def wrap(self: 'DatabaseORMSessionAsync', *args, **kwargs):

            # Transaction.
            await self.get_begin()

            # Execute.
            if inspect_iscoroutinefunction(method):
                result = await method(self, *args, **kwargs)
            else:
                result = method(self, *args, **kwargs)

            # Automatic commit.
            if self.autocommit:
                await self.commit()
                await self.close()
                await self.orm.db.dispose()

            return result


        return wrap


    @wrap_transact
    async def create(
        self,
        *models: Type[DatabaseORMModel] | DatabaseORMModel,
        skip: bool = False
    ) -> None:
        """
        Asynchronous create tables.

        Parameters
        ----------
        models : ORM model instances.
        skip : Whether skip existing table.
        """

        # Set parameter.
        tables = [
            model._get_table()
            for model in models
        ]

        ## Check.
        if None in tables:
            throw(ValueError, tables)

        # Create.
        conn = await self.sess.connection()
        await conn.run_sync(metadata.create_all, tables, skip)


    @wrap_transact
    async def drop(
        self,
        *models: Type[DatabaseORMModel] | DatabaseORMModel,
        skip: bool = False
    ) -> None:
        """
        Asynchronous delete tables.

        Parameters
        ----------
        models : ORM model instances.
        skip : Skip not exist table.
        """

        # Set parameter.
        tables = [
            model._get_table()
            for model in models
        ]

        ## Check.
        if None in tables:
            throw(ValueError, tables)

        # Drop.
        conn = await self.sess.connection()
        await conn.run_sync(metadata.drop_all, tables, skip)


    @wrap_transact
    async def get(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT, key: Any | tuple[Any]) -> DatabaseORMModelT | None:
        """
        Asynchronous select records by primary key.

        Parameters
        ----------
        model : ORM model type or instance.
        key : Primary key.
            - `Any`: Single primary key.
            - `tuple[Any]`: Composite primary key.

        Returns
        -------
        With records ORM model instance or null.
        """

        # Set parameter.
        if is_instance(model):
            model = type(model)

        # Get.
        result = await self.sess.get(model, key)

        # Autucommit.
        if (
            self.autocommit
            and result is not None
        ):
            self.sess.expunge(result)

        return result


    @wrap_transact
    async def gets(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT, *keys: Any | tuple[Any]) -> list[DatabaseORMModelT]:
        """
        Asynchronous select records by primary key sequence.

        Parameters
        ----------
        model : ORM model type or instance.
        keys : Primary key sequence.
            - `Any`: Single primary key.
            - `tuple[Any]`: Composite primary key.

        Returns
        -------
        With records ORM model instance list.
        """

        # Set parameter.
        if is_instance(model):
            model = type(model)

        # Get.
        results = [
            result
            for key in keys
            if (result := await self.sess.get(model, key)) is not None
        ]

        return results


    @wrap_transact
    async def all(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT) -> list[DatabaseORMModelT]:
        """
        Asynchronous select all records.

        Parameters
        ----------
        model : ORM model type or instance.

        Returns
        -------
        With records ORM model instance list.
        """

        # Set parameter.
        if is_instance(model):
            model = type(model)

        # Get.
        select = Select(model)
        models = await self.sess.exec(select)
        models = list(models)

        return models


    @wrap_transact
    async def add(self, *models: DatabaseORMModel) -> None:
        """
        Asynchronous insert records.

        Parameters
        ----------
        models : ORM model instances.
        """

        # Add.
        self.sess.add_all(models)


    @wrap_transact
    async def rm(self, *models: DatabaseORMModel) -> None:
        """
        Asynchronous delete records.

        Parameters
        ----------
        models : ORM model instances.
        """

        # Delete.
        for model in models:
            await self.sess.delete(model)


    @wrap_transact
    async def refresh(self, *models: DatabaseORMModel) -> None:
        """
        Asynchronous refresh records.

        Parameters
        ----------
        models : ORM model instances.
        """ 

        # Refresh.
        for model in models:
            await self.sess.refresh(model)


    @wrap_transact
    async def expire(self, *models: DatabaseORMModel) -> None:
        """
        Asynchronous mark records to expire, refresh on next call.

        Parameters
        ----------
        models : ORM model instances.
        """ 

        # Refresh.
        for model in models:
            self.sess.expire(model)


    @overload
    def select(self, model: Type[DatabaseORMModelT] | DatabaseORMModelT) -> 'DatabaseORMStatementSelectAsync[list[DatabaseORMModelT]]': ...

    select = DatabaseORMSessionSuper.select


class DatabaseORMStatementSuper(DatabaseORMBase, Generic[DatabaseORMSessionT]):
    """
    Database ORM statement super type.
    """


    def __init__(
        self,
        sess: DatabaseORMSessionT,
        model: Type[DatabaseORMModelT]
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        sess : DataBase ORM session instance.
        model : ORM model instance.
        """

        # Super.
        super().__init__(model)

        # Build.
        self.sess = sess
        self.model = model


    @overload
    def with_only_columns(self) -> NoReturn: ...


class DatabaseORMStatement(DatabaseORMStatementSuper[DatabaseORMSession], Generic[DatabaseORMStatementReturn]):
    """
    Database ORM statement type.
    """


    def execute(self) -> DatabaseORMStatementReturn:
        """
        Execute statement.
        """

        # Transaction.
        self.sess.get_begin()

        # Execute.
        result = self.sess.sess.exec(self)

        ## Select.
        if isinstance(self, Select):
            result = list(result)
        else:
            result = None

        # Automatic commit.
        if self.sess.autocommit:

            ## Select.
            if isinstance(self, Select):
                for model in result:
                    if isinstance(model, DatabaseORMModel):
                        self.sess.sess.expunge(model)

            self.sess.commit()
            self.sess.close()

        return result


class DatabaseORMStatementAsync(DatabaseORMStatementSuper[DatabaseORMSessionAsync], Generic[DatabaseORMStatementReturn]):
    """
    Asynchronous dtabase ORM statement type.
    """


    async def execute(self) -> DatabaseORMStatementReturn:
        """
        Asynchronous execute statement.
        """

        # Transaction.
        await self.sess.get_begin()

        # Execute.
        result = await self.sess.sess.exec(self)

        ## Select.
        if isinstance(self, Select):
            result = list(result)
        else:
            result = None

        # Automatic commit.
        if self.sess.autocommit:

            ## Select.
            if isinstance(self, Select):
                for model in result:
                    if isinstance(model, DatabaseORMModel):
                        self.sess.sess.expunge(model)

            await self.sess.commit()
            await self.sess.close()
            await self.sess.orm.db.dispose()

        return result


class DatabaseORMStatementSelectSuper(DatabaseORMStatementSuper, Select):
    """
    Database ORM `select` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Select` type.
    """

    inherit_cache: Final = True


    def fields(self, *field: _AttrType) -> Self:
        """
        Replace select fiedls.

        Parameters
        ----------
        field : Field set.

        Returns
        -------
        Set self.
        """

        # Set.
        set = load_only(*field)
        select = self.options(set)

        return select


class DatabaseORMStatementSelect(DatabaseORMStatement, DatabaseORMStatementSelectSuper, Generic[DatabaseORMStatementReturn]):
    """
    Database ORM `select` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Select` type.
    """

    inherit_cache: Final = True


    @overload
    def execute(self) -> DatabaseORMStatementReturn: ...

    execute = DatabaseORMStatement.execute


class DatabaseORMStatementInsert(DatabaseORMStatement[None], Insert):
    """
    Database ORM `insert` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Select` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementUpdate(DatabaseORMStatement[None], Update):
    """
    Database ORM `update` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Update` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementDelete(DatabaseORMStatement[None], Delete):
    """
    Database ORM `delete` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Delete` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementSelectAsync(DatabaseORMStatementAsync, DatabaseORMStatementSelectSuper, Generic[DatabaseORMStatementReturn]):
    """
    Asynchronous database ORM `select` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Select` type.
    """

    inherit_cache: Final = True


    @overload
    async def execute(self) -> DatabaseORMStatementReturn: ...

    execute = DatabaseORMStatementAsync.execute


class DatabaseORMStatementInsertAsync(DatabaseORMStatementAsync[None], Insert):
    """
    Asynchronous database ORM `insert` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Select` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementUpdateAsync(DatabaseORMStatementAsync[None], Update):
    """
    Asynchronous database ORM `update` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Update` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementDeleteAsync(DatabaseORMStatementAsync[None], Delete):
    """
    Asynchronous database ORM `delete` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Delete` type.
    """

    inherit_cache: Final = True


# Simple path.

## Registry metadata instance.
metadata = default_registry.metadata

## Database ORM model type.
Model = DatabaseORMModel

## Database ORM model field type.
Field = DatabaseORMModelField

## Database ORM model config type.
Config = ConfigDict

## Database ORM model filed types.
types = types

## Database ORM model MySQL filed types.
types_mysql = types_mysql

## Database ORM model functions.
funcs = sqlalchemy_func

## Create decorator of validate database ORM model.
wrap_validate_model = pydantic_model_validator

## Create decorator of validate database ORM model field.
wrap_validate_filed = pydantic_field_validator

## Time type.
Datetime = datetime
Date = date
Time = time
Timedelta = timedelta
