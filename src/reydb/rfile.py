# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2023-10-29 20:01:25
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database file methods.
"""


from typing import TypedDict, overload
from datetime import datetime
from reykit.rbase import throw
from reykit.ros import File, Folder, get_md5

from .rbase import DatabaseBase
from .rconn import DatabaseConnection
from .rdb import Database


__all__ = (
    'DatabaseFile',
)


FileInfo = TypedDict('FileInfo', {'create_time': datetime, 'md5': str, 'name': str | None, 'size': int, 'note': str | None})


class DatabaseFile(DatabaseBase):
    """
    Database file type.
    Can create database used `self.build_db` method.
    """


    def __init__(self, database: Database | DatabaseConnection) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        database : Database or DatabaseConnection instance.
        """

        # Check.
        if database.backend == 'sqlite':
            text = 'not suitable for SQLite databases'
            throw(AssertionError, text=text)

        # Build.
        self.database = database

        ## Database path name.
        self.db_names = {
            'file': 'file',
            'file.information': 'information',
            'file.data': 'data',
            'file.stats': 'stats',
            'file.data_information': 'data_information'
        }


    def build_db(self) -> None:
        """
        Check and build all standard databases and tables, by `self.db_names`.
        """

        # Set parameter.

        ## Database.
        databases = [
            {
                'name': self.db_names['file']
            }
        ]

        ## Table.
        tables = [

            ### 'information'.
            {
                'path': (self.db_names['file'], self.db_names['file.information']),
                'fields': [
                    {
                        'name': 'create_time',
                        'type': 'datetime',
                        'constraint': 'NOT NULL DEFAULT CURRENT_TIMESTAMP',
                        'comment': 'Record create time.'
                    },
                    {
                        'name': 'file_id',
                        'type': 'mediumint unsigned',
                        'constraint': 'NOT NULL AUTO_INCREMENT',
                        'comment': 'File ID.'
                    },
                    {
                        'name': 'md5',
                        'type': 'char(32)',
                        'constraint': 'NOT NULL',
                        'comment': 'File MD5.'
                    },
                    {
                        'name': 'name',
                        'type': 'varchar(260)',
                        'comment': 'File name.'
                    },
                    {
                        'name': 'note',
                        'type': 'varchar(500)',
                        'comment': 'File note.'
                    }
                ],
                'primary': 'file_id',
                'indexes': [
                    {
                        'name': 'n_create_time',
                        'fields': 'create_time',
                        'type': 'noraml',
                        'comment': 'Record create time normal index.'
                    },
                    {
                        'name': 'n_md5',
                        'fields': 'md5',
                        'type': 'noraml',
                        'comment': 'File MD5 normal index.'
                    },
                    {
                        'name': 'n_name',
                        'fields': 'name',
                        'type': 'noraml',
                        'comment': 'File name normal index.'
                    }
                ],
                'comment': 'File information table.'
            },

            ### 'data'.
            {
                'path': (self.db_names['file'], self.db_names['file.data']),
                'fields': [
                    {
                        'name': 'md5',
                        'type': 'char(32)',
                        'constraint': 'NOT NULL',
                        'comment': 'File MD5.'
                    },
                    {
                        'name': 'size',
                        'type': 'int unsigned',
                        'constraint': 'NOT NULL',
                        'comment': 'File byte size.'
                    },
                    {
                        'name': 'bytes',
                        'type': 'longblob',
                        'constraint': 'NOT NULL',
                        'comment': 'File bytes.'
                    }
                ],
                'primary': 'md5',
                'comment': 'File data table.'
            }

        ]

        ## View.
        views = [

            ### Data information.
            {
                'path': (self.db_names['file'], self.db_names['file.data_information']),
                'select': (
                    'SELECT `b`.`last_time`, `a`.`md5`, `a`.`size`, `b`.`names`, `b`.`notes`\n'
                    f'FROM `{self.db_names['file']}`.`{self.db_names['file.data']}` AS `a`\n'
                    'LEFT JOIN (\n'
                    '    SELECT\n'
                    '        `md5`,\n'
                    "        GROUP_CONCAT(DISTINCT(`name`) ORDER BY `create_time` DESC SEPARATOR ' | ') AS `names`,\n"
                    "        GROUP_CONCAT(DISTINCT(`note`) ORDER BY `create_time` DESC SEPARATOR ' | ') AS `notes`,\n"
                    '        MAX(`create_time`) as `last_time`\n'
                    f'    FROM `{self.db_names['file']}`.`{self.db_names['file.information']}`\n'
                    '    GROUP BY `md5`\n'
                    '    ORDER BY `last_time` DESC\n'
                    ') AS `b`\n'
                    'ON `a`.`md5` = `b`.`md5`\n'
                    'ORDER BY `last_time` DESC'
                )
            }

        ]

        ## View stats.
        views_stats = [

            ### 'stats'.
            {
                'path': (self.db_names['file'], self.db_names['file.stats']),
                'items': [
                    {
                        'name': 'count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['file']}`.`{self.db_names['file.information']}`'
                        ),
                        'comment': 'File information count.'
                    },
                    {
                        'name': 'past_day_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['file']}`.`{self.db_names['file.information']}`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) = 0'
                        ),
                        'comment': 'File information count in the past day.'
                    },
                    {
                        'name': 'past_week_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['file']}`.`{self.db_names['file.information']}`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 6'
                        ),
                        'comment': 'File information count in the past week.'
                    },
                    {
                        'name': 'past_month_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['file']}`.`{self.db_names['file.information']}`\n'
                            'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 29'
                        ),
                        'comment': 'File information count in the past month.'
                    },
                    {
                        'name': 'data_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db_names['file']}`.`{self.db_names['file.data']}`'
                        ),
                        'comment': 'File data unique count.'
                    },
                    {
                        'name': 'total_size',
                        'select': (
                            'SELECT FORMAT(SUM(`size`), 0)\n'
                            f'FROM `{self.db_names['file']}`.`{self.db_names['file.data']}`'
                        ),
                        'comment': 'File total byte size.'
                    },
                    {
                        'name': 'avg_size',
                        'select': (
                            'SELECT FORMAT(AVG(`size`), 0)\n'
                            f'FROM `{self.db_names['file']}`.`{self.db_names['file.data']}`'
                        ),
                        'comment': 'File average byte size.'
                    },
                    {
                        'name': 'max_size',
                        'select': (
                            'SELECT FORMAT(MAX(`size`), 0)\n'
                            f'FROM `{self.db_names['file']}`.`{self.db_names['file.data']}`'
                        ),
                        'comment': 'File maximum byte size.'
                    },
                    {
                        'name': 'last_time',
                        'select': (
                            'SELECT MAX(`create_time`)\n'
                            f'FROM `{self.db_names['file']}`.`{self.db_names['file.information']}`'
                        ),
                        'comment': 'File last record create time.'
                    }
                ]

            }

        ]

        # Build.
        self.database.build.build(databases, tables, views, views_stats)


    def upload(
        self,
        source: str | bytes,
        name: str | None = None,
        note: str | None = None
    ) -> int:
        """
        Upload file.

        Parameters
        ----------
        source : File path or file bytes.
        name : File name.
            - `None`: Automatic set.
                `parameter 'file' is 'str'`: Use path file name.
                `parameter 'file' is 'bytes'`: No name.
            - `str`: Use this name.
        note : File note.

        Returns
        -------
        File ID.
        """

        # Handle parameter.
        conn = self.database.connect()
        match source:

            ## File path.
            case str():
                file = File(source)
                file_bytes = file.bytes
                file_md5 = get_md5(file_bytes)
                file_name = file.name_suffix

            ## File bytes.
            case bytes() | bytearray():
                if type(source) == bytearray:
                    source = bytes(source)
                file_bytes = source
                file_md5 = get_md5(file_bytes)
                file_name = None

        ## File name.
        if name is not None:
            file_name = name

        ## File size.
        file_size = len(file_bytes)

        # Exist.
        exist = conn.execute_exist(
            (self.db_names['file'], self.db_names['file.data']),
            '`md5` = :file_md5',
            file_md5=file_md5
        )

        # Upload.

        ## Data.
        if not exist:
            data = {
                'md5': file_md5,
                'size': file_size,
                'bytes': file_bytes
            }
            conn.execute_insert(
                (self.db_names['file'], self.db_names['file.data']),
                data,
                'ignore'
            )

        ## Information.
        data = {
            'md5': file_md5,
            'name': file_name,
            'note': note
        }
        conn.execute_insert(
            (self.db_names['file'], self.db_names['file.information']),
            data
        )

        # Get ID.
        file_id = conn.variables['identity']

        # Commit.
        conn.commit()

        return file_id


    @overload
    def download(
        self,
        file_id: int,
        path: None = None
    ) -> bytes: ...

    @overload
    def download(
        self,
        file_id: int,
        path: str
    ) -> str: ...

    def download(
        self,
        file_id: int,
        path: str | None = None
    ) -> bytes | str:
        """
        Download file.

        Parameters
        ----------
        file_id : File ID.
        path : File save path.
            - `None`: Not save and return file bytes.
            - `str`: Save and return file path.
                `File path`: Use this file path.
                `Folder path`: Use this folder path and original name.

        Returns
        -------
        File bytes or file path.
        """

        # Generate SQL.
        sql = (
            'SELECT `name`, (\n'
            '    SELECT `bytes`\n'
            f'    FROM `{self.db_names['file']}`.`{self.db_names['file.data']}`\n'
            f'    WHERE `md5` = `{self.db_names['file.information']}`.`md5`\n'
            '    LIMIT 1\n'
            ') AS `bytes`\n'
            f'FROM `{self.db_names['file']}`.`{self.db_names['file.information']}`\n'
            'WHERE `file_id` = :file_id\n'
            'LIMIT 1'
        )

        # Execute SQL.
        result = self.database.execute(sql, file_id=file_id)

        # Check.
        if result.empty:
            text = "file ID '%s' not exist or no data" % file_id
            raise ValueError(text)
        file_name, file_bytes = result.first()

        # Not save.
        if path is None:
            return file_bytes

        # Save.
        else:
            folder = Folder(path)
            if folder:
                path = folder + file_name
            file = File(path)
            file(file_bytes)
            return file.path


    def query(
        self,
        file_id: int
    ) -> FileInfo:
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
            'SELECT `create_time`, `md5`, `name`, `note`, (\n'
            '    SELECT `size`\n'
            f'    FROM `{self.db_names['file']}`.`{self.db_names['file.data']}`\n'
            '    WHERE `md5` = `a`.`md5`\n'
            '    LIMIT 1\n'
            ') AS `size`\n'
            f'FROM `{self.db_names['file']}`.`{self.db_names['file.information']}` AS `a`\n'
            'WHERE `file_id` = :file_id\n'
            'LIMIT 1'
        )

        # Execute SQL.
        result = self.database.execute(sql, file_id=file_id)

        # Check.
        if result.empty:
            raise AssertionError('file ID does not exist')

        # Convert.
        table = result.to_table()
        info = table[0]

        return info
