# services/preprocessing.py
import os
import json
import ast
from typing import Dict, Any, List
from services.event_manager import EventManager

SKIP_DIRS = {".git", "node_modules", "__pycache__", "venv", ".idea", ".vscode"}

async def preprocess_repository(repo_path: str, event_manager: EventManager, project_id: int) -> Dict[str, Any]:
    """Analyze repository structure and extract metadata"""
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
                elif file in ["requirements.txt", "pyproject.toml"] or file.endswith(".py"):
                    metadata["repo_type"] = "Python"
                elif file.endswith(".java"):
                    metadata["repo_type"] = "Java"

            # Detect entry points
            if file.lower() in ["main.py", "app.py", "index.js"]:
                metadata["entry_points"].append(file_path)
                await event_manager.send(project_id, f"⚙️ Entry point detected: {file}")

            # Detect dependency files
            if file in ["package.json", "requirements.txt", "pyproject.toml"]:
                metadata["important_files"].append(file_path)
                deps = await parse_dependencies(file_path)
                metadata["dependencies"].extend(deps)
                await event_manager.send(project_id, f"📦 Dependencies parsed from {file}")

            # Code structure discovery
            if file.endswith(".py"):
                chunks = await extract_python_chunks(file_path)
                metadata["code_chunks"].extend(chunks)

    await event_manager.send(project_id, f"✅ Preprocessing complete — {metadata['total_files']} files analyzed")

    # Save metadata to JSON
    output_path = os.path.join(repo_path, "metadata.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    await event_manager.send(project_id, f"🗂 Metadata saved to {output_path}")

    return metadata

async def parse_dependencies(file_path: str) -> List[str]:
    deps = []
    try:
        if file_path.endswith("requirements.txt"):
            with open(file_path, "r") as f:
                deps = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        elif file_path.endswith("package.json"):
            with open(file_path, "r") as f:
                data = json.load(f)
                deps = list(data.get("dependencies", {}).keys())
    except Exception as e:
        print(f"Error reading dependencies in {file_path}: {e}")
    return deps

async def extract_python_chunks(file_path: str) -> List[Dict[str, Any]]:
    """Extract function and class structure from Python files"""
    chunks = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                chunks.append({
                    "type": "function",
                    "name": node.name,
                    "file": file_path,
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno)
                })
            elif isinstance(node, ast.ClassDef):
                chunks.append({
                    "type": "class",
                    "name": node.name,
                    "file": file_path,
                    "line_start": node.lineno,
                    "line_end": getattr(node, "end_lineno", node.lineno)
                })
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return chunks
