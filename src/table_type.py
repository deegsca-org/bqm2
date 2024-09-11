from enum import Enum


class TableType(Enum):
    VIEW = 1
    TABLE = 2
    TABLE_EXTRACT = 3
    TABLE_GCS_LOAD = 4
    UNION_TABLE = 5
    UNION_VIEW = 6
    BASH_TABLE = 7
    EXTERNAL_TABLE = 8
    JOIN_TABLE = 9
    JOIN_VIEW = 10
