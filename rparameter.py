# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2022-12-05 14:10:02
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Database parameter methods.
"""


from typing import Dict, Union, Optional, overload

from .rconnection import RDatabase, RDBConnection


__all__ = (
    "RDBParameter",
    "RDBPStatus",
    "RDBPVariable"
)


class RDBParameter(object):
    """
    Rey's `database parameters` type.
    """


    def __init__(
        self,
        rdatabase: Union[RDatabase, RDBConnection],
        global_: bool
    ) -> None:
        """
        Build `database parameters` instance.

        Parameters
        ----------
        rdatabase : RDatabase or RDBConnection instance.
        global_ : Whether base global.
        """

        # Set parameter.
        self.rdatabase = rdatabase
        self.global_ = global_


    def __getitem__(self, key: str) -> Optional[str]:
        """
        Get item of parameter dictionary.

        Parameters
        ----------
        key : Parameter key.

        Returns
        -------
        Parameter value.
        """

        # Get.
        value = self.get(key)

        return value


    def __setitem__(self, key: str, value: Union[str, float]) -> None:
        """
        Set item of parameter dictionary.

        Parameters
        ----------
        key : Parameter key.
        value : Parameter value.
        """

        # Set.
        params = {key: value}

        # Update.
        self.update(params)


class RDBPStatus(RDBParameter):
    """
    Rey's `database parameter status` type.
    """


    @overload
    def get(self, key: None = None) -> Dict[str, str]: ...

    @overload
    def get(self, key: str = None) -> Optional[str]: ...

    def get(self, key: Optional[str] = None) -> Union[Dict[str, str], Optional[str]]:
        """
        Get parameter.

        Parameters
        ----------
        key : Parameter key.
            - `None` : Return dictionary of all parameters.
            - `str` : Return value of parameter.

        Returns
        -------
        Status of database.
        """

        # Generate SQL.

        ## Global.
        if self.global_:
            sql = "SHOW GLOBAL STATUS"

        ## Not global.
        else:
            sql = "SHOW STATUS"

        # Execute SQL.

        ## Dictionary.
        if key is None:
            status = result.fetch_dict(val_field=1)

        ## Value.
        else:
            sql += " LIKE :key"
            result = self.rdatabase(sql, key=key)
            row = result.first()
            if row is None:
                status = None
            else:
                status = row["Value"]

        return status


    def update(self, params: Dict[str, Union[str, float]]) -> None:
        """
        Update parameter.

        Parameters
        ----------
        params : Update parameter key value pairs.
        """

        # Throw exception.
        raise AssertionError("database status not update")


class RDBPVariable(RDBParameter):
    """
    Rey's `database parameter variable` type.
    """


    @overload
    def get(self, key: None = None) -> Dict[str, str]: ...

    @overload
    def get(self, key: str = None) -> Optional[str]: ...

    def get(self, key: Optional[str] = None) -> Union[Dict[str, str], Optional[str]]:
        """
        Get parameter.

        Parameters
        ----------
        key : Parameter key.
            - `None` : Return dictionary of all parameters.
            - `str` : Return value of parameter.

        Returns
        -------
        Variables of database.
        """

        # Generate SQL.

        ## Global.
        if self.global_:
            sql = "SHOW GLOBAL VARIABLES"

        ## Not global.
        else:
            sql = "SHOW VARIABLES"

        # Execute SQL.

        ## Dictionary.
        if key is None:
            variables = result.fetch_dict(val_field=1)

        ## Value.
        else:
            sql += " LIKE :key"
            result = self.rdatabase(sql, key=key)
            row = result.first()
            if row is None:
                variables = None
            else:
                variables = row["Value"]

        return variables



    def update(self, params: Dict[str, Union[str, float]]) -> None:
        """
        Update parameter.

        Parameters
        ----------
        params : Update parameter key value pairs.
        """

        # Generate SQL.
        sql_set_list = [
            "%s = %s" % (
                key,
                (
                    value
                    if value.__class__ in (int, float)
                    else "'%s'" % value
                )
            )
            for key, value in params.items()
        ]
        sql_set = ",\n    ".join(sql_set_list)

        # Global.
        if self.global_:
            sql = f"SET GLOBAL {sql_set}"

        ## Not global.
        else:
            sql = f"SET {sql_set}"

        # Execute SQL.
        self.rdatabase(sql)