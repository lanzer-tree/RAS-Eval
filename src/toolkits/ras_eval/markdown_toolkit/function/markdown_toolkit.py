import os

from markitdown import MarkItDown


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
    try:
        result = md.convert(file_path)
        content = result.text_content
    except Exception:
        content = _fallback_convert(file_path)
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
    with open(save_path, "w") as file:
        file.write(content)
    return {"success": True, "description": f"File {file_path} converted to markdown saved to {save_path}"}


def _fallback_convert(file_path: str) -> str:
    try:
        with open(file_path, "rb") as f:
            raw = f.read()
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("latin-1")
    except Exception:
        return f"*Unable to convert file: {file_path}*"

