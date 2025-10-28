# services/preprocessing.py
import os
import json
import ast
import asyncio
from typing import Dict, Any, List
from services.event_manager import EventManager

SKIP_DIRS = {".git", "node_modules", "__pycache__", "venv", ".idea", ".vscode"}

async def preprocess_repository(repo_path: str, event_manager: EventManager, project_id: int) -> Dict[str, Any]:
    """
    Intelligently preprocess repository structure and extract metadata.
    Detects entry points, dependencies, and code structure.
    """
    metadata = {
        "repo_type": None,
        "entry_points": [],
        "dependencies": [],
        "important_files": [],
        "code_chunks": [],
        "total_files": 0
    }

    await event_manager.send(project_id, "🔍 Starting intelligent preprocessing...")

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for file in files:
            file_path = os.path.join(root, file)
            metadata["total_files"] += 1

            # Detect repo type
            if not metadata["repo_type"]:
                if file == "package.json":
                    metadata["repo_type"] = "Node.js"
                elif file in ("requirements.txt", "pyproject.toml") or file.endswith(".py"):
                    metadata["repo_type"] = "Python"
                elif file.endswith(".java"):
                    metadata["repo_type"] = "Java"

            # Detect entry points
            if file.lower() in ("main.py", "app.py", "index.js"):
                metadata["entry_points"].append(file_path)
                await event_manager.send(project_id, f"⚙️ Entry point detected: {file}")

            # Detect dependency files
            if file in ("package.json", "requirements.txt", "pyproject.toml"):
                metadata["important_files"].append(file_path)
                deps = await parse_dependencies(file_path)
                metadata["dependencies"].extend(deps)
                await event_manager.send(project_id, f"📦 Dependencies loaded from {file}")

            # Code structure discovery (Python)
            if file.endswith(".py"):
                chunks = await extract_python_chunks(file_path)
                metadata["code_chunks"].extend(chunks)

    # Fallback type
    if not metadata["repo_type"]:
        metadata["repo_type"] = "Unknown"

    await event_manager.send(project_id, f"✅ Preprocessing complete ({metadata['total_files']} files analyzed)")

    # Save metadata asynchronously
    output_path = os.path.join(repo_path, "metadata.json")
    await asyncio.to_thread(save_metadata, output_path, metadata)
    await event_manager.send(project_id, f"🗂 Metadata saved to {output_path}")

    return metadata


async def parse_dependencies(file_path: str) -> List[str]:
    """Parse dependency files asynchronously."""
    try:
        if file_path.endswith("requirements.txt"):
            return await asyncio.to_thread(read_requirements, file_path)
        elif file_path.endswith("package.json"):
            return await asyncio.to_thread(read_package_json, file_path)
        else:
            return []
    except Exception as e:
        print(f"Error reading dependencies in {file_path}: {e}")
        return []


def read_requirements(file_path: str) -> List[str]:
    deps = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                deps.append(line)
    return deps


def read_package_json(file_path: str) -> List[str]:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)
    return list(data.get("dependencies", {}).keys())


async def extract_python_chunks(file_path: str) -> List[Dict[str, Any]]:
    """Extract Python function/class definitions with AST."""
    try:
        source = await asyncio.to_thread(read_limited, file_path, 20000)
        tree = ast.parse(source)
        chunks = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                chunks.append({
                    "type": "function" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "class",
                    "name": node.name,
                    "file": file_path,
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno)
                })
        return chunks
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []


def read_limited(file_path: str, limit: int) -> str:
    """Read up to `limit` characters safely."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read(limit)


def save_metadata(path: str, metadata: dict):
    """Write metadata JSON to disk safely."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
