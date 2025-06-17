from langchain_core.tools import tool
from mcp.server.fastmcp import FastMCP
from markitdown import MarkItDown


mcp = FastMCP('markdown_toolkit')
def convert_file_to_markdown(file_path: str, save_path: str) -> dict:
    """
    Convert a file to markdown.

    Args:
        file_path (str): The path to the file.
        save_path (str): The path to save the markdown file.

    Returns:
        dict: success status and description.
    """
    md = MarkItDown(enable_plugins=False)
    result = md.convert(file_path)
    with open(save_path, 'w') as file:
        file.write(result.text_content)
    return {'success': True, 'description': f'File {file_path} converted to markdown saved to {save_path}'}


@tool(parse_docstring=True)
def langgraph_convert_file_to_markdown(file_path: str, save_path: str) -> dict:
    """
    Convert a file to markdown.

    Args:
        file_path (str): The path to the file.
        save_path (str): The path to save the markdown file.

    Returns:
        dict: success status and description.
    """
    return convert_file_to_markdown(file_path=file_path, save_path=save_path)


@mcp.tool()
def mcp_convert_file_to_markdown(file_path: str, save_path: str) -> dict:
    """
    Convert a file to markdown.

    Args:
        file_path (str): The path to the file.
        save_path (str): The path to save the markdown file.

    Returns:
        dict: success status and description.
    """
    return convert_file_to_markdown(file_path=file_path, save_path=save_path)


