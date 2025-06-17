from mcp.server.fastmcp import FastMCP
from src.toolkits.real.markdown_toolkit.function.markdown_toolkit import convert_file_to_markdown
from markitdown import MarkItDown


mcp = FastMCP('markdown_toolkit')


@mcp.tool()
def _convert_file_to_markdown(file_path: str, save_path: str) -> dict:
    """
    Convert a file to markdown.

    Args:
        file_path (str): The path to the file.
        save_path (str): The path to save the markdown file.

    Returns:
        dict: success status and description.
    """
    return convert_file_to_markdown(file_path=file_path, save_path=save_path)


if __name__ == '__main__':
    mcp.run('stdio')
