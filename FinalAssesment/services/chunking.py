import ast
import re
import logging
from pathlib import Path
from services.extraction import is_skipped

logger = logging.getLogger(__name__)


def chunk_python_file(file_path: str):
    """Extract logical code chunks (functions, classes) from a Python file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            src = f.read()
    except Exception as e:
        logger.warning(f"Failed to read python file {file_path}: {e}")
        return []

    try:
        tree = ast.parse(src)
    except SyntaxError:
        logger.warning(f"Failed to parse python file: {file_path}")
        return []

    chunks = []
    lines = src.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = getattr(node, "lineno", None)
            end = getattr(node, "end_lineno", None)

            if start and end:
                chunk_src = "\n".join(lines[start - 1:end])
                chunks.append({
                    "name": getattr(node, "name", "<lambda>"),
                    "type": type(node).__name__,
                    "start_line": start,
                    "end_line": end,
                    "source": chunk_src
                })

    return chunks


def chunk_javascript_file(file_path: str):
    """Extract functions and classes from a JS/TS file using regex scanning."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            src = f.read()
    except Exception as e:
        logger.warning(f"Failed to read JS file {file_path}: {e}")
        return []

    # Match function or class definitions
    pattern = re.compile(
        r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(|class\s+(\w+)\b",
        re.MULTILINE
    )

    chunks = []
    for m in pattern.finditer(src):
        start_line = src.count("\n", 0, m.start()) + 1
        name = m.group(1) or m.group(2)
        chunks.append({
            "name": name,
            "type": "FunctionOrClass",
            "start_line": start_line,
            "end_line": None,
            "source": None
        })

    return chunks


def chunk_all_files(repo_path: str):
    """
    Walk through the repo and chunk all Python and JS/TS files.
    Returns a list of chunk metadata for downstream embedding or analysis.
    """
    root = Path(repo_path)
    all_chunks = []

    for p in root.rglob("*"):
        if p.is_file() and not is_skipped(p):
            try:
                chunks = []
                if p.suffix == ".py":
                    chunks = chunk_python_file(str(p))
                elif p.suffix in (".js", ".ts"):
                    chunks = chunk_javascript_file(str(p))

                for c in chunks:
                    c_meta = {
                        **c,
                        "file_path": str(p.relative_to(root))
                    }
                    all_chunks.append(c_meta)
            except Exception as e:
                logger.exception(f"Failed to chunk file {p}: {e}")

    return all_chunks
