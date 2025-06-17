from mcp.server.fastmcp import FastMCP
from src.toolkits.real.excel_toolkit.function.excel_toolkit import excel_create_workbook
from src.toolkits.real.excel_toolkit.function.excel_toolkit import excel_add_sheet
from src.toolkits.real.excel_toolkit.function.excel_toolkit import excel_delete_sheet
from src.toolkits.real.excel_toolkit.function.excel_toolkit import excel_write_cell
from src.toolkits.real.excel_toolkit.function.excel_toolkit import excel_read_cell
from src.toolkits.real.excel_toolkit.function.excel_toolkit import excel_format_cell
from src.toolkits.real.excel_toolkit.function.excel_toolkit import excel_read_sheet
from src.toolkits.real.excel_toolkit.function.excel_toolkit import excel_list_sheets
import openpyxl
import os
from typing import Optional


mcp = FastMCP('excel_toolkit')


@mcp.tool()
def _excel_create_workbook(file_path: str) -> dict:
    """
    Create a new Excel workbook and save it to the specified file path.

    Args:
        file_path (str): The path to save the Excel workbook.

    Returns:
        dict: A dictionary containing the success status and message.
    """
    return excel_create_workbook(file_path=file_path)


@mcp.tool()
def _excel_add_sheet(file_path: str, sheet_name: str) -> dict:
    """
    Add a new sheet to an existing Excel workbook.

    Args:
        file_path (str): The path to the Excel workbook.
        sheet_name (str): The name of the new sheet.

    Returns:
        dict: A dictionary containing the success status and message.
    """
    return excel_add_sheet(file_path=file_path, sheet_name=sheet_name)


@mcp.tool()
def _excel_delete_sheet(file_path: str, sheet_name: str) -> dict:
    """
    Delete a sheet from an existing Excel workbook.

    Args:
        file_path (str): The path to the Excel workbook.
        sheet_name (str): The name of the sheet to delete.

    Returns:
        dict: A dictionary containing the success status and message.
    """
    return excel_delete_sheet(file_path=file_path, sheet_name=sheet_name)


@mcp.tool()
def _excel_write_cell(file_path: str, cell: str, value: str, sheet_name: Optional[str]='Sheet') -> dict:
    """
    Write a value to a specific cell in an existing Excel workbook.

    Args:
        file_path (str): The path to the Excel workbook.
        cell (str): The cell to write to (e.g., "A1").
        value (str): The value to write.
        sheet_name (str): The name of the sheet.

    Returns:
        dict: A dictionary containing the success status and message.
    """
    return excel_write_cell(file_path=file_path, cell=cell, value=value, sheet_name=sheet_name)


@mcp.tool()
def _excel_read_cell(file_path: str, cell: str, sheet_name: Optional[str]='Sheet') -> dict:
    """
    Read a value from a specific cell in an existing Excel workbook.

    Args:
        file_path (str): The path to the Excel workbook.
        cell (str): The cell to read from (e.g., "A1").
        sheet_name (str): The name of the sheet.

    Returns:
        dict: A dictionary containing the success status and the value read from the cell.
    """
    return excel_read_cell(file_path=file_path, cell=cell, sheet_name=sheet_name)


@mcp.tool()
def _excel_format_cell(file_path: str, cell: str, format: str, sheet_name: Optional[str]='Sheet') -> dict:
    """
    Format a cell in an existing Excel workbook.

    Args:
        file_path (str): The path to the Excel workbook.
        cell (str): The cell to format (e.g., "A1").
        format (str): The format to apply (e.g., "0.00").
        sheet_name (str): The name of the sheet.

    Returns:
        dict: A dictionary containing the success status and message.
    """
    return excel_format_cell(file_path=file_path, cell=cell, format=format, sheet_name=sheet_name)


@mcp.tool()
def _excel_read_sheet(file_path: str, sheet_name: Optional[str]='Sheet') -> dict:
    """
    Read the content of a specific sheet in an existing Excel workbook.

    Args:
        file_path (str): The path to the Excel workbook.
        sheet_name (str): The name of the sheet.

    Returns:
        dict: A dictionary containing the success status and the content of the sheet.
    """
    return excel_read_sheet(file_path=file_path, sheet_name=sheet_name)


@mcp.tool()
def _excel_list_sheets(file_path: str) -> dict:
    """
    List all sheets in an existing Excel workbook.

    Args:
        file_path (str): The path to the Excel workbook.

    Returns:
        dict: A dictionary containing the success status and the list of sheet names.
    """
    return excel_list_sheets(file_path=file_path)


if __name__ == '__main__':
    mcp.run('stdio')
