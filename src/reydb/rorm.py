# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-09-23 00:50:32
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database ORM methods.
"""


from typing import Self, Any, Type, TypeVar, Generic, Final
from functools import wraps as functools_wraps
from sqlalchemy.orm import SessionTransaction
from sqlalchemy.sql.dml import Insert, Update, Delete
from sqlmodel import SQLModel, Session, Field as sqlmodel_Field
from sqlmodel.sql._expression_select_cls import SelectOfScalar as Select
from reykit.rbase import CallableT, is_instance

from .rbase import DatabaseBase
from .rdb import Database


__all__ = (
    'DatabaseORMBase',
    'DatabaseORMModel',
    'DatabaseORM',
    'DatabaseORMSession',
    'DatabaseORMStatement',
    'DatabaseORMStatementSelect',
    'DatabaseORMStatementInsert',
    'DatabaseORMStatementUpdate',
    'DatabaseORMStatementDelete'
)


class DatabaseORMBase(DatabaseBase):
    """
    Database ORM base type.
    """


class DatabaseORMModel(DatabaseORMBase, SQLModel):
    """
    Database ORM model type.
    """


    def copy(self) -> Self:
        """
        Copy self instance to new instance.

        Returns
        -------
        New instance.
        """

        # Copy.
        data = self.model_dump()
        instance = self.__class__(**data)

        return instance


ModelT = TypeVar('ModelT', bound=DatabaseORMModel)


class DatabaseORM(DatabaseORMBase):
    """
    Database ORM type.

    Attributes
    ----------
    DatabaseModel : Database ORM model type.
    Field : Factory function of database ORM model field.
    """

    Model = DatabaseORMModel
    Field = sqlmodel_Field


    def __init__(self, db: Database) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: `Database` instance.
        """

        # Build.
        self.db = db

        ## Avoid descriptor error.
        self.Field = sqlmodel_Field


    def session(self):
        """
        Build `DataBaseORMSession` instance.

        Returns
        -------
        Instance.
        """

        # Build.
        sess = DataBaseORMSession(self)

        return sess


    __call__ = session


class DataBaseORMSession(DatabaseORMBase):
    """
    Database ORM session type, based ORM model.
    """


    def __init__(self, orm: DatabaseORM) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        orm : `DatabaseORM` instance.
        """

        # Build.
        self.orm = orm
        self.session = Session(orm.db.engine)
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
        self.session.close()


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


    def wrap_begin(method: CallableT) -> CallableT:
        """
        Decorator, create and store `SessionTransaction` instance.

        Parameters
        ----------
        method : Method.

        Returns
        -------
        Decorated method.
        """


        # Define.
        @functools_wraps(method)
        def wrap(self, *args, **kwargs):

            # Create.
            if self.begin is None:
                self.begin = self.session.begin()

            # Execute.
            result = method(self, *args, **kwargs)

            return result


        return wrap


    @wrap_begin
    def get(self, model: Type[ModelT] | ModelT, key: Any | tuple[Any]) -> ModelT | None:
        """
        select records by primary key.

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

        return result


    @wrap_begin
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


    @wrap_begin
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

        # Get.
        models = self.select(model).execute()

        return models


    @wrap_begin
    def add(self, *models: DatabaseORMModel) -> None:
        """
        Insert records.

        Parameters
        ----------
        models : ORM model instances.
        """

        # Add.
        self.session.add_all(models)


    @wrap_begin
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


    @wrap_begin
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


    @wrap_begin
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


    @wrap_begin
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


    @wrap_begin
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


    @wrap_begin
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


    @wrap_begin
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

        # Build.
        self.sess = sess
        self.model = model

        # Init.
        super().__init__(self.model)


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
