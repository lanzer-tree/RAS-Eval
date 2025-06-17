from mcp.server.fastmcp import FastMCP
from src.toolkits.real.sql_toolkit.function.sql_toolkit import create_sql_database
from src.toolkits.real.sql_toolkit.function.sql_toolkit import insert_data
from src.toolkits.real.sql_toolkit.function.sql_toolkit import query_all_data
from src.toolkits.real.sql_toolkit.function.sql_toolkit import query_data
from src.toolkits.real.sql_toolkit.function.sql_toolkit import clear_sql_database
from src.toolkits.real.sql_toolkit.function.sql_toolkit import delete_data
import sqlite3


mcp = FastMCP('sql_toolkit')


@mcp.tool()
def _create_sql_database(db_path: str, keys: dict[str, str], primary_keys: list[str]=()) -> dict:
    """
    Create a sql database with the given name and keys.

    Args:
        db_path (str): The path to the database file. e.g. "data/database.db"
        keys (dict[str, str]): The keys  and their type to create in the database. e.g. {"id": "INTEGER", "name": "TEXT"}
        primary_keys (list[str]): The primary keys to create in the database. e.g. ["id"]

    Returns:
        dict: success status and description of whether the database was created or not.
    """
    return create_sql_database(db_path=db_path, keys=keys, primary_keys=primary_keys)


@mcp.tool()
def _insert_data(db_path: str, items: dict[str, str | float | int]) -> dict:
    """
    Insert a single data into a SQL database.

    Args:
        db_path (str): The path to the database file.
        items (dict[str, str | float | int]): The keys and values of data to insert into the database. e.g. {"id": 1, "name": "John"}

    Returns:
        dict:  success status and description.
    """
    return insert_data(db_path=db_path, items=items)


@mcp.tool()
def _query_all_data(db_path: str) -> list[dict[str, str | float | int]]:
    """
    Query all data from a SQL database.

    Args:
        db_path (str): The path to the database file.

    Returns:
        list[dict[str, str | float | int]]: A list of dictionaries containing the data from the database.
    """
    return query_all_data(db_path=db_path)


@mcp.tool()
def _query_data(db_path: str, key: str, value: str | float | int) -> list[dict[str, str | float | int]]:
    """
    Query data based on a specific key and value from a SQL database.

    Args:
        db_path (str): The path of the database file.
        key (str): The key to search for.
        value (str | float | int): The value to search for.

    Returns:
        list[dict[str, str | float | int]]: A list of tuples containing the data from the database.
    """
    return query_data(db_path=db_path, key=key, value=value)


@mcp.tool()
def _clear_sql_database(db_path: str) -> dict:
    """
    Clear all data from a SQL database.

    Args:
        db_path (str): The path to the database file.

    Returns:
        dict: success status and description.
    """
    return clear_sql_database(db_path=db_path)


@mcp.tool()
def _delete_data(db_path: str, condition: list[str]) -> dict:
    """
    Delete data from a SQL database based on given conditions.

    Args:
        db_path (str): The path to the database file.
        condition (list[str]): A list of conditions to delete data from the database. e.g. ["id = 1", "grade < 4"]
    """
    return delete_data(db_path=db_path, condition=condition)


if __name__ == '__main__':
    mcp.run('stdio')
