"""
Milestone 2 — Intelligent Preprocessing
Single-file implementation containing:
 - extract_repo(project_id, source_zip_path=None, github_url=None)
 - analyze_structure(repo_path)
 - detect_repo_type_and_stack(repo_path)
 - parse_dependencies(repo_path)
 - chunk_code_files(repo_path) (Python AST + simple JS/TS heuristics)
 - store_metadata(project_id, metadata)
 - FastAPI route `/projects/{project_id}/analyse`

Notes
 - This file is designed to be dropped into a FastAPI project.
 - DB persistence uses SQLAlchemy + PostgreSQL (JSONB). Adjust connection URL as needed.
 - Embeddings are left as a placeholder function `generate_embeddings` so you can plug your embedding provider (OpenAI, etc.).
"""

import os
import re
import json
import ast
import shutil
import logging
import tempfile
import zipfile
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# SQLAlchemy for metadata storage
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------
# Config - adjust to your env
# ------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/repo_intel")
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "/tmp/uploads")
SKIP_PATTERNS = {"node_modules", ".git", "__pycache__", "dist", "build"}

# Ensure uploads dir exists
Path(UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

# ------------------------
# Database helper (simple)
# ------------------------
engine = create_engine(DATABASE_URL)
metadata = MetaData()

project_files_table = Table(
    "project_files",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("project_id", Integer, nullable=False, index=True),
    Column("path", String, nullable=False),
    Column("file_type", String, nullable=False),
    Column("metadata", JSONB),
)

# Create table if not exists (simple convenience; in prod use migrations)
metadata.create_all(engine)

# ------------------------
# Utility functions
# ------------------------

def _is_skipped(path: Path) -> bool:
    for part in path.parts:
        if part in SKIP_PATTERNS:
            return True
    return False


def extract_repo(project_id: int, source_zip_path: Optional[str] = None, github_url: Optional[str] = None) -> str:
    """Extracts a zip file or clones a GitHub repository into UPLOADS_DIR/{project_id}

    Returns path to repo root.
    """
    dest_dir = Path(UPLOADS_DIR) / str(project_id)

    # Clean previous
    if dest_dir.exists():
        logger.info(f"Cleaning existing directory: {dest_dir}")
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    if source_zip_path:
        logger.info(f"Extracting zip {source_zip_path} to {dest_dir}")
        with zipfile.ZipFile(source_zip_path, 'r') as zf:
            zf.extractall(dest_dir)
        # If zip had a top-level folder, try to detect it as repo root
        candidates = [p for p in dest_dir.iterdir() if p.is_dir()]
        if len(candidates) == 1:
            return str(candidates[0])
        return str(dest_dir)

    if github_url:
        logger.info(f"Cloning {github_url} to {dest_dir}")
        try:
            subprocess.check_call(["git", "clone", "--depth", "1", github_url, str(dest_dir)])
            return str(dest_dir)
        except subprocess.CalledProcessError as e:
            logger.error(f"Git clone failed: {e}")
            raise

    raise ValueError("Either source_zip_path or github_url must be provided")


def analyze_structure(repo_path: str) -> Dict[str, Any]:
    """Walk repository and produce a JSON-friendly structure.

    Returns dict with: structure (list), important_files, skip_patterns
    """
    root = Path(repo_path)
    structure = []
    important_files = set()

    for p in root.rglob("*"):
        rel = p.relative_to(root).as_posix()
        if _is_skipped(p):
            continue
        node = {
            "path": rel,
            "is_dir": p.is_dir(),
            "size": p.stat().st_size if p.exists() and p.is_file() else None,
            "ext": p.suffix,
        }
        structure.append(node)

        # heuristics for important files
        name = p.name.lower()
        if name in {"package.json", "requirements.txt", "pyproject.toml", "setup.py", "pom.xml", "go.mod"}:
            important_files.add(rel)
        if rel in {"main.py", "app.py", "index.js", "server.js", "src/index.js"}:
            important_files.add(rel)

    # Guess repo type (simple): if package.json -> node, if .py files -> python, etc.
    repo_type = "unknown"
    exts = {Path(n['path']).suffix for n in structure if n.get('ext')}
    if '.py' in exts:
        repo_type = 'python'
    if '.js' in exts or '.ts' in exts:
        repo_type = 'javascript'
    if 'pom.xml' in {n['path'] for n in structure}:
        repo_type = 'java'

    return {
        "repo_type": repo_type,
        "structure": structure,
        "important_files": list(sorted(important_files)),
        "skip_patterns": list(sorted(SKIP_PATTERNS)),
    }


# ------------------------
# Dependency parsing
# ------------------------

def parse_dependencies(repo_path: str) -> Dict[str, Any]:
    root = Path(repo_path)
    deps = {"python": [], "node": [], "other": []}

    # Python
    req = root / 'requirements.txt'
    if req.exists():
        with open(req, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    deps['python'].append(line)

    pyproject = root / 'pyproject.toml'
    if pyproject.exists():
        try:
            import toml
            data = toml.load(pyproject)
            tool = data.get('tool', {})
            poetry = tool.get('poetry')
            if poetry:
                for name, v in poetry.get('dependencies', {}).items():
                    deps['python'].append(name)
        except Exception:
            logger.info('toml not available or failed to parse pyproject.toml')

    # Node
    pkg = root / 'package.json'
    if pkg.exists():
        with open(pkg, 'r', encoding='utf-8') as f:
            j = json.load(f)
            for group in ('dependencies', 'devDependencies', 'peerDependencies'):
                if group in j:
                    for name, ver in j[group].items():
                        deps['node'].append(f"{name}@{ver}")

    # Other heuristics (go.mod, pom.xml)
    if (root / 'go.mod').exists():
        with open(root / 'go.mod', 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith('//')]
            deps['other'].extend(lines[:50])

    if (root / 'pom.xml').exists():
        # naive: include filename; parsing pom properly needs xml parsing
        deps['other'].append('pom.xml')

    return deps


# ------------------------
# Chunking code into logical units
# ------------------------

def chunk_python_file(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, 'r', encoding='utf-8') as f:
        src = f.read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        logger.warning(f"Failed to parse python file: {file_path}")
        return []

    chunks = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = getattr(node, 'lineno', None)
            end = getattr(node, 'end_lineno', None)
            chunk_src = '\n'.join(src.splitlines()[start-1:end]) if start and end else None
            chunks.append({
                'name': getattr(node, 'name', '<lambda>'),
                'type': type(node).__name__,
                'start_line': start,
                'end_line': end,
                'source': chunk_src,
            })
    return chunks


def chunk_javascript_file(file_path: str) -> List[Dict[str, Any]]:
    # Very simple heuristic-based chunking for JS/TS: find top-level function and class definitions
    with open(file_path, 'r', encoding='utf-8') as f:
        src = f.read()
    pattern = re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(|^class\s+(\w+)\b", re.MULTILINE)
    chunks = []
    for m in pattern.finditer(src):
        name = m.group(1) or m.group(2)
        # find line numbers
        start_line = src.count('\n', 0, m.start()) + 1
        # naive end: next blank line or next pattern
        chunks.append({
            'name': name,
            'type': 'FunctionOrClass',
            'start_line': start_line,
            'end_line': None,
            'source': None,
        })
    return chunks


def chunk_all_files(repo_path: str) -> List[Dict[str, Any]]:
    root = Path(repo_path)
    all_chunks = []
    for p in root.rglob("*"):
        if p.is_file() and not _is_skipped(p):
            try:
                if p.suffix == '.py':
                    chunks = chunk_python_file(str(p))
                elif p.suffix in {'.js', '.ts'}:
                    chunks = chunk_javascript_file(str(p))
                else:
                    chunks = []
                for c in chunks:
                    c_meta = {
                        'file_path': str(p.relative_to(root)),
                        **c,
                    }
                    all_chunks.append(c_meta)
            except Exception as e:
                logger.exception(f"Failed to chunk file {p}: {e}")
    return all_chunks


# ------------------------
# Placeholder for embeddings
# ------------------------

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Placeholder: plug in your embedding generator here (OpenAI, HuggingFace, etc.)"""
    # returning empty vectors to keep signatures consistent
    return [[0.0] * 8 for _ in texts]


# ------------------------
# Persistence
# ------------------------

def store_metadata(project_id: int, metadata: Dict[str, Any]):
    """Basic persistence: write project metadata into the project_files table.

    The function writes one row per file for quick retrieval. In production, you'll want
    a more normalized schema and to store embeddings in a vector column (pgvector).
    """
    root_meta = metadata.get('structure', [])
    conn = engine.connect()
    trans = conn.begin()
    try:
        for node in root_meta:
            entry = {
                'project_id': project_id,
                'path': node['path'],
                'file_type': ('dir' if node['is_dir'] else node.get('ext', 'file')),
                'metadata': {
                    'size': node.get('size'),
                    'is_dir': node.get('is_dir'),
                }
            }
            conn.execute(project_files_table.insert().values(**entry))
        # store a special row for aggregated metadata
        conn.execute(project_files_table.insert().values(
            project_id=project_id,
            path='__metadata__.json',
            file_type='metadata',
            metadata={
                'analysis': metadata,
            }
        ))
        trans.commit()
        logger.info("Metadata stored to DB")
    except SQLAlchemyError as e:
        trans.rollback()
        logger.exception(f"DB error while storing metadata: {e}")
        raise
    finally:
        conn.close()


# ------------------------
# FastAPI route
# ------------------------

router = APIRouter()

class AnalyseRequest(BaseModel):
    project_id: int
    source_zip_path: Optional[str] = None
    github_url: Optional[str] = None


@router.post("/projects/{project_id}/analyse")
async def analyse_project(project_id: int, payload: AnalyseRequest):
    try:
        repo_path = extract_repo(project_id, source_zip_path=payload.source_zip_path, github_url=payload.github_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    structure = analyze_structure(repo_path)
    dependencies = parse_dependencies(repo_path)
    chunks = chunk_all_files(repo_path)

    metadata = {
        'structure': structure,
        'dependencies': dependencies,
        'chunks': chunks,
    }

    # Optionally: compute embeddings for chunk text for semantic search
    texts = [c.get('source') or '' for c in chunks if c.get('source')]
    if texts:
        embeddings = generate_embeddings(texts)
        # attach small sample of embedding to chunks (in prod store to vector column)
        for i, emb in enumerate(embeddings):
            chunks[i]['embedding_preview'] = emb[:8]

    # store metadata
    store_metadata(project_id, metadata)

    return {
        'status': 'success',
        'repo_path': repo_path,
        'metadata_summary': {
            'files_indexed': len(structure['structure']),
            'chunks_found': len(chunks),
            'dependencies': {k: len(v) for k, v in dependencies.items()},
        }
    }


# ------------------------
# Example manual run helper
# ------------------------
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-id', required=True, type=int)
    parser.add_argument('--zip', dest='zip', help='Local zip path')
    parser.add_argument('--git', dest='git', help='GitHub url')
    args = parser.parse_args()

    rp = extract_repo(args.project_id, source_zip_path=args.zip, github_url=args.git)
    s = analyze_structure(rp)
    d = parse_dependencies(rp)
    c = chunk_all_files(rp)
    print(json.dumps({'structure_count': len(s['structure']), 'deps': d, 'chunks': len(c)}, indent=2))
