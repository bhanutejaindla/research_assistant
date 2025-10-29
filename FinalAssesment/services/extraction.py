import os
import shutil
import zipfile
import subprocess
import logging
from pathlib import Path
from typing import Dict, Any, List

# Define patterns to skip
SKIP_PATTERNS = {"node_modules", ".git", "__pycache__", "dist", "build"}

# Uploads directory
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "/tmp/uploads")
Path(UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)


def _is_skipped(path: Path) -> bool:
    """Return True if path should be skipped."""
    for part in path.parts:
        if part in SKIP_PATTERNS:
            return True
    return False


def extract_repo(project_id: int, source_zip_path: str = None, github_url: str = None) -> str:
    """
    Extract a ZIP file or clone a GitHub repository to a local uploads directory.
    Returns the path to the extracted repository.
    """
    dest_dir = Path(UPLOADS_DIR) / str(project_id)

    # Clean up if directory exists
    if dest_dir.exists():
        logger.info(f"Cleaning existing directory: {dest_dir}")
        shutil.rmtree(dest_dir)

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Handle ZIP upload
    if source_zip_path:
        logger.info(f"Extracting ZIP {source_zip_path} to {dest_dir}")
        with zipfile.ZipFile(source_zip_path, "r") as zf:
            zf.extractall(dest_dir)

        # If the ZIP contains a single root folder, use it
        candidates = [p for p in dest_dir.iterdir() if p.is_dir()]
        if len(candidates) == 1:
            return str(candidates[0])
        return str(dest_dir)

    # Handle GitHub URL cloning
    if github_url:
        logger.info(f"Cloning {github_url} into {dest_dir}")
        try:
            subprocess.check_call(["git", "clone", "--depth", "1", github_url, str(dest_dir)])
            return str(dest_dir)
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e}")
            raise RuntimeError(f"Git clone failed: {e}")

    raise ValueError("Either source_zip_path or github_url must be provided.")


def analyze_structure(repo_path: str) -> Dict[str, Any]:
    """
    Analyze repository file structure, detect repo type, and list important files.
    """
    root = Path(repo_path)
    structure: List[Dict[str, Any]] = []
    important_files = set()

    for p in root.rglob("*"):
        if _is_skipped(p):
            continue

        rel = p.relative_to(root).as_posix()
        node = {
            "path": rel,
            "is_dir": p.is_dir(),
            "size": p.stat().st_size if p.exists() and p.is_file() else None,
            "ext": p.suffix,
        }
        structure.append(node)

        # Detect important files
        name = p.name.lower()
        if name in ("package.json", "requirements.txt", "pyproject.toml", "setup.py", "pom.xml", "go.mod"):
            important_files.add(rel)

        # Detect entry point files
        if name in ("main.py", "app.py", "index.js", "server.js", "src/index.js"):
            important_files.add(rel)

    # Determine repository type based on file extensions
    repo_type = "unknown"
    exts = {Path(n["path"]).suffix for n in structure if n.get("ext")}

    if ".py" in exts:
        repo_type = "python"
    elif ".js" in exts or ".ts" in exts:
        repo_type = "javascript"
    elif "pom.xml" in (n["path"] for n in structure):
        repo_type = "java"

    return {
        "repo_type": repo_type,
        "structure": structure,
        "important_files": sorted(list(important_files)),
        "skip_patterns": sorted(list(SKIP_PATTERNS)),
    }
