# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-14 23:05:35
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database build methods.
"""


from typing import TypedDict, NotRequired, Literal, Type, TypeVar, Generic
from copy import deepcopy
from reykit.rbase import throw, is_instance
from reykit.rstdout import ask

from . import rdb
from .rbase import DatabaseBase
from .rorm import DatabaseORMModel


__all__ = (
    'DatabaseBuildSuper',
    'DatabaseBuild',
    'DatabaseBuildAsync'
)


FieldSet = TypedDict(
    'FieldSet',
    {
        'name': str,
        'type': str,
        'constraint': NotRequired[str | None],
        'comment': NotRequired[str | None],
        'position': NotRequired[Literal['first'] | str | None]
    }
)
type IndexType = Literal['noraml', 'unique', 'fulltext', 'spatial']
IndexSet = TypedDict(
    'IndexSet',
    {
        'name': str,
        'fields' : str | list[str],
        'type': IndexType,
        'comment': NotRequired[str | None]
    }
)
DatabaseT = TypeVar('DatabaseT', 'rdb.Database', 'rdb.DatabaseAsync')


class DatabaseBuildSuper(DatabaseBase, Generic[DatabaseT]):
    """
    Database build super type.
    """


    def __init__(self, db: DatabaseT) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db: Database instance.
        """

        # Set attribute.
        self.db = db


    def get_sql_create_database(
        self,
        name: str,
        character: str = 'utf8mb4',
        collate: str = 'utf8mb4_0900_ai_ci'
    ) -> str:
        """
        Get SQL of create database.

        Parameters
        ----------
        name : Database name.
        character : Character set.
        collate : Collate rule.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Generate.
        sql = f'CREATE DATABASE `{name}` CHARACTER SET {character} COLLATE {collate}'

        return sql


    def __get_field_sql(
        self,
        name: str,
        type_: str,
        constraint: str = 'DEFAULT NULL',
        comment: str | None = None,
        position: str | None = None,
        old_name: str | None = None
    ) -> str:
        """
        Get a field set SQL.

        Parameters
        ----------
        name : Field name.
        type_ : Field type.
        constraint : Field constraint.
        comment : Field comment.
        position : Field position.
        old_name : Field old name.

        Returns
        -------
        Field set SQL.
        """

        # Handle parameter.

        ## Constraint.
        constraint = ' ' + constraint

        ## Comment.
        if comment is None:
            comment = ''
        else:
            comment = f" COMMENT '{comment}'"

        ## Position.
        match position:
            case None:
                position = ''
            case 'first':
                position = ' FIRST'
            case _:
                position = f' AFTER `{position}`'

        ## Old name.
        if old_name is None:
            old_name = ''
        else:
            old_name = f'`{old_name}` '

        # Generate.
        sql = f'{old_name}`{name}` {type_}{constraint}{comment}{position}'

        return sql


    def __get_index_sql(
        self,
        name: str,
        fields: str | list[str],
        type_: IndexType,
        comment: str | None = None
    ) -> str:
        """
        Get a index set SQL.

        Parameters
        ----------
        name : Index name.
        fields : Index fileds.
        type\\_ : Index type.
        comment : Index comment.

        Returns
        -------
        Index set SQL.
        """

        # Handle parameter.
        if fields.__class__ == str:
            fields = [fields]
        match type_:
            case 'noraml':
                type_ = 'KEY'
                method = ' USING BTREE'
            case 'unique':
                type_ = 'UNIQUE KEY'
                method = ' USING BTREE'
            case 'fulltext':
                type_ = 'FULLTEXT KEY'
                method = ''
            case 'spatial':
                type_ = 'SPATIAL KEY'
                method = ''
            case _:
                throw(ValueError, type_)
        if comment in (None, ''):
            comment = ''
        else:
            comment = f" COMMENT '{comment}'"

        # Generate.

        ## Fields.
        sql_fields = ', '.join(
            [
                f'`{field}`'
                for field in fields
            ]
        )

        ## Join.
        sql = f'{type_} `{name}` ({sql_fields}){method}{comment}'

        return sql


    def get_sql_create_table(
        self,
        path: str | tuple[str, str],
        fields: FieldSet | list[FieldSet],
        primary: str | list[str] | None = None,
        indexes: IndexSet | list[IndexSet] | None = None,
        engine: str = 'InnoDB',
        increment: int = 1,
        charset: str = 'utf8mb4',
        collate: str = 'utf8mb4_0900_ai_ci',
        comment: str | None = None
    ) -> str:
        """
        Get SQL of create table.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        fields : Fields set table.
            - `Key 'name'`: Field name, required.
            - `Key 'type'`: Field type, required.
            - `Key 'constraint'`: Field constraint.
                `Empty or None`: Use 'DEFAULT NULL'.
                `str`: Use this value.
            - `Key 'comment'`: Field comment.
                `Empty or None`: Not comment.
                `str`: Use this value.
            - `Key 'position'`: Field position.
                `None`: Last.
                `Literal['first']`: First.
                `str`: After this field.
        primary : Primary key fields.
            - `str`: One field.
            - `list[str]`: Multiple fileds.
        indexes : Index set table.
            - `Key 'name'`: Index name, required.
            - `Key 'fields'`: Index fields, required.
                `str`: One field.
                `list[str]`: Multiple fileds.
            - `Key 'type'`: Index type.
                `Literal['noraml']`: Noraml key.
                `Literal['unique']`: Unique key.
                `Literal['fulltext']`: Full text key.
                `Literal['spatial']`: Spatial key.
            - `Key 'comment'`: Field comment.
                `Empty or None`: Not comment.
                `str`: Use this value.
        engine : Engine type.
        increment : Automatic Increment start value.
        charset : Charset type.
        collate : Collate type.
        comment : Table comment.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.db.database, path
        else:
            database, table = path
        if fields.__class__ == dict:
            fields = [fields]
        if primary.__class__ == str:
            primary = [primary]
        if primary in ([], ['']):
            primary = None
        if indexes.__class__ == dict:
            indexes = [indexes]

        ## Compatible dictionary key name.
        fields = deepcopy(fields)
        for row in fields:
            row['type_'] = row.pop('type')
        if indexes is not None:
            indexes = deepcopy(indexes)
            for row in indexes:
                row['type_'] = row.pop('type')

        # Generate.

        ## Fields.
        sql_fields = [
            self.__get_field_sql(**field)
            for field in fields
        ]

        ## Primary.
        if primary is not None:
            keys = ', '.join(
                [
                    f'`{key}`'
                    for key in primary
                ]
            )
            sql_primary = f'PRIMARY KEY ({keys}) USING BTREE'
            sql_fields.append(sql_primary)

        ## Indexes.
        if indexes is not None:
            sql_indexes = [
                self.__get_index_sql(**index)
                for index in indexes
            ]
            sql_fields.extend(sql_indexes)

        ## Comment.
        if comment is None:
            sql_comment = ''
        else:
            sql_comment = f" COMMENT='{comment}'"

        ## Join.
        sql_fields = ',\n    '.join(sql_fields)
        sql = (
            f'CREATE TABLE `{database}`.`{table}`(\n'
            f'    {sql_fields}\n'
            f') ENGINE={engine} AUTO_INCREMENT={increment} CHARSET={charset} COLLATE={collate}{sql_comment}'
        )

        return sql


    def get_sql_create_view(
        self,
        path: str | tuple[str, str],
        select: str
    ) -> str:
        """
        Get SQL of create view.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        select : View select SQL.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.db.database, path
        else:
            database, table = path

        # Generate SQL.
        select = select.replace('\n', '\n    ')
        sql = f'CREATE VIEW `{database}`.`{table}` AS (\n    {select}\n)'

        return sql


    def get_sql_create_view_stats(
        self,
        path: str | tuple[str, str],
        items: list[dict]
    ) -> str:
        """
        Get SQL of create stats view.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        items : Items set table.
            - `Key 'name'`: Item name, required.
            - `Key 'select'`: Item select SQL, must only return one value, required.
            - `Key 'comment'`: Item comment.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Check.
        if items == []:
            throw(ValueError, items)

        # Generate select SQL.
        item_first = items[0]
        select_first = "SELECT '%s' AS `item`,\n(\n    %s\n) AS `value`,\n%s AS `comment`" % (
            item_first['name'],
            item_first['select'].replace('\n', '\n    '),
            (
                'NULL'
                if 'comment' not in item_first
                else "'%s'" % item_first['comment']
            )
        )
        selects = [
            "SELECT '%s',\n(\n    %s\n),\n%s" % (
                item['name'],
                item['select'].replace('\n', '\n    '),
                (
                    'NULL'
                    if 'comment' not in item
                    else "'%s'" % item['comment']
                )
            )
            for item in items[1:]
        ]
        selects[0:0] = [select_first]
        select = '\nUNION\n'.join(selects)

        # Create.
        sql = self.get_sql_create_view(path, select)

        return sql


    def get_sql_drop_database(
        self,
        database: str
    ) -> str:
        """
        Get SQL of drop database.

        Parameters
        ----------
        database : Database name.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Generate.
        sql = f'DROP DATABASE `{database}`'

        return sql


    def get_sql_drop_table(
        self,
        path: str | tuple[str, str]
    ) -> str:
        """
        Get SQL of drop table.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.db.database, path
        else:
            database, table = path

        # Generate.
        sql = f'DROP TABLE `{database}`.`{table}`'

        return sql


    def get_sql_drop_view(
        self,
        path: str | tuple[str, str]
    ) -> str:
        """
        Get SQL of drop view.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.db.database, path
        else:
            database, table = path

        # Generate SQL.
        sql = 'DROP VIEW `%s`.`%s`' % (database, table)

        return sql


    def get_sql_alter_database(
        self,
        database: str,
        character: str | None = None,
        collate: str | None = None
    ) -> str:
        """
        Get SQL of alter database.

        Parameters
        ----------
        database : Database name.
        character : Character set.
            - `None`: Not alter.
            - `str`: Alter to this value.
        collate : Collate rule.
            - `None`: Not alter.
            - `str`: Alter to this value.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Generate.

        ## Character.
        if character is None:
            sql_character = ''
        else:
            sql_character = f' CHARACTER SET {character}'

        ## Collate.
        if collate is None:
            sql_collate = ''
        else:
            sql_collate = f' COLLATE {collate}'

        ## Join.
        sql = f'ALTER DATABASE `{database}`{sql_character}{sql_collate}'

        return sql


    def get_sql_alter_table_add(
        self,
        path: str | tuple[str, str],
        fields: FieldSet | list[FieldSet] | None = None,
        primary: str | list[str] | None = None,
        indexes: IndexSet | list[IndexSet] | None = None
    ) -> str:
        """
        Get SQL of alter table add filed.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        fields : Fields set table.
            - `Key 'name'`: Field name, required.
            - `Key 'type'`: Field type, required.
            - `Key 'constraint'`: Field constraint.
                `Empty or None`: Use 'DEFAULT NULL'.
                `str`: Use this value.
            - `Key 'comment'`: Field comment.
                `Empty or None`: Not comment.
                `str`: Use this value.
            - `Key 'position'`: Field position.
                `None`: Last.
                `Literal['first']`: First.
                `str`: After this field.
        primary : Primary key fields.
            - `str`: One field.
            - `list[str]`: Multiple fileds.
        indexes : Index set table.
            - `Key 'name'`: Index name, required.
            - `Key 'fields'`: Index fields, required.
                `str`: One field.
                `list[str]`: Multiple fileds.
            - `Key 'type'`: Index type.
                `Literal['noraml']`: Noraml key.
                `Literal['unique']`: Unique key.
                `Literal['fulltext']`: Full text key.
                `Literal['spatial']`: Spatial key.
            - `Key 'comment'`: Field comment.
                `Empty or None`: Not comment.
                `str`: Use this value.

        Returns
        -------
        SQL.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.db.database, path
        else:
            database, table = path
        if fields.__class__ == dict:
            fields = [fields]
        if primary.__class__ == str:
            primary = [primary]
        if primary in ([], ['']):
            primary = None
        if indexes.__class__ == dict:
            indexes = [indexes]

        ## Compatible dictionary key name.
        fields = deepcopy(fields)
        for row in fields:
            row['type_'] = row.pop('type')
        if indexes is not None:
            indexes = deepcopy(indexes)
            for row in indexes:
                row['type_'] = row.pop('type')

        # Generate.
        sql_content = []

        ## Fields.
        if fields is not None:
            sql_fields = [
                'COLUMN ' + self.__get_field_sql(**field)
                for field in fields
            ]
            sql_content.extend(sql_fields)

        ## Primary.
        if primary is not None:
            keys = ', '.join(
                [
                    f'`{key}`'
                    for key in primary
                ]
            )
            sql_primary = f'PRIMARY KEY ({keys}) USING BTREE'
            sql_content.append(sql_primary)

        ## Indexes.
        if indexes is not None:
            sql_indexes = [
                self.__get_index_sql(**index)
                for index in indexes
            ]
            sql_content.extend(sql_indexes)

        ## Join.
        sql_content = ',\n    ADD '.join(sql_content)
        sql = (
            f'ALTER TABLE `{database}`.`{table}`\n'
            f'    ADD {sql_content}'
        )

        return sql


    def get_sql_alter_table_drop(
        self,
        path: str | tuple[str, str],
        fields: str | list[str] | None = None,
        primary: bool = False,
        indexes: str | list[str] | None = None
    ) -> str:
        """
        Get SQL of alter table drop field.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        fields : Delete fields name.
        primary : Whether delete primary key.
        indexes : Delete indexes name.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.db.database, path
        else:
            database, table = path
        if fields.__class__ == str:
            fields = [fields]
        if indexes.__class__ == str:
            indexes = [indexes]

        # Generate.
        sql_content = []

        ## Fields.
        if fields is not None:
            sql_fields = [
                'COLUMN ' + field
                for field in fields
            ]
            sql_content.extend(sql_fields)

        ## Primary.
        if primary:
            sql_primary = 'PRIMARY KEY'
            sql_content.append(sql_primary)

        ## Indexes.
        if indexes is not None:
            sql_indexes = [
                'INDEX ' + index
                for index in indexes
            ]
            sql_content.extend(sql_indexes)

        ## Join.
        sql_content = ',\n    DROP '.join(sql_content)
        sql = (
            f'ALTER TABLE `{database}`.`{table}`\n'
            f'    DROP {sql_content}'
        )

        return sql


    def get_sql_alter_table_change(
        self,
        path: str | tuple[str, str],
        fields: FieldSet | list[FieldSet] | None = None,
        rename: str | None = None,
        engine: str | None = None,
        increment: int | None = None,
        charset: str | None = None,
        collate: str | None = None
    ) -> str:
        """
        Get SQL of alter database.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        fields : Fields set table.
            - `Key 'name'`: Field name, required.
            - `Key 'type'`: Field type, required.
            - `Key 'constraint'`: Field constraint.
                `Empty or None`: Use 'DEFAULT NULL'.
                `str`: Use this value.
            - `Key 'comment'`: Field comment.
                `Empty or None`: Not comment.
                `str`: Use this value.
            - `Key 'position'`: Field position.
                `None`: Last.
                `Literal['first']`: First.
                `str`: After this field.
            - `Key 'old_name'`: Field old name.
        rename : Table new name.
        engine : Engine type.
        increment : Automatic Increment start value.
        charset : Charset type.
        collate : Collate type.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.db.database, path
        else:
            database, table = path
        if fields.__class__ == dict:
            fields = [fields]

        ## Compatible dictionary key name.
        fields = deepcopy(fields)
        for row in fields:
            row['type_'] = row.pop('type')

        # Generate.
        sql_content = []

        ## Rename.
        if rename is not None:
            sql_rename = f'RENAME `{database}`.`{rename}`'
            sql_content.append(sql_rename)

        ## Fields.
        if fields is not None:
            sql_fields = [
                '%s %s' % (
                    (
                        'MODIFY'
                        if 'old_name' not in field
                        else 'CHANGE'
                    ),
                    self.__get_field_sql(**field)
                )
                for field in fields
            ]
            sql_content.extend(sql_fields)

        ## Attribute.
        sql_attr = []

        ### Engine.
        if engine is not None:
            sql_engine = f'ENGINE={engine}'
            sql_attr.append(sql_engine)

        ### Increment.
        if increment is not None:
            sql_increment = f'AUTO_INCREMENT={increment}'
            sql_attr.append(sql_increment)

        ### Charset.
        if charset is not None:
            sql_charset = f'CHARSET={charset}'
            sql_attr.append(sql_charset)

        ### Collate.
        if collate is not None:
            sql_collate = f'COLLATE={collate}'
            sql_attr.append(sql_collate)

        if sql_attr != []:
            sql_attr = ' '.join(sql_attr)
            sql_content.append(sql_attr)

        ## Join.
        sql_content = ',\n    '.join(sql_content)
        sql = (
            f'ALTER TABLE `{database}`.`{table}`\n'
            f'    {sql_content}'
        )

        return sql


    def get_sql_alter_view(
        self,
        path: str | tuple[str, str],
        select: str
    ) -> str:
        """
        Get SQL of alter view.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        select : View select SQL.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.db.database, path
        else:
            database, table = path

        # Generate SQL.
        sql = 'ALTER VIEW `%s`.`%s` AS\n%s' % (database, table, select)

        return sql


    def get_sql_truncate_table(
        self,
        path: str | tuple[str, str]
    ) -> str:
        """
        Get SQL of truncate table.

        Parameters
        ----------
        path : Path.
            - `str`: Table name.
            - `tuple[str, str]`: Database name and table name.
        execute : Whether directly execute.

        Returns
        -------
        SQL.
        """

        # Handle parameter.
        if type(path) == str:
            database, table = self.db.database, path
        else:
            database, table = path

        # Generate.
        sql = f'TRUNCATE TABLE `{database}`.`{table}`'

        return sql


    def input_confirm_build(
        self,
        sql: str
    ) -> None:
        """
        Print tip text, and confirm execute SQL. If reject, throw exception.

        Parameters
        ----------
        sql : SQL.
        """

        # Confirm.
        text = 'Do you want to execute SQL to build the database? Otherwise stop program. (y/n) '
        command = ask(
            sql,
            text,
            title='SQL',
            frame='top'
        )

        # Check.
        while True:
            command = command.lower()
            match command:

                ## Confirm.
                case 'y':
                    break

                ## Stop.
                case 'n':
                    raise AssertionError('program stop')

                ## Reenter.
                case _:
                    text = 'Incorrect input, reenter. (y/n) '
                    command = input(text)


    def get_orm_table_text(self, model: DatabaseORMModel) -> str:
        """
        Get table text from ORM model.

        Parameters
        ----------
        model : ORM model instances.

        Returns
        -------
        Table text.
        """

        # Get.
        table = model._table()
        text = f'TABLE `{self.db.database}`.`{table}`'
        if 'mysql_charset' in table.kwargs:
            text += f" | CHARSET '{table.kwargs['mysql_charset']}'"
        if table.comment:
            text += f" | COMMENT '{table.comment}'"

        ## Field.
        text += '\n' + '\n'.join(
            [
                f'    FIELD `{column.name}` : {column.type}' + (
                    ' | NOT NULL'
                    if (
                        not column.nullable
                        or column.primary_key
                    )
                    else ' | NULL'
                ) + (
                    ''
                    if not column.primary_key
                    else ' | KEY AUTO'
                    if column.autoincrement
                    else ' | KEY'
                ) + (
                    f" | DEFAULT '{column.server_default.arg}'"
                    if column.server_default
                    else ''
                ) + (
                    f" | COMMMENT '{column.comment}'"
                    if column.comment
                    else ''
                )
                for column in table.columns
            ]
        )

        ## Index.
        if (table.indexes):
            text += '\n' + '\n'.join(
                [
                    (
                        '    UNIQUE'
                        if index.unique
                        else '    NORMAL'
                    ) + f' INDEX `{index.name}` : ' + ', '.join(
                        [
                            f'`{column.name}`'
                            for column in index.expressions
                        ]
                    )
                    for index in table.indexes
                ]
            )

        return text


class DatabaseBuild(DatabaseBuildSuper['rdb.Database']):
    """
    Database build type.
    """


    def create_orm_table(
        self,
        *models: Type[DatabaseORMModel] | DatabaseORMModel,
        skip: bool = False
    ) -> None:
        """
        Create tables by ORM model.

        Parameters
        ----------
        models : ORM model instances.
        skip : Whether skip existing table.
        """

        # Create.
        self.db.orm.create(*models, skip=skip)


    def drop_orm_table(
        self,
        *models: Type[DatabaseORMModel] | DatabaseORMModel,
        skip: bool = False
    ) -> None:
        """
        Delete tables by model.

        Parameters
        ----------
        models : ORM model instances.
        skip : Skip not exist table.
        """

        # Drop.
        self.db.orm.drop(*models, skip=skip)


    def build(
        self,
        databases: list[dict] | None = None,
        tables: list[dict | Type[DatabaseORMModel] | DatabaseORMModel] | None = None,
        views: list[dict] | None = None,
        views_stats: list[dict] | None = None,
        ask: bool = True,
        skip: bool = False
    ) -> None:
        """
        Build databases or tables.

        Parameters
        ----------
        databases : Database build parameters, equivalent to the parameters of method `self.create_database`.
        tables : Tables build parameters or model, equivalent to the parameters of method `self.create_table` or `self.create_orm_table`.
        views : Views build parameters, equivalent to the parameters of method `self.create_view`.
        views_stats : Views stats build parameters, equivalent to the parameters of method `self.create_view_stats`.
        ask : Whether ask confirm execute.
        skip : Whether skip existing table.
        """

        # Handle parameter.
        databases = databases or []
        tables = tables or []
        views = views or []
        views_stats = views_stats or []
        refresh_schema = False

        # Database.
        for params in databases:
            database = params['name']

            ## Exist.
            if (
                skip
                and self.db.schema.exist(database)
            ):
                continue

            ## SQL.
            sql = self.get_sql_create_database(**params)

            ## Confirm.
            if ask:
                self.input_confirm_build(sql)

            ## Execute.
            self.db.execute(sql)

            ## Report.
            text = f"Database '{database}' build completed."
            print(text)

        # Table.
        for params in tables:

            ## ORM.
            if (
                is_instance(params)
                and isinstance(params, DatabaseORMModel)
                or issubclass(params, DatabaseORMModel)
            ):
                database = self.db.database
                table = params._table().name

                ## Exist.
                if (
                    skip
                    and self.db.schema.exist(self.db.database, table)
                ):
                    continue

                ## Confirm.
                if ask:
                    text = self.get_orm_table_text(params)
                    self.input_confirm_build(text)

                ## Execute.
                self.create_orm_table(params)

            ## Parameter.
            else:
                path: str | tuple[str, str] = params['path']
                if type(path) == str:
                    database, table = self.db.database, path
                else:
                    database, table = path

                ### Exist.
                if (
                    skip
                    and self.db.schema.exist(database, table)
                ):
                    continue

                ### SQL.
                sql = self.get_sql_create_table(**params)

                ### Confirm.
                if ask:
                    self.input_confirm_build(sql)

                ### Execute.
                self.db.execute(sql)
                refresh_schema = True

            ## Report.
            text = f"Table '{table}' of database '{database}' build completed."
            print(text)

        # Refresh schema.
        if refresh_schema:
            self.db.schema()

        # View.
        for params in views:
            path = params['path']
            if type(path) == str:
                database, table = self.db.database, path
            else:
                database, table = path

            ## Exist.
            if (
                skip
                and self.db.schema.exist(database, table)
            ):
                continue

            ## SQL.
            sql = self.get_sql_create_view(**params)

            ## Confirm.
            if ask:
                self.input_confirm_build(sql)

            ## Execute.
            self.db.execute(sql)

            ## Report.
            text = f"View '{table}' of database '{database}' build completed."
            print(text)

        # View stats.
        for params in views_stats:
            path = params['path']
            if type(path) == str:
                database, table = self.db.database, path
            else:
                database, table = path

            ## Exist.
            if (
                skip
                and self.db.schema.exist(database, table)
            ):
                continue

            ## SQL.
            sql = self.get_sql_create_view_stats(**params)

            ## Confirm.
            if ask:
                self.input_confirm_build(sql)

            ## Execute.
            self.db.execute(sql)

            ## Report.
            text = f"View '{table}' of database '{database}' build completed."
            print(text)


    __call__ = build


class DatabaseBuildAsync(DatabaseBuildSuper['rdb.DatabaseAsync']):
    """
    Asynchronous database build type.
    """


    async def create_orm_table(
        self,
        *models: Type[DatabaseORMModel] | DatabaseORMModel,
        skip: bool = False
    ) -> None:
        """
        Asynchronous create tables by ORM model.

        Parameters
        ----------
        models : ORM model instances.
        skip : Whether skip existing table.
        """

        # Create.
        await self.db.orm.create(*models, skip=skip)


    async def drop_orm_table(
        self,
        *models: Type[DatabaseORMModel] | DatabaseORMModel,
        skip: bool = False
    ) -> None:
        """
        Asynchronous delete tables by model.

        Parameters
        ----------
        models : ORM model instances.
        skip : Skip not exist table.
        """

        # Drop.
        await self.db.orm.drop(*models, skip=skip)


    async def build(
        self,
        databases: list[dict] | None = None,
        tables: list[dict] | None = None,
        tables_orm: list[Type[DatabaseORMModel]] | None = None,
        views: list[dict] | None = None,
        views_stats: list[dict] | None = None,
        ask: bool = True,
        skip: bool = False
    ) -> None:
        """
        Asynchronous build databases or tables.

        Parameters
        ----------
        databases : Database build parameters, equivalent to the parameters of method `self.create_database`.
        tables : Tables build parameters, equivalent to the parameters of method `self.create_table`.
        views : Views build parameters, equivalent to the parameters of method `self.create_view`.
        views_stats : Views stats build parameters, equivalent to the parameters of method `self.create_view_stats`.
        ask : Whether ask confirm execute.
        skip : Whether skip existing table.
        """

        # Handle parameter.
        databases = databases or []
        tables = tables or []
        tables_orm = tables_orm or []
        views = views or []
        views_stats = views_stats or []
        refresh_schema = False

        # Database.
        for params in databases:
            database = params['name']

            ## Exist.
            if (
                skip
                and await self.db.schema.exist(database)
            ):
                continue

            ## SQL.
            sql = self.get_sql_create_database(**params)

            ## Confirm.
            if ask:
                self.input_confirm_build(sql)

            ## Execute.
            await self.db.execute(sql)

            ## Report.
            text = f"Database '{database}' build completed."
            print(text)

        # Table.
        for params in tables:

            ## ORM.
            if (
                is_instance(params)
                and isinstance(params, DatabaseORMModel)
                or issubclass(params, DatabaseORMModel)
            ):
                database = self.db.database
                table = params._table().name

                ## Exist.
                if (
                    skip
                    and await self.db.schema.exist(self.db.database, table)
                ):
                    continue

                ## Confirm.
                if ask:
                    text = self.get_orm_table_text(params)
                    self.input_confirm_build(text)

                ## Execute.
                await self.create_orm_table(params)

            ## Parameter.
            else:
                path: str | tuple[str, str] = params['path']
                if type(path) == str:
                    database, table = self.db.database, path
                else:
                    database, table = path

                ### Exist.
                if (
                    skip
                    and await self.db.schema.exist(database, table)
                ):
                    continue

                ### SQL.
                sql = self.get_sql_create_table(**params)

                ### Confirm.
                if ask:
                    self.input_confirm_build(sql)

                ### Execute.
                await self.db.execute(sql)
                refresh_schema = True

            ## Report.
            text = f"Table '{table}' of database '{database}' build completed."
            print(text)

        # Refresh schema.
        if refresh_schema:
            self.db.schema()

        # View.
        for params in views:
            path = params['path']
            if type(path) == str:
                database, table = self.db.database, path
            else:
                database, table = path

            ## Exist.
            if (
                skip
                and await self.db.schema.exist(database, table)
            ):
                continue

            ## SQL.
            sql = self.get_sql_create_view(**params)

            ## Confirm.
            if ask:
                self.input_confirm_build(sql)

            ## Execute.
            await self.db.execute(sql)

            ## Report.
            text = f"View '{table}' of database '{database}' build completed."
            print(text)

        # View stats.
        for params in views_stats:
            path = params['path']
            if type(path) == str:
                database, table = self.db.database, path
            else:
                database, table = path

            ## Exist.
            if (
                skip
                and await self.db.schema.exist(database, table)
            ):
                continue

            ## SQL.
            sql = self.get_sql_create_view_stats(**params)

            ## Confirm.
            if ask:
                self.input_confirm_build(sql)

            ## Execute.
            await self.db.execute(sql)

            ## Report.
            text = f"View '{table}' of database '{database}' build completed."
            print(text)


    __call__ = build
