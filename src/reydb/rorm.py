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
from pydantic import ConfigDict, field_validator as pydantic_field_validator, model_validator as pydantic_model_validator
from sqlalchemy.orm import SessionTransaction
from sqlalchemy.sql.dml import Insert, Update, Delete
from sqlmodel import SQLModel, Session, Table, Field as sqlmodel_Field
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


class DatabaseORMModelField(DatabaseBase):
    """
    Database ORM model filed type.
    """


class DatabaseORMModel(DatabaseORMBase, SQLModel):
    """
    Database ORM model type.
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
    def table(cls_or_self) -> Table:
        """
        Mapping `Table` instance.

        Returns
        -------
        Instance.
        """

        # Get.
        table: Table = cls_or_self.__table__

        return table


    @classmethod
    def comment(cls_or_self) -> str | None:
        """
        Table comment.

        Returns
        -------
        Comment.
        """

        # Get.
        table = cls_or_self.table()
        comment = table.comment

        return comment


    @classmethod
    def set_comment(cls_or_self, comment: str) -> None:
        """
        Set table comment.

        Parameters
        ----------
        comment : Comment.
        """

        # Set.
        table = cls_or_self.table()
        table.comment = comment


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
    Config = ConfigDict
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

        ## Avoid descriptor error.
        self.Field = sqlmodel_Field


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
        check : Skip existing table.
        """

        # Create.
        for model in models:
            table = model.table()
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
        check : Skip not exist table.
        """

        # Create.
        for model in models:
            table = model.table()
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
