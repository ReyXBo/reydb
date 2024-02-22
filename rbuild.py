# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-14 23:05:35
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database build methods.
"""


from typing import Any, List, Tuple, Dict, Optional, Union, Literal, NoReturn, overload
from reytool.rstdout import rinput
from reytool.rsystem import throw, get_first_notnull

from .rconnection import RDatabase, RDBConnection


__all__ = (
    "RDBBuild",
)


class RDBBuild(object):
    """
    Rey's `database build` type.
    """


    def __init__(self, rdatabase: Union[RDatabase, RDBConnection]) -> None:
        """
        Build `database build` instance.

        Parameters
        ----------
        rdatabase : RDatabase or RDBConnection instance.
        """

        # Set attribute.
        self.rdatabase = rdatabase


    def create_database(
        self,
        database: str,
        character: str = "utf8mb3",
        collate: str = "utf8mb3_general_ci",
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
        sql = f"CREATE DATABASE `{database}` CHARACTER SET {character} COLLATE {collate}"

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def _get_field_sql(
        self,
        name: str,
        type_: str,
        constraint: str = "DEFAULT NULL",
        comment: Optional[str] = None,
        position: Optional[str] = None,
        old_name: Optional[str] = None
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
        constraint = " " + constraint

        ## Comment.
        if comment is None:
            comment = ""
        else:
            comment = f" COMMENT '{comment}'"

        ## Position.
        if position is None:
            position = ""
        elif position == "first":
            position = " FIRST"
        else:
            position = f" AFTER `{position}`"

        ## Old name.
        if old_name is None:
            old_name = ""
        else:
            old_name = f"`{old_name}` "

        # Generate.
        sql = f"{old_name}`{name}` {type_}{constraint}{comment}{position}"

        return sql


    @overload
    def _get_index_sql(
        self,
        name: str,
        fields: Union[str, List[str]],
        type_: Literal["noraml", "unique", "fulltext", "spatial"] = "noraml",
        comment: Optional[str] = None
    ) -> str: ...

    @overload
    def _get_index_sql(
        self,
        name: str,
        fields: Union[str, List[str]],
        type_: str = "noraml",
        comment: Optional[str] = None
    ) -> NoReturn: ...

    def _get_index_sql(
        self,
        name: str,
        fields: Union[str, List[str]],
        type_: Literal["noraml", "unique", "fulltext", "spatial"] = "noraml",
        comment: Optional[str] = None
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
        if type_ == "noraml":
            type_ = "KEY"
            method = " USING BTREE"
        elif type_ == "unique":
            type_ = "UNIQUE KEY"
            method = " USING BTREE"
        elif type_ == "fulltext":
            type_ = "FULLTEXT KEY"
            method = ""
        elif type_ == "spatial":
            type_ = "SPATIAL KEY"
            method = ""
        else:
            throw(ValueError, type_)
        if comment in (None, ""):
            comment = ""
        else:
            comment = f" COMMENT '{comment}'"

        # Generate.

        ## Fields.
        sql_fields = ", ".join(
            [
                f"`{field}`"
                for field in fields
            ]
        )

        ## Join.
        sql = f"{type_} `{name}` ({sql_fields}){method}{comment}"

        return sql


    def create_table(
        self,
        path: Union[str, Tuple[str, str]],
        fields: Union[Dict, List[Dict]],
        primary: Optional[Union[str, List[str]]] = None,
        indexes: Optional[Union[Dict, List[Dict]]] = None,
        engine: str = "InnoDB",
        increment: int = 1,
        charset: str = "utf8mb3",
        collate: str = "utf8mb3_general_ci",
        comment: Optional[str] = None,
        execute: bool = True
    ) -> str:
        """
        Create table.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        fields : Fields set table.
            - `Key 'name'` : Field name, required.
            - `Key 'type' or 'type_'` : Field type, required.
            - `Key 'constraint'` : Field constraint.
                * `Empty or None` : Use 'DEFAULT NULL'.
                * `str` : Use this value.
            - `Key 'comment'` : Field comment.
                * `Empty or None` : Not comment.
                * `str` : Use this value.

        primary : Primary key fields.
            - `str` : One field.
            - `List[str]` : Multiple fileds.

        indexes : Index set table.
            - `Key 'name'` : Index name, required.
            - `Key 'fields'` : Index fields, required.
                * `str` : One field.
                * `List[str]` : Multiple fileds.
            - `Key 'type' or 'type_'` : Index type.
                * `Literal['noraml']` : Noraml key.
                * `Literal['unique']` : Unique key.
                * `Literal['fulltext']` : Full text key.
                * `Literal['spatial']` : Spatial key.
            - `Key 'comment'` : Field comment.
                * `Empty or None` : Not comment.
                * `str` : Use this value.

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
        if path.__class__ == str:
            database, table, _ = self.rdatabase.extract_path(path)
        else:
            database, table = path
        database = get_first_notnull(database, self.rdatabase.database, default="exception")
        if fields.__class__ == dict:
            fields = [fields]
        if primary.__class__ == str:
            primary = [primary]
        if primary in ([], [""]):
            primary = None
        if indexes.__class__ == dict:
            indexes = [indexes]

        ## Compatible dictionary key name.
        fields = [
            {
                (
                    "type_"
                    if key == "type"
                    else key
                ): value
                for key, value in row.items()
            }
            for row in fields
        ]
        if indexes is not None:
            indexes = [
                {
                    (
                        "type_"
                        if key == "type"
                        else key
                    ): value
                    for key, value in row.items()
                }
                for row in indexes
            ]

        # Generate.

        ## Fields.
        sql_fields = [
            self._get_field_sql(**field)
            for field in fields
        ]

        ## Primary.
        if primary is not None:
            keys = ", ".join(
                [
                    f"`{key}`"
                    for key in primary
                ]
            )
            sql_primary = f"PRIMARY KEY ({keys}) USING BTREE"
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
            sql_comment = ""
        else:
            sql_comment = f" COMMENT='{comment}'"

        ## Join.
        sql_fields = ",\n    ".join(sql_fields)
        sql = (
            f"CREATE TABLE `{database}`.`{table}`(\n"
            f"    {sql_fields}\n"
            f") ENGINE={engine} AUTO_INCREMENT={increment} CHARSET={charset} COLLATE={collate}{sql_comment}"
        )

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def create_view(
        self,
        path: Union[str, Tuple[str, str]],
        select: str,
        execute: bool = True
    ) -> str:
        """
        Create view.

        Parameters
        ----------
        path : View name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str` : Automatic extract database name and view name.
            - `Tuple[str, str]` : Database name and view name.

        select : View select SQL.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        if path.__class__ == str:
            database, view, _ = self.rdatabase.extract_path(path)
        else:
            database, view = path
        database = get_first_notnull(database, self.rdatabase.database, default="exception")

        # Generate SQL.
        select = select.replace("\n", "\n    ")
        sql = "CREATE VIEW `%s`.`%s` AS (\n    %s\n)" % (database, view, select)

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def create_view_stats(
        self,
        path: Union[str, Tuple[str, str]],
        items: List[Dict],
        execute: bool = True
    ) -> str:
        """
        Create stats view.

        Parameters
        ----------
        path : View name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str` : Automatic extract database name and view name.
            - `Tuple[str, str]` : Database name and view name.

        items : Items set table.
            - `Key 'name'` : Item name, required.
            - `Key 'select'` : Item select SQL, must only return one value, required.
            - `Key 'comment' : Item comment.

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
        select_first = "SELECT '%s' AS `Item`,\n(\n    %s\n) AS `Value`,\n%s AS `Comment`" % (
            item_first["name"],
            item_first["select"].replace("\n", "\n    "),
            (
                "NULL"
                if "comment" not in item_first
                else '"%s"' % item_first["comment"]
            )
        )
        selects = [
            "SELECT '%s',\n(\n    %s\n),\n%s" % (
                item["name"],
                item["select"].replace("\n", "\n    "),
                (
                    "NULL"
                    if "comment" not in item
                    else "'%s'" % item["comment"]
                )
            )
            for item in items[1:]
        ]
        selects[0:0] = [select_first]
        select = "\nUNION\n".join(selects)

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
        sql = f"DROP DATABASE `{database}`"

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def drop_table(
        self,
        path: Union[str, Tuple[str, str]],
        execute: bool = True
    ) -> str:
        """
        Drop table.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, _ = self.rdatabase.extract_path(path)
        else:
            database, table = path
        database = get_first_notnull(database, self.rdatabase.database, default="exception")

        # Generate.
        sql = f"DROP TABLE `{database}`.`{table}`"

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def drop_view(
        self,
        path: Union[str, Tuple[str, str]],
        execute: bool = True
    ) -> str:
        """
        Drop view.

        Parameters
        ----------
        path : View name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str` : Automatic extract database name and view name.
            - `Tuple[str, str]` : Database name and view name.

        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        if path.__class__ == str:
            database, view, _ = self.rdatabase.extract_path(path)
        else:
            database, view = path
        database = get_first_notnull(database, self.rdatabase.database, default="exception")

        # Generate SQL.
        sql = "DROP VIEW `%s`.`%s`" % (database, view)

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def alter_database(
        self,
        database: str,
        character: Optional[str] = None,
        collate: Optional[str] = None,
        execute: bool = True
    ) -> str:
        """
        Alter database.

        Parameters
        ----------
        database : Database name.
        character : Character set.
            - `None` : Not alter.
            - `str` : Alter to this value.

        collate : Collate rule.
            - `None` : Not alter.
            - `str` : Alter to this value.

        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Generate.

        ## Character.
        if character is None:
            sql_character = ""
        else:
            sql_character = f" CHARACTER SET {character}"

        ## Collate.
        if collate is None:
            sql_collate = ""
        else:
            sql_collate = f" COLLATE {collate}"

        ## Join.
        sql = f"ALTER DATABASE `{database}`{sql_character}{sql_collate}"

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def alter_table_add(
        self,
        path: Union[str, Tuple[str, str]],
        fields: Optional[Union[Dict, List[Dict]]] = None,
        primary: Optional[Union[str, List[str]]] = None,
        indexes: Optional[Union[Dict, List[Dict]]] = None,
        execute: bool = True
    ) -> str:
        """
        Alter table add filed.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        fields : Fields set table.
            - `Key 'name'` : Field name, required.
            - `Key 'type' or 'type_'` : Field type, required.
            - `Key 'constraint'` : Field constraint.
                * `Empty or None` : Use 'DEFAULT NULL'.
                * `str` : Use this value.
            - `Key 'comment'` : Field comment.
                * `Empty or None` : Not comment.
                * `str` : Use this value.
            - `Key 'position'` : Field position.
                * `None` : Last.
                * `Literal['first']` : First.
                * `str` : After this field.

        primary : Primary key fields.
            - `str` : One field.
            - `List[str]` : Multiple fileds.

        indexes : Index set table.
            - `Key 'name'` : Index name, required.
            - `Key 'fields'` : Index fields, required.
                * `str` : One field.
                * `List[str]` : Multiple fileds.
            - `Key 'type' or 'type_'` : Index type.
                * `Literal['noraml']` : Noraml key.
                * `Literal['unique']` : Unique key.
                * `Literal['fulltext']` : Full text key.
                * `Literal['spatial']` : Spatial key.
            - `Key 'comment'` : Field comment.
                * `Empty or None` : Not comment.
                * `str` : Use this value.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, _ = self.rdatabase.extract_path(path)
        else:
            database, table = path
        database = get_first_notnull(database, self.rdatabase.database, default="exception")
        if fields.__class__ == dict:
            fields = [fields]
        if primary.__class__ == str:
            primary = [primary]
        if primary in ([], [""]):
            primary = None
        if indexes.__class__ == dict:
            indexes = [indexes]

        ## Compatible dictionary key name.
        fields = [
            {
                (
                    "type_"
                    if key == "type"
                    else key
                ): value
                for key, value in row.items()
            }
            for row in fields
        ]
        if indexes is not None:
            indexes = [
                {
                    (
                        "type_"
                        if key == "type"
                        else key
                    ): value
                    for key, value in row.items()
                }
                for row in indexes
            ]

        # Generate.
        sql_content = []

        ## Fields.
        if fields is not None:
            sql_fields = [
                "COLUMN " + self._get_field_sql(**field)
                for field in fields
            ]
            sql_content.extend(sql_fields)

        ## Primary.
        if primary is not None:
            keys = ", ".join(
                [
                    f"`{key}`"
                    for key in primary
                ]
            )
            sql_primary = f"PRIMARY KEY ({keys}) USING BTREE"
            sql_content.append(sql_primary)

        ## Indexes.
        if indexes is not None:
            sql_indexes = [
                self._get_index_sql(**index)
                for index in indexes
            ]
            sql_content.extend(sql_indexes)

        ## Join.
        sql_content = ",\n    ADD ".join(sql_content)
        sql = (
            f"ALTER TABLE `{database}`.`{table}`\n"
            f"    ADD {sql_content}"
        )

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def alter_table_drop(
        self,
        path: Union[str, Tuple[str, str]],
        fields: Optional[List[str]] = None,
        primary: bool = False,
        indexes: Optional[List[str]] = None,
        execute: bool = True
    ) -> str:
        """
        Alter table drop field.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        fields : Delete fields name.
        primary : Whether delete primary key.
        indexes : Delete indexes name.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, _ = self.rdatabase.extract_path(path)
        else:
            database, table = path
        database = get_first_notnull(database, self.rdatabase.database, default="exception")

        # Generate.
        sql_content = []

        ## Fields.
        if fields is not None:
            sql_fields = [
                "COLUMN " + field
                for field in fields
            ]
            sql_content.extend(sql_fields)

        ## Primary.
        if primary:
            sql_primary = "PRIMARY KEY"
            sql_content.append(sql_primary)

        ## Indexes.
        if indexes is not None:
            sql_indexes = [
                "INDEX " + index
                for index in indexes
            ]
            sql_content.extend(sql_indexes)

        ## Join.
        sql_content = ",\n    DROP ".join(sql_content)
        sql = (
            f"ALTER TABLE `{database}`.`{table}`\n"
            f"    DROP {sql_content}"
        )

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def alter_table_change(
        self,
        path: Union[str, Tuple[str, str]],
        fields: Optional[Union[Dict, List[Dict]]] = None,
        rename: Optional[str] = None,
        engine: Optional[str] = None,
        increment: Optional[int] = None,
        charset: Optional[str] = None,
        collate: Optional[str] = None,
        execute: bool = True
    ) -> str:
        """
        Alter database.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        fields : Fields set table.
            - `Key 'name'` : Field name, required.
            - `Key 'type' or 'type_'` : Field type, required.
            - `Key 'constraint'` : Field constraint.
                * `Empty or None` : Use 'DEFAULT NULL'.
                * `str` : Use this value.
            - `Key 'comment'` : Field comment.
                * `Empty or None` : Not comment.
                * `str` : Use this value.
            - `Key 'position'` : Field position.
                * `None` : Last.
                * `Literal['first']` : First.
                * `str` : After this field.
            - `Key 'old_name'` : Field old name.

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
        if path.__class__ == str:
            database, table, _ = self.rdatabase.extract_path(path)
        else:
            database, table = path
        database = get_first_notnull(database, self.rdatabase.database, default="exception")
        if fields.__class__ == dict:
            fields = [fields]

        ## Compatible dictionary key name.
        fields = [
            {
                (
                    "type_"
                    if key == "type"
                    else key
                ): value
                for key, value in row.items()
            }
            for row in fields
        ]

        # Generate.
        sql_content = []

        ## Rename.
        if rename is not None:
            sql_rename = f"RENAME `{database}`.`{rename}`"
            sql_content.append(sql_rename)

        ## Fields.
        if fields is not None:
            sql_fields = [
                "%s %s" % (
                    (
                        "MODIFY"
                        if "old_name" not in field
                        else "CHANGE"
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
            sql_engine = f"ENGINE={engine}"
            sql_attr.append(sql_engine)

        ### Increment.
        if increment is not None:
            sql_increment = f"AUTO_INCREMENT={increment}"
            sql_attr.append(sql_increment)

        ### Charset.
        if charset is not None:
            sql_charset = f"CHARSET={charset}"
            sql_attr.append(sql_charset)

        ### Collate.
        if collate is not None:
            sql_collate = f"COLLATE={collate}"
            sql_attr.append(sql_collate)

        if sql_attr != []:
            sql_attr = " ".join(sql_attr)
            sql_content.append(sql_attr)

        ## Join.
        sql_content = ",\n    ".join(sql_content)
        sql = (
            f"ALTER TABLE `{database}`.`{table}`\n"
            f"    {sql_content}"
        )

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def alter_view(
        self,
        path: Union[str, Tuple[str, str]],
        select: str,
        execute: bool = True
    ) -> str:
        """
        Alter view.

        Parameters
        ----------
        path : View name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str` : Automatic extract database name and view name.
            - `Tuple[str, str]` : Database name and view name.

        select : View select SQL.
        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        if path.__class__ == str:
            database, view, _ = self.rdatabase.extract_path(path)
        else:
            database, view = path
        database = get_first_notnull(database, self.rdatabase.database, default="exception")

        # Generate SQL.
        sql = "ALTER VIEW `%s`.`%s` AS\n%s" % (database, view, select)

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def truncate_table(
        self,
        path: Union[str, Tuple[str, str]],
        execute: bool = True
    ) -> str:
        """
        Truncate table.

        Parameters
        ----------
        path : Table name, can contain database name, otherwise use `self.rdatabase.database`.
            - `str` : Automatic extract database name and table name.
            - `Tuple[str, str]` : Database name and table name.

        execute : Whether directly execute.

        Returns
        -------
        Execute SQL.
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, _ = self.rdatabase.extract_path(path)
        else:
            database, table = path
        database = get_first_notnull(database, self.rdatabase.database, default="exception")

        # Generate.
        sql = f"TRUNCATE TABLE `{database}`.`{table}`"

        # Execute.
        if execute:
            self.rdatabase(sql)

        return sql


    def exist(
        self,
        path: Union[str, Tuple[str, Optional[str], Optional[str]]]
    ) -> bool:
        """
        Judge database or table or column exists.

        Parameters
        ----------
        path : Database name and table name and column name.
            - `str` : Automatic extract.
            - `Tuple[str, Optional[str], Optional[str]]` : Database name, table name and column name is optional.

        Returns
        -------
        Judge result.
        """

        # Handle parameter.
        if path.__class__ == str:
            database, table, column = self.rdatabase.extract_path(path, "database")
        else:
            database, table, column = path

        # Judge.
        if table is None:
            rinfo = self.rdatabase.info(database)
        elif column is None:
            rinfo = self.rdatabase.info(database)(table)
        else:
            rinfo = self.rdatabase.info(database)(table)(column)
        try:
            rinfo["*"]
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
        text = "Do you want to execute SQL to build the database? Otherwise stop program. (y/n) "
        command = rinput(
            sql,
            text,
            frame="top",
            title="SQL"
        )

        # Check.
        while True:
            command = command.lower()

            ## Confirm.
            if command == "y":
                break

            ## Stop.
            elif command == "n":
                raise AssertionError("program stop")

            ## Reenter.
            else:
                text = "Incorrect input, reenter. (y/n) "
                command = input(text)


    def build(
        self,
        databases: Optional[List[Dict]] = None,
        tables: Optional[List[Dict]] = None,
        views: Optional[List[Dict]] = None,
        views_stats: Optional[List[Dict]] = None
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
            database = params["database"]

            # Exist.
            exist = self.rdatabase.build.exist((database, None, None))
            if exist: continue

            # Create.
            sql = self.create_database(**params, execute=False)

            # Confirm.
            self.input_confirm_build(sql)

            # Execute.
            self.rdatabase(sql)

            # Report.
            text = f"Database '{database}' build completed."
            print(text)

        # Table.
        for params in tables:
            path = params["path"]
            if path.__class__ == str:
                database, table, _ = self.rdatabase.extract_path(path)
            else:
                database, table = path

            # Exist.
            exist = self.rdatabase.build.exist((database, table, None))
            if exist: continue

            # Create.
            sql = self.create_table(**params, execute=False)

            # Confirm.
            self.input_confirm_build(sql)

            # Execute.
            self.rdatabase(sql)

            # Report.
            text = f"Table '{table}' of database '{database}' build completed."
            print(text)

        # View.
        for params in views:
            path = params["path"]
            if path.__class__ == str:
                database, view, _ = self.rdatabase.extract_path(path)
            else:
                database, view = path

            # Exist.
            exist = self.rdatabase.build.exist((database, view, None))
            if exist: continue

            # Create.
            sql = self.create_view(**params, execute=False)

            # Confirm.
            self.input_confirm_build(sql)

            # Execute.
            self.rdatabase(sql)

            # Report.
            text = f"View '{view}' of database '{database}' build completed."
            print(text)

        # View stats.
        for params in views_stats:
            path = params["path"]
            if path.__class__ == str:
                database, view, _ = self.rdatabase.extract_path(path)
            else:
                database, view = path

            # Exist.
            exist = self.rdatabase.build.exist((database, view, None))
            if exist: continue

            # Create.
            sql = self.create_view_stats(**params, execute=False)

            # Confirm.
            self.input_confirm_build(sql)

            # Execute.
            self.rdatabase(sql)

            # Report.
            text = f"View '{view}' of database '{database}' build completed."
            print(text)


    __call__ = build