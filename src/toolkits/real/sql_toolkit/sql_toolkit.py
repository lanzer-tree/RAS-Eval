from langchain_core.tools import tool
from mcp.server.fastmcp import FastMCP
import sqlite3


mcp = FastMCP('sql_toolkit')
def _connect_to_sql_database(db_path: str) -> tuple[sqlite3.Connection, sqlite3.Cursor, str]:
    """
    Connect to a SQLite database.

    Args:
        db_path (str): The path to the database file.

    Returns:
        sqlite3.Connection: The connection object to the database.
        sqlite3.Cursor: The cursor object to execute SQL queries.
        str: The name of the table name.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if '/' in db_path:
        db_path = db_path.split('/')[-1]
    table_name = db_path[:-3]
    return (conn, cursor, table_name)


def _disconnect_from_sql_database(conn: sqlite3.Connection, cursor: sqlite3.Cursor) -> None:
    """
    Disconnect from a SQLite database.

    Args:
        conn (sqlite3.Connection): The connection object to the database.
        cursor (sqlite3.Cursor): The cursor object to execute SQL queries.
    """
    conn.commit()
    cursor.close()
    conn.close()


def create_sql_database(db_path: str, keys: dict[str, str], primary_keys: list[str]=()) -> dict:
    """
    Create a sql database with the given name and keys.

    Args:
        db_path (str): The path to the database file. e.g. "data/database.db"
        keys (dict[str, str]): The keys  and their type to create in the database. e.g. {"id": "INTEGER", "name": "TEXT"}
        primary_keys (list[str]): The primary keys to create in the database. e.g. ["id"]

    Returns:
        dict: success status and description of whether the database was created or not.
    """
    try:
        conn, cursor, table_name = _connect_to_sql_database(db_path=db_path)
        command = f'CREATE TABLE IF NOT EXISTS {table_name} ('
        for key, value_type in keys.items():
            command += f'{key} {value_type}, '
        if len(primary_keys):
            command += f"PRIMARY KEY ({', '.join(tuple(primary_keys))})"
        if command[-2] == ',':
            command = command[:-2]
        command += ')'
        cursor.execute(command)
        _disconnect_from_sql_database(conn, cursor)
        return {'success': True, 'description': f'You created a database table with the name {table_name}'}
    except Exception as error:
        return {'success': False, 'description': f'Error: {error}'}


@tool(parse_docstring=True)
def langgraph_create_sql_database(db_path: str, keys: dict[str, str], primary_keys: list[str]=()) -> dict:
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
def mcp_create_sql_database(db_path: str, keys: dict[str, str], primary_keys: list[str]=()) -> dict:
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


def insert_data(db_path: str, items: dict[str, str | float | int]) -> dict:
    """
    Insert a single data into a SQL database.

    Args:
        db_path (str): The path to the database file.
        items (dict[str, str | float | int]): The keys and values of data to insert into the database. e.g. {"id": 1, "name": "John"}

    Returns:
        dict:  success status and description.
    """
    try:
        conn, cursor, table_name = _connect_to_sql_database(db_path)
        command = f'INSERT INTO {table_name} ('
        for key in items.keys():
            command += f'{key}, '
        if command[-2] == ',':
            command = command[:-2]
        command += ') VALUES ('
        for _ in range(len(items.keys())):
            command += f'?, '
        if command[-2] == ',':
            command = command[:-2]
        command += ')'
        cursor.executemany(command, [tuple(items.values())])
        _disconnect_from_sql_database(conn, cursor)
        return {'success': True, 'description': f'You inserted a data into the database table with the name {table_name}'}
    except Exception as error:
        return {'success': False, 'description': f'Error: {error}'}


@tool(parse_docstring=True)
def langgraph_insert_data(db_path: str, items: dict[str, str | float | int]) -> dict:
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
def mcp_insert_data(db_path: str, items: dict[str, str | float | int]) -> dict:
    """
    Insert a single data into a SQL database.

    Args:
        db_path (str): The path to the database file.
        items (dict[str, str | float | int]): The keys and values of data to insert into the database. e.g. {"id": 1, "name": "John"}

    Returns:
        dict:  success status and description.
    """
    return insert_data(db_path=db_path, items=items)


def query_all_data(db_path: str) -> list[dict[str, str | float | int]]:
    """
    Query all data from a SQL database.

    Args:
        db_path (str): The path to the database file.

    Returns:
        list[dict[str, str | float | int]]: A list of dictionaries containing the data from the database.
    """
    try:
        conn, cursor, table_name = _connect_to_sql_database(db_path)
        command = f'SELECT * FROM {table_name}'
        cursor.execute(command)
        data = cursor.fetchall()
        data = [dict(zip([column[0] for column in cursor.description], row)) for row in data]
        _disconnect_from_sql_database(conn, cursor)
        return data
    except Exception as error:
        return []


@tool(parse_docstring=True)
def langgraph_query_all_data(db_path: str) -> list[dict[str, str | float | int]]:
    """
    Query all data from a SQL database.

    Args:
        db_path (str): The path to the database file.

    Returns:
        list[dict[str, str | float | int]]: A list of dictionaries containing the data from the database.
    """
    return query_all_data(db_path=db_path)


@mcp.tool()
def mcp_query_all_data(db_path: str) -> list[dict[str, str | float | int]]:
    """
    Query all data from a SQL database.

    Args:
        db_path (str): The path to the database file.

    Returns:
        list[dict[str, str | float | int]]: A list of dictionaries containing the data from the database.
    """
    return query_all_data(db_path=db_path)


def query_data(db_path: str, key: str, value: str | float | int) -> list[dict[str, str | float | int]]:
    """
    Query data based on a specific key and value from a SQL database.

    Args:
        db_path (str): The path of the database file.
        key (str): The key to search for.
        value (str | float | int): The value to search for.

    Returns:
        list[dict[str, str | float | int]]: A list of tuples containing the data from the database.
    """
    try:
        conn, cursor, table_name = _connect_to_sql_database(db_path)
        if isinstance(value, str):
            command = f"SELECT * FROM {table_name} WHERE {key} = '{value}'"
        else:
            command = f'SELECT * FROM {table_name} WHERE {key} = {value}'
        cursor.execute(command)
        data = cursor.fetchall()
        data = [dict(zip([column[0] for column in cursor.description], row)) for row in data]
        _disconnect_from_sql_database(conn, cursor)
        return data
    except Exception as error:
        return []


@tool(parse_docstring=True)
def langgraph_query_data(db_path: str, key: str, value: str | float | int) -> list[dict[str, str | float | int]]:
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
def mcp_query_data(db_path: str, key: str, value: str | float | int) -> list[dict[str, str | float | int]]:
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


def clear_sql_database(db_path: str) -> dict:
    """
    Clear all data from a SQL database.

    Args:
        db_path (str): The path to the database file.

    Returns:
        dict: success status and description.
    """
    try:
        conn, cursor, table_name = _connect_to_sql_database(db_path)
        command = f'DELETE FROM {table_name}'
        cursor.execute(command)
        _disconnect_from_sql_database(conn, cursor)
        return {'success': True, 'description': f'You cleared the database table with the name {table_name}'}
    except Exception as error:
        return {'success': False, 'description': f'Error: {error}'}


@tool(parse_docstring=True)
def langgraph_clear_sql_database(db_path: str) -> dict:
    """
    Clear all data from a SQL database.

    Args:
        db_path (str): The path to the database file.

    Returns:
        dict: success status and description.
    """
    return clear_sql_database(db_path=db_path)


@mcp.tool()
def mcp_clear_sql_database(db_path: str) -> dict:
    """
    Clear all data from a SQL database.

    Args:
        db_path (str): The path to the database file.

    Returns:
        dict: success status and description.
    """
    return clear_sql_database(db_path=db_path)


def delete_data(db_path: str, condition: list[str]) -> dict:
    """
    Delete data from a SQL database based on given conditions.

    Args:
        db_path (str): The path to the database file.
        condition (list[str]): A list of conditions to delete data from the database. e.g. ["id = 1", "grade < 4"]
    """
    try:
        conn, cursor, table_name = _connect_to_sql_database(db_path)
        command = f"DELETE FROM {table_name} WHERE {' AND '.join(condition)};"
        cursor.execute(command)
        _disconnect_from_sql_database(conn, cursor)
        return {'success': True, 'description': f'You deleted data that {condition} from the database {table_name}'}
    except Exception as error:
        return {'success': False, 'description': f'Error: {error}'}


@tool(parse_docstring=True)
def langgraph_delete_data(db_path: str, condition: list[str]) -> dict:
    """
    Delete data from a SQL database based on given conditions.

    Args:
        db_path (str): The path to the database file.
        condition (list[str]): A list of conditions to delete data from the database. e.g. ["id = 1", "grade < 4"]
    """
    return delete_data(db_path=db_path, condition=condition)


@mcp.tool()
def mcp_delete_data(db_path: str, condition: list[str]) -> dict:
    """
    Delete data from a SQL database based on given conditions.

    Args:
        db_path (str): The path to the database file.
        condition (list[str]): A list of conditions to delete data from the database. e.g. ["id = 1", "grade < 4"]
    """
    return delete_data(db_path=db_path, condition=condition)


