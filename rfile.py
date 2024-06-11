# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-29 20:01:25
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database file methods.
"""


from typing import Any, Dict, Literal, Union, Optional
from os.path import join as os_join
from reytool.ros import RFile, RFolder, get_md5

from .rconnection import RDatabase, RDBConnection


__all__ = (
    "RDBFile",
)


class RDBFile(object):
    """
    Rey's `database file` type.
    """


    def __init__(
        self,
        rdatabase: Union[RDatabase, RDBConnection]
    ) -> None:
        """
        Build `database file` instance.

        Parameters
        ----------
        rdatabase : RDatabase or RDBConnection instance.
        """

        # Set attribute.
        self.rdatabase = rdatabase


    def build(self) -> None:
        """
        Check and build all standard databases and tables.
        """

        # Set parameter.

        ## Database.
        databases = [
            {
                "database": "file"
            }
        ]

        ## Table.
        tables = [

            ### "information".
            {
                "path": ("file", "information"),
                "fields": [
                    {
                        "name": "create_time",
                        "type": "datetime",
                        "constraint": "NOT NULL DEFAULT CURRENT_TIMESTAMP",
                        "comment": "Record create time."
                    },
                    {
                        "name": "file_id",
                        "type": "mediumint unsigned",
                        "constraint": "NOT NULL AUTO_INCREMENT",
                        "comment": "File self increase ID."
                    },
                    {
                        "name": "md5",
                        "type": "char(32)",
                        "constraint": "NOT NULL",
                        "comment": "File MD5."
                    },
                    {
                        "name": "name",
                        "type": "varchar(260)",
                        "constraint": "DEFAULT NULL",
                        "comment": "File name."
                    },
                    {
                        "name": "note",
                        "type": "varchar(500)",
                        "constraint": "DEFAULT NULL",
                        "comment": "File note."
                    }
                ],
                "primary": "file_id",
                "indexes": [
                    {
                        "name": "n_md5",
                        "fields": "md5",
                        "type": "noraml",
                        "comment": "File MD5 normal index."
                    },
                    {
                        "name": "n_name",
                        "fields": "name",
                        "type": "noraml",
                        "comment": "File name normal index."
                    }
                ],
                "comment": "File information table."
            },

            ### "data".
            {
                "path": ("file", "data"),
                "fields": [
                    {
                        "name": "md5",
                        "type": "char(32)",
                        "constraint": "NOT NULL",
                        "comment": "File MD5."
                    },
                    {
                        "name": "size",
                        "type": "int unsigned",
                        "constraint": "NOT NULL",
                        "comment": "File byte size."
                    },
                    {
                        "name": "bytes",
                        "type": "longblob",
                        "constraint": "NOT NULL",
                        "comment": "File bytes."
                    }
                ],
                "primary": "md5",
                "comment": "File data table."
            }
        ]

        ## View stats.
        views_stats = [

            ### "stats".
            {
                "path": ("file", "stats"),
                "items": [
                    {
                        "name": "count",
                        "select": (
                            "SELECT COUNT(1)\n"
                            "FROM `file`.`information`"
                        ),
                        "comment": "File information count."
                    },
                    {
                        "name": "count_data",
                        "select": (
                            "SELECT COUNT(1)\n"
                            "FROM `file`.`data`"
                        ),
                        "comment": "File data unique count."
                    },
                    {
                        "name": "size_avg",
                        "select": (
                            "SELECT CONCAT(\n"
                            "    ROUND(AVG(`size`) / 1024),\n"
                            "    ' KB'\n"
                            ")\n"
                            "FROM `file`.`data`\n"
                        ),
                        "comment": "File average size."
                    },
                    {
                        "name": "size_max",
                        "select": (
                            "SELECT CONCAT(\n"
                            "    ROUND(MAX(`size`) / 1024),\n"
                            "    ' KB'\n"
                            ")\n"
                            "FROM `file`.`data`\n"
                        ),
                        "comment": "File maximum size."
                    },
                    {
                        "name": "last_time",
                        "select": (
                            "SELECT MAX(`create_time`)\n"
                            "FROM `file`.`information`"
                        ),
                        "comment": "File last record create time."
                    }
                ]
            }
        ]

        # Build.
        self.rdatabase.build.build(databases, tables, views_stats=views_stats)


    def upload(
        self,
        file: Union[str, bytes],
        name: Optional[str] = None,
        note: Optional[str] = None
    ) -> int:
        """
        Upload file.

        Parameters
        ----------
        file : File path or file bytes.
        name : File name.
            - `None` : Automatic set.
                * `parameter 'file' is 'str'` : Use path file name.
                * `parameter 'file' is 'bytes'` : No name.
            - `str` : Use this name.

        note : File note.

        Returns
        -------
        File ID.
        """

        # Get parameter.
        conn = self.rdatabase.connect()

        ## File path.
        if file.__class__ == str:
            rfile = RFile(file)
            file_bytes = rfile.bytes
            file_md5 = get_md5(file_bytes)
            file_name = rfile.name_suffix

        ## File bytes.
        elif file.__class__ == bytes:
            file_bytes = file
            file_md5 = get_md5(file_bytes)
            file_name = None

        ## File name.
        if name is not None:
            file_name = name

        ## File size.
        file_size = len(file_bytes)

        # Exist.
        exist = conn.execute_exist(
            ("file", "data"),
            "`md5` = :file_md5",
            file_md5=file_md5
        )

        # Upload.

        ## Data.
        if not exist:
            data = {
                "md5": file_md5,
                "size": file_size,
                "bytes": file_bytes
            }
            conn.execute_insert(
                ("file", "data"),
                data,
                "ignore"
            )

        ## Information.
        data = {
            "md5": file_md5,
            "name": file_name,
            "note": note
        }
        conn.execute_insert(
            ("file", "information"),
            data
        )

        # Get ID.
        file_id = conn.variables["identity"]

        # Commit.
        conn.commit()

        return file_id


    def download(
        self,
        file_id: int,
        path: Optional[str] = None
    ) -> bytes:
        """
        Download file.

        Parameters
        ----------
        file_id : File ID.
        path : File save path.
            - `None` : Not save.
            - `str` : Save.
                * `File path` : Use this file path.
                * `Folder path` : Use this folder path and original name.

        Returns
        -------
        File bytes.
        """

        # Generate SQL.
        sql = (
            "SELECT `name`, (\n"
            "    SELECT `bytes`\n"
            "    FROM `file`.`data`\n"
            "    WHERE `md5` = `information`.`md5`\n"
            "    LIMIT 1\n"
            ") AS `bytes`\n"
            "FROM `file`.`information`\n"
            "WHERE `file_id` = :file_id\n"
            "LIMIT 1"
        )

        # Execute SQL.
        result = self.rdatabase(sql, file_id=file_id)

        # Check.
        if result.empty:
            text = "file ID '%s' not exist or no data" % file_id
            raise ValueError(text)
        file_name, file_bytes = result.first()

        # Save.
        if path is not None:
            rfolder = RFolder(path)
            if rfolder:
                path = os_join(path, file_name)
            rfile = RFile(path)
            rfile(file_bytes)

        return file_bytes


    def query(
        self,
        file_id: int
    ) -> Dict[
        Literal[
            "create_time",
            "md5",
            "name",
            "size",
            "note"
        ],
        Any
    ]:
        """
        Query file information.

        Parameters
        ----------
        file_id : File ID.

        Returns
        -------
        File information.
        """

        # Generate SQL.
        sql = (
            "SELECT `create_time`, `md5`, `name`, `note`, (\n"
            "    SELECT `size`\n"
            "    FROM `file`.`data`\n"
            "    WHERE `md5` = `a`.`md5`\n"
            "    LIMIT 1\n"
            ") AS `size`\n"
            "FROM `file`.`information` AS `a`\n"
            "WHERE `file_id` = :file_id\n"
            "LIMIT 1"
        )

        # Execute SQL.
        result = self.rdatabase.execute(sql, file_id=file_id)

        # Check.
        if result.empty:
            raise AssertionError("file ID does not exist")

        # Convert.
        table = result.fetch_table()
        info = table[0]

        return info


    __call__ = build