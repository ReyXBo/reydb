# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-09-23 00:50:32
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database ORM methods.
"""


from typing import Self, Any, Type, TypeVar, Generic, Final, overload
from collections.abc import Callable
from functools import wraps as functools_wraps
from inspect import iscoroutinefunction as inspect_iscoroutinefunction
from pydantic import ConfigDict, field_validator as pydantic_field_validator, model_validator as pydantic_model_validator
from sqlalchemy.orm import SessionTransaction
from sqlalchemy.ext.asyncio import AsyncSessionTransaction
from sqlalchemy.sql import sqltypes
from sqlalchemy.sql.sqltypes import TypeEngine
from sqlalchemy.sql.dml import Insert, Update, Delete
from sqlmodel import SQLModel, Session, Table
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.main import SQLModelMetaclass, FieldInfo, default_registry
from sqlmodel.sql._expression_select_cls import SelectOfScalar as Select
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
    'DatabaseORMModel',
    'DatabaseORMModelField',
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

        # Handle parameter.
        if attrs['__module__'] == '__main__':
            table_args = attrs.setdefault('__table_args__', {})
            table_args['quote'] = True

            ## Charset.
            attrs.setdefault('__charset__', 'utf8mb4')
            table_args['mysql_charset'] = attrs.pop('__charset__')

            ## Name.
            if '__name__' in attrs:
                table_args['name'] = attrs.pop('__name__')

            ## Comment.
            if '__comment__' in attrs:
                table_args['comment'] = attrs.pop('__comment__')

            ## Field.
            for __name__ in attrs['__annotations__']:
                field = attrs.get(__name__)
                if field is None:
                    field = attrs[__name__] = DatabaseORMModelField()
                sa_column_kwargs: dict = field.sa_column_kwargs
                sa_column_kwargs.setdefault('name', __name__)

        # Super.
        new_cls = super().__new__(cls, name, bases, attrs, **kwargs)

        return new_cls


model_metaclass: SQLModelMetaclass = DatabaseORMModelMeta


class DatabaseORMModel(DatabaseORMBase, SQLModel, metaclass=model_metaclass):
    """
    Database ORM model type.

    Examples
    --------
    >>> class Foo(DatabaseORMModel, table=True):
    ...     __comment__ = 'Table comment.'
    ...     ...
    """


    def update(self, data: 'DatabaseORMModel | dict[dict, Any]') -> None:
        """
        Update attributes.

        Parameters
        ----------
        data : `DatabaseORMModel` or `dict`.
        """

        # Update.
        self.sqlmodel_update(data)


    def validate(self) -> Self:
        """
        Validate all attributes, and copy self instance to new instance.
        """

        # Validate.
        model = self.model_validate(self)

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
        instance = self.__class__(**data)

        return instance


    @property
    def data(self) -> dict[str, Any]:
        """
        All attributes data.

        Returns
        -------
        data.
        """

        # Get.
        data = self.model_dump()

        return data


    @classmethod
    def table(cls_or_self) -> Table | None:
        """
        Mapping `Table` instance.

        Returns
        -------
        Instance or null.
        """

        # Get.
        table: Table | None = getattr(cls_or_self, '__table__', None)

        return table


    @classmethod
    def comment(cls_or_self, comment: str) -> None:
        """
        Set table comment.

        Parameters
        ----------
        comment : Comment.
        """

        # Set.
        table = cls_or_self.table()
        table.comment = comment


class DatabaseORMModelField(DatabaseBase, FieldInfo):
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
        arg_default: Any | Callable[[], Any] | Null = Null,
        *,
        arg_name: str | None = None,
        field_default: str | None = None,
        filed_name: str | None = None,
        field_type: TypeEngine | None = None,
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
        arg_default: Any | Callable[[], Any] | Null = Null,
        **kwargs: Any
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        arg_default : Call argument default value.
        arg_name : Call argument name.
            - `None`: Same as attribute name.
        field_default : Database field defualt value.
        filed_name : Database field name.
            - `None`: Same as attribute name.
        field_type : Database field type.
            - `None`: Based type annotation automatic judgment.
        key : Whether the field is primary key.
        key_auto : Whether the field is automatic increment primary key.
        not_null : Whether the field is not null constraint.
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

        # Handle parameter.
        kwargs = {
            key: value
            for key, value in kwargs.items()
            if value not in (None, False)
        }
        kwargs.setdefault('sa_column_kwargs', {})
        kwargs['sa_column_kwargs']['quote'] = True

        ## Convert argument name.
        mapping_keys = {
            'arg_name': 'alias',
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

        ## Argument default.
        if (
            arg_default != Null
            and callable(arg_default)
        ):
            kwargs['default_factory'] = arg_default
        else:
            kwargs['default'] = arg_default

        ## Field default.
        if 'field_default' in kwargs:
            kwargs['sa_column_kwargs']['server_default'] = kwargs.pop('field_default')

        ## Field name.
        if 'filed_name' in kwargs:
            kwargs['sa_column_kwargs']['name'] = kwargs.pop('filed_name')

        ## Field type.
        if 'filed_name' in kwargs:
            kwargs['sa_column_kwargs']['type_'] = kwargs.pop('filed_type')

        ## Key auto.
        if 'key_auto' in kwargs:
            kwargs['sa_column_kwargs']['autoincrement'] = True
        else:
            kwargs['sa_column_kwargs']['autoincrement'] = False

        ## Non null.
        if 'not_null' in kwargs:
            kwargs['nullable'] = not kwargs.pop('not_null')
        else:
            kwargs['nullable'] = True

        ## Comment.
        if 'comment' in kwargs:
            kwargs['sa_column_kwargs']['comment'] = kwargs.pop('comment')

        # Super.
        super().__init__(**kwargs)


class DatabaseORMSuper(DatabaseORMBase, Generic[DatabaseT, DatabaseORMSessionT]):
    """
    Database ORM super type.

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

    metaData = default_registry.metadata
    Model = DatabaseORMModel
    Field = DatabaseORMModelField
    Config = ConfigDict
    types = sqltypes
    wrap_validate_model = pydantic_model_validator
    wrap_validate_filed = pydantic_field_validator


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

        # Handle parameter.
        if is_instance(model):
            model = type(model)

        # Build.
        match self:
            case DatabaseORMSession():
                select = DatabaseORMStatementSelect[DatabaseORMModelT](self, model)
            case DatabaseORMSessionAsync():
                select = DatabaseORMStatementSelectAsync[DatabaseORMModelT](self, model)

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
        # Handle parameter.
        if is_instance(model):
            model = type(model)

        # Build.
        match self:
            case DatabaseORMSession():
                insert = DatabaseORMStatementInsert[DatabaseORMModelT](self, model)
            case DatabaseORMSessionAsync():
                insert = DatabaseORMStatementInsertAsync[DatabaseORMModelT](self, model)

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

        # Handle parameter.
        if is_instance(model):
            model = type(model)

        # Build.
        match self:
            case DatabaseORMSession():
                update = DatabaseORMStatementUpdate[DatabaseORMModelT](self, model)
            case DatabaseORMSessionAsync():
                update = DatabaseORMStatementUpdateAsync[DatabaseORMModelT](self, model)

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

        # Handle parameter.
        if is_instance(model):
            model = type(model)

        # Build.
        match self:
            case DatabaseORMSession():
                delete = DatabaseORMStatementDelete[DatabaseORMModelT](self, model)
            case DatabaseORMSessionAsync():
                delete = DatabaseORMStatementDeleteAsync[DatabaseORMModelT](self, model)

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

        # Handle parameter.
        tables = [
            model.table()
            for model in models
        ]

        ## Check.
        if None in tables:
            throw(ValueError, tables)

        # Create.
        self.orm.metaData.create_all(self.orm.db.engine, tables, skip)


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

        # Handle parameter.
        tables = [
            model.table()
            for model in models
        ]

        ## Check.
        if None in tables:
            throw(ValueError, tables)

        # Drop.
        self.orm.metaData.drop_all(self.orm.db.engine, tables, skip)


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

        # Handle parameter.
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

        # Handle parameter.
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

        # Handle parameter.
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

        # Handle parameter.
        tables = [
            model.table()
            for model in models
        ]

        ## Check.
        if None in tables:
            throw(ValueError, tables)

        # Create.
        conn = await self.sess.connection()
        await conn.run_sync(self.orm.metaData.create_all, tables, skip)


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

        # Handle parameter.
        tables = [
            model.table()
            for model in models
        ]

        ## Check.
        if None in tables:
            throw(ValueError, tables)

        # Drop.
        conn = await self.sess.connection()
        await conn.run_sync(self.orm.metaData.drop_all, tables, skip)


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

        # Handle parameter.
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

        # Handle parameter.
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

        # Handle parameter.
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
            await self.sess.commit()
            await self.sess.close()
            await self.sess.orm.db.dispose()

        return result


class DatabaseORMStatementSelect(DatabaseORMStatement[list[DatabaseORMModelT]], Select, Generic[DatabaseORMModelT]):
    """
    Database ORM `select` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Select` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementInsert(DatabaseORMStatement[None], Insert, Generic[DatabaseORMModelT]):
    """
    Database ORM `insert` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Select` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementUpdate(DatabaseORMStatement[None], Update, Generic[DatabaseORMModelT]):
    """
    Database ORM `update` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Update` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementDelete(DatabaseORMStatement[None], Delete, Generic[DatabaseORMModelT]):
    """
    Database ORM `delete` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Delete` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementSelectAsync(DatabaseORMStatementAsync[list[DatabaseORMModelT]], Select, Generic[DatabaseORMModelT]):
    """
    Asynchronous database ORM `select` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Select` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementInsertAsync(DatabaseORMStatementAsync[None], Insert, Generic[DatabaseORMModelT]):
    """
    Asynchronous database ORM `insert` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Select` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementUpdateAsync(DatabaseORMStatementAsync[None], Update, Generic[DatabaseORMModelT]):
    """
    Asynchronous database ORM `update` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Update` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementDeleteAsync(DatabaseORMStatementAsync[None], Delete, Generic[DatabaseORMModelT]):
    """
    Asynchronous database ORM `delete` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Delete` type.
    """

    inherit_cache: Final = True
