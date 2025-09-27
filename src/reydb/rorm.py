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
from pydantic import ConfigDict, field_validator as pydantic_field_validator, model_validator as pydantic_model_validator
from sqlalchemy.orm import SessionTransaction
from sqlalchemy.sql import sqltypes
from sqlalchemy.sql.sqltypes import TypeEngine
from sqlalchemy.sql.dml import Insert, Update, Delete
from sqlmodel import SQLModel, Session, Table
from sqlmodel.main import SQLModelMetaclass, FieldInfo
from sqlmodel.sql._expression_select_cls import SelectOfScalar as Select
from reykit.rbase import CallableT, Null, is_instance

from .rbase import DatabaseBase
from .rdb import Database


__all__ = (
    'DatabaseORMBase',
    'DatabaseORMModelMeta',
    'DatabaseORMModel',
    'DatabaseORMModelField',
    'DatabaseORM',
    'DatabaseORMSession',
    'DatabaseORMStatement',
    'DatabaseORMStatementSelect',
    'DatabaseORMStatementInsert',
    'DatabaseORMStatementUpdate',
    'DatabaseORMStatementDelete'
)


ModelT = TypeVar('ModelT', bound='DatabaseORMModel')


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
            if '__comment__' in attrs:
                table_args['comment'] = attrs.pop('__comment__')

            ## Field.
            for __name__ in attrs['__annotations__']:
                field = attrs.get(__name__)
                if field is None:
                    field = attrs[__name__] = DatabaseORMModelField()
                sa_column_kwargs: dict = field.sa_column_kwargs
                sa_column_kwargs.setdefault('name', __name__)

        # Base.
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
        non_null: bool = False,
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
        non_null : Whether the field is non null constraint.
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
        if 'non_null' in kwargs:
            kwargs['nullable'] = not kwargs.pop('non_null')
        else:
            kwargs['nullable'] = True

        ## Comment.
        if 'comment' in kwargs:
            kwargs['sa_column_kwargs']['comment'] = kwargs.pop('comment')

        # Base.
        super().__init__(**kwargs)


class DatabaseORM(DatabaseORMBase):
    """
    Database ORM type.

    Attributes
    ----------
    DatabaseModel : Database ORM model type.
    Field : Factory function of database ORM model field.
    """

    Model = DatabaseORMModel
    Field = DatabaseORMModelField
    Config = ConfigDict
    tyeps = sqltypes
    wrap_validate_filed = pydantic_field_validator
    wrap_validate_model = pydantic_model_validator


    def __init__(self, db: Database) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: `Database` instance.
        """

        # Build.
        self.db = db
        self._session = self.session(True)

        ## Method.
        self.get = self._session.get
        self.gets = self._session.gets
        self.all = self._session.all
        self.add = self._session.add


    def session(self, autocommit: bool = False):
        """
        Build `DataBaseORMSession` instance.

        Parameters
        ----------
        autocommit: Whether automatic commit execute.

        Returns
        -------
        Instance.
        """

        # Build.
        sess = DataBaseORMSession(self, autocommit)

        return sess


    def create(
        self,
        *models: Type[DatabaseORMModel] | DatabaseORMModel,
        skip: bool = False
    ) -> None:
        """
        Create table.

        Parameters
        ----------
        models : ORM model instances.
        check : Skip existing table and not mapping model.
        """

        # Create.
        for model in models:
            table = model.table()
            if (
                not skip
                or table is not None
            ):
                table.create(self.db.engine, checkfirst=skip)


    def drop(
        self,
        *models: Type[DatabaseORMModel] | DatabaseORMModel,
        skip: bool = False
    ) -> None:
        """
        Delete table.

        Parameters
        ----------
        models : ORM model instances.
        check : Skip not exist table and not mapping model.
        """

        # Create.
        for model in models:
            table = model.table()
            if (
                not skip
                or table is not None
            ):
                table.drop(self.db.engine, checkfirst=skip)


class DataBaseORMSession(DatabaseORMBase):
    """
    Database ORM session type, based ORM model.
    """


    def __init__(
        self,
        orm: 'DatabaseORM',
        autocommit: bool = False
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        orm : `DatabaseORM` instance.
        autocommit: Whether automatic commit execute.
        """

        # Build.
        self.orm = orm
        self.autocommit = autocommit
        self.session: Session | None = None
        self.begin: SessionTransaction | None = None


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
        Close database connection.
        """

        # Close.
        if self.session is not None:
            self.session.close()
            self.session = None


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
        else:
            self.close()


    __del__ = close


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
        def wrap(self: 'DataBaseORMSession', *args, **kwargs):

            # Session.
            if self.session is None:
                self.session = Session(self.orm.db.engine)

            # Begin.
            if self.begin is None:
                self.begin = self.session.begin()

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
        Create table.

        Parameters
        ----------
        models : ORM model instances.
        check : Skip existing table.
        """

        # Create.
        for model in models:
            table = model.table()
            table.create(self.session.connection(), checkfirst=skip)


    @wrap_transact
    def drop(
        self,
        *models: Type[DatabaseORMModel] | DatabaseORMModel,
        skip: bool = False
    ) -> None:
        """
        Delete table.

        Parameters
        ----------
        models : ORM model instances.
        check : Skip not exist table.
        """

        # Create.
        for model in models:
            table = model.table()
            table.drop(self.session.connection(), checkfirst=skip)


    @wrap_transact
    def get(self, model: Type[ModelT] | ModelT, key: Any | tuple[Any]) -> ModelT | None:
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
        result = self.session.get(model, key)

        # Autucommit.
        if (
            self.autocommit
            and result is not None
        ):
            self.session.expunge(result)

        return result


    @wrap_transact
    def gets(self, model: Type[ModelT] | ModelT, *keys: Any | tuple[Any]) -> list[ModelT]:
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
            if (result := self.session.get(model, key)) is not None
        ]

        return results


    @wrap_transact
    def all(self, model: Type[ModelT] | ModelT) -> list[ModelT]:
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
        models = self.session.exec(select)
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
        self.session.add_all(models)


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
            self.session.delete(model)


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
            self.session.refresh(model)


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
            self.session.expire(model)


    @wrap_transact
    def select(self, model: Type[ModelT] | ModelT):
        """
        Build `DatabaseORMSelect` instance.

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
        select = DatabaseORMStatementSelect[ModelT](self, model)

        return select


    @wrap_transact
    def insert(self, model: Type[ModelT] | ModelT):
        """
        Build `DatabaseORMInsert` instance.

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
        select = DatabaseORMStatementInsert[ModelT](self, model)

        return select


    @wrap_transact
    def update(self, model: Type[ModelT] | ModelT):
        """
        Build `DatabaseORMUpdate` instance.

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
        select = DatabaseORMStatementUpdate[ModelT](self, model)

        return select


    @wrap_transact
    def delete(self, model: Type[ModelT] | ModelT):
        """
        Build `DatabaseORMDelete` instance.

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
        select = DatabaseORMStatementDelete[ModelT](self, model)

        return select


class DatabaseORMStatement(DatabaseORMBase):
    """
    Database ORM statement type.
    """


    def __init__(
        self,
        sess: DataBaseORMSession,
        model: Type[ModelT]
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        sess : `DataBaseORMSession` instance.
        model : ORM model instance.
        """

        # Base.
        super().__init__(self.model)

        # Build.
        self.sess = sess
        self.model = model


    def execute(self) -> None:
        """
        Execute statement.
        """

        # Execute.
        self.sess.session.exec(self)


class DatabaseORMStatementSelect(DatabaseORMStatement, Select, Generic[ModelT]):
    """
    Database ORM `select` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Select` type.
    """

    inherit_cache: Final = True


    def execute(self) -> list[ModelT]:
        """
        Execute self statement.

        Returns
        -------
        With records ORM model instance list.
        """

        # Execute.
        result = self.sess.session.exec(self)
        models = list(result)

        return models


class DatabaseORMStatementInsert(Generic[ModelT], DatabaseORMStatement, Insert):
    """
    Database ORM `insert` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Select` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementUpdate(Generic[ModelT], DatabaseORMStatement, Update):
    """
    Database ORM `update` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Update` type.
    """

    inherit_cache: Final = True


class DatabaseORMStatementDelete(Generic[ModelT], DatabaseORMStatement, Delete):
    """
    Database ORM `delete` statement type.

    Attributes
    ----------
    inherit_cache : Compatible `Delete` type.
    """

    inherit_cache: Final = True
