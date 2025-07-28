# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-14 23:05:35
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database build methods.
"""


from typing import TypedDict, NotRequired, Literal
from copy import deepcopy
from reykit.rbase import throw
from reykit.rstdout import ask

from .rbase import BaseDatabase
from .rconn import Database, DBConnection


__all__ = (
    'DBBuild',
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
IndexType = Literal['noraml', 'unique', 'fulltext', 'spatial']
IndexSet = TypedDict(
    'IndexSet',
    {
        'name': str,
        'fields' : str | list[str],
        'type': IndexType,
        'comment': NotRequired[str | None]
    }
)


class DBBuild(BaseDatabase):
    """
    Database build type.
    """


    def __init__(self, rdatabase: Database | DBConnection) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        rdatabase : Database or DBConnection instance.
        """

        # SQLite.
        if rdatabase.backend == 'sqlite':
            text='not suitable for SQLite databases'
            throw(AssertionError, text=text)

        # Set attribute.
        self.rdatabase = rdatabase


    def create_database(
        self,
        database: str,
        character: str = 'utf8mb3',
        collate: str = 'utf8mb3_general_ci',
        execute: bool = True
    ) -> str:
        """
        Create database.

        Parameters
        ----------
        database : Database name.
        character : Character set.
        collate : Collate rule.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Generate.
        sql = f'CREATE DATABASE `{database}` CHARACTER SET {character} COLLATE {collate}'

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def _get_field_sql(
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

        # Get parameter.

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


    def _get_index_sql(
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
        type_ : Index type.
        comment : Index comment.

        Returns
        -------
        Index set SQL.
        """

        # Get parameter.
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


    def create_table(
        self,
        path: str | tuple[str, str],
        fields: FieldSet | list[FieldSet],
        primary: str | list[str] | None = None,
        indexes: IndexSet | list[IndexSet] | None = None,
        engine: str = 'InnoDB',
        increment: int = 1,
        charset: str = 'utf8mb3',
        collate: str = 'utf8mb3_general_ci',
        comment: str | None = None,
        execute: bool = True
    ) -> str:
        """
        Create table.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str`: Automatic extract database name and table name.
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
        Execute SQL.
        """

        # Handle parameter.
        database, table, _ = self.rdatabase.extract_path(path)
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
            self._get_field_sql(**field)
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
                self._get_index_sql(**index)
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

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def create_view(
        self,
        path: str | tuple[str, str],
        select: str,
        execute: bool = True
    ) -> str:
        """
        Create view.

        Parameters
        ----------
        path : View name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str`: Automatic extract database name and view name.
            - `tuple[str, str]`: Database name and view name.
        select : View select SQL.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        database, view, _ = self.rdatabase.extract_path(path)

        # Generate SQL.
        select = select.replace('\n', '\n    ')
        sql = 'CREATE VIEW `%s`.`%s` AS (\n    %s\n)' % (database, view, select)

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def create_view_stats(
        self,
        path: str | tuple[str, str],
        items: list[dict],
        execute: bool = True
    ) -> str:
        """
        Create stats view.

        Parameters
        ----------
        path : View name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str`: Automatic extract database name and view name.
            - `tuple[str, str]`: Database name and view name.
        items : Items set table.
            - `Key 'name'`: Item name, required.
            - `Key 'select'`: Item select SQL, must only return one value, required.
            - `Key 'comment'`: Item comment.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
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
        sql = self.create_view(
            path,
            select,
            execute
        )

        return sql


    def drop_database(
        self,
        database: str,
        execute: bool = True
    ) -> str:
        """
        Drop database.

        Parameters
        ----------
        database : Database name.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Generate.
        sql = f'DROP DATABASE `{database}`'

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def drop_table(
        self,
        path: str | tuple[str, str],
        execute: bool = True
    ) -> str:
        """
        Drop table.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str`: Automatic extract database name and table name.
            - `tuple[str, str]`: Database name and table name.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        database, table, _ = self.rdatabase.extract_path(path)

        # Generate.
        sql = f'DROP TABLE `{database}`.`{table}`'

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def drop_view(
        self,
        path: str | tuple[str, str],
        execute: bool = True
    ) -> str:
        """
        Drop view.

        Parameters
        ----------
        path : View name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str`: Automatic extract database name and view name.
            - `tuple[str, str]`: Database name and view name.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        database, view, _ = self.rdatabase.extract_path(path)

        # Generate SQL.
        sql = 'DROP VIEW `%s`.`%s`' % (database, view)

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def alter_database(
        self,
        database: str,
        character: str | None = None,
        collate: str | None = None,
        execute: bool = True
    ) -> str:
        """
        Alter database.

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
        Execute SQL.
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

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def alter_table_add(
        self,
        path: str | tuple[str, str],
        fields: FieldSet | list[FieldSet] | None = None,
        primary: str | list[str] | None = None,
        indexes: IndexSet | list[IndexSet] | None = None,
        execute: bool = True
    ) -> str:
        """
        Alter table add filed.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str`: Automatic extract database name and table name.
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
        Execute SQL.
        """

        # Handle parameter.
        database, table, _ = self.rdatabase.extract_path(path)
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
                'COLUMN ' + self._get_field_sql(**field)
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
                self._get_index_sql(**index)
                for index in indexes
            ]
            sql_content.extend(sql_indexes)

        ## Join.
        sql_content = ',\n    ADD '.join(sql_content)
        sql = (
            f'ALTER TABLE `{database}`.`{table}`\n'
            f'    ADD {sql_content}'
        )

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def alter_table_drop(
        self,
        path: str | tuple[str, str],
        fields: str | list[str] | None = None,
        primary: bool = False,
        indexes: str | list[str] | None = None,
        execute: bool = True
    ) -> str:
        """
        Alter table drop field.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str`: Automatic extract database name and table name.
            - `tuple[str, str]`: Database name and table name.
        fields : Delete fields name.
        primary : Whether delete primary key.
        indexes : Delete indexes name.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        database, table, _ = self.rdatabase.extract_path(path)
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

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def alter_table_change(
        self,
        path: str | tuple[str, str],
        fields: FieldSet | list[FieldSet] | None = None,
        rename: str | None = None,
        engine: str | None = None,
        increment: int | None = None,
        charset: str | None = None,
        collate: str | None = None,
        execute: bool = True
    ) -> str:
        """
        Alter database.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str`: Automatic extract database name and table name.
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
        Execute SQL.
        """

        # Handle parameter.
        database, table, _ = self.rdatabase.extract_path(path)
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
                    self._get_field_sql(**field)
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

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def alter_view(
        self,
        path: str | tuple[str, str],
        select: str,
        execute: bool = True
    ) -> str:
        """
        Alter view.

        Parameters
        ----------
        path : View name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str`: Automatic extract database name and view name.
            - `tuple[str, str]`: Database name and view name.
        select : View select SQL.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        database, view, _ = self.rdatabase.extract_path(path)

        # Generate SQL.
        sql = 'ALTER VIEW `%s`.`%s` AS\n%s' % (database, view, select)

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def truncate_table(
        self,
        path: str | tuple[str, str],
        execute: bool = True
    ) -> str:
        """
        Truncate table.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str`: Automatic extract database name and table name.
            - `tuple[str, str]`: Database name and table name.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        database, table, _ = self.rdatabase.extract_path(path)

        # Generate.
        sql = f'TRUNCATE TABLE `{database}`.`{table}`'

        # Execute.
        if execute:
            self.rdatabase.execute(sql)

        return sql


    def exist(
        self,
        path: str | tuple[str, str | None, str | None]
    ) -> bool:
        """
        Judge database or table or column exists.

        Parameters
        ----------
        path : Database name and table name and column name.
            - `str`: Automatic extract.
            - `tuple[str, str | None, str | None]`: Database name, table name and column name is optional.

        Returns
        -------
        Judge result.
        """

        # Handle parameter.
        database, table, column = self.rdatabase.extract_path(path, 'database')

        # Judge.
        if table is None:
            rinfo = self.rdatabase.info(database)
        elif column is None:
            rinfo = self.rdatabase.info(database)(table)
        else:
            rinfo = self.rdatabase.info(database)(table)(column)
        try:
            rinfo['*']
        except AssertionError:
            judge = False
        else:
            judge = True

        return judge


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


    def build(
        self,
        databases: list[dict] | None = None,
        tables: list[dict] | None = None,
        views: list[dict] | None = None,
        views_stats: list[dict] | None = None
    ) -> None:
        """
        Build databases or tables.

        Parameters
        ----------
        databases : Database build parameters, equivalent to the parameters of method `self.create_database`.
        tables : Tables build parameters, equivalent to the parameters of method `self.create_table`.
        views : Views build parameters, equivalent to the parameters of method `self.create_view`.
        views_stats : Views stats build parameters, equivalent to the parameters of method `self.create_view_stats`.
        """

        # Handle parameter.
        if databases is None:
            databases = []
        if tables is None:
            tables = []
        if views is None:
            views = []
        if views_stats is None:
            views_stats = []

        # Database.
        for params in databases:
            database = params['database']

            ## Exist.
            exist = self.rdatabase.build.exist((database, None, None))
            if exist:
                continue

            ## Create.
            sql = self.create_database(**params, execute=False)

            ## Confirm.
            self.input_confirm_build(sql)

            ## Execute.
            self.rdatabase.execute(sql)

            ## Report.
            text = f"Database '{database}' build completed."
            print(text)

        # Table.
        for params in tables:
            path = params['path']
            database, table, _ = self.rdatabase.extract_path(path)

            ## Exist.
            exist = self.rdatabase.build.exist((database, table, None))
            if exist:
                continue

            ## Create.
            sql = self.create_table(**params, execute=False)

            ## Confirm.
            self.input_confirm_build(sql)

            ## Execute.
            self.rdatabase.execute(sql)

            ## Report.
            text = f"Table '{table}' of database '{database}' build completed."
            print(text)

        # View.
        for params in views:
            path = params['path']
            database, view, _ = self.rdatabase.extract_path(path)

            ## Exist.
            exist = self.rdatabase.build.exist((database, view, None))
            if exist:
                continue

            ## Create.
            sql = self.create_view(**params, execute=False)

            ## Confirm.
            self.input_confirm_build(sql)

            ## Execute.
            self.rdatabase.execute(sql)

            ## Report.
            text = f"View '{view}' of database '{database}' build completed."
            print(text)

        # View stats.
        for params in views_stats:
            path = params['path']
            database, view, _ = self.rdatabase.extract_path(path)

            ## Exist.
            exist = self.rdatabase.build.exist((database, view, None))
            if exist:
                continue

            ## Create.
            sql = self.create_view_stats(**params, execute=False)

            ## Confirm.
            self.input_confirm_build(sql)

            ## Execute.
            self.rdatabase.execute(sql)

            ## Report.
            text = f"View '{view}' of database '{database}' build completed."
            print(text)


    __call__ = build
