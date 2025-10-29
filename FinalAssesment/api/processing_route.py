from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os

from services.extraction import extract_repo, analyze_structure
from services.dependencies import parse_dependencies
from services.chunking import chunk_all_files
from services.embeddings import generate_embeddings
from services.db import store_metadata


router = APIRouter()


# -----------------------------
# Request Model
# -----------------------------
class AnalyseRequest(BaseModel):
    project_id: int
    source_zip_path: Optional[str] = None
    github_url: Optional[str] = None


# -----------------------------
# Helper: Convert File Paths → Structure
# -----------------------------
def convert_file_paths_to_structure(file_paths: List[str]) -> List[Dict[str, Any]]:
    structure = []
    for path in file_paths:
        structure.append({
            "path": path,
            "is_dir": os.path.isdir(path),
            "size": os.path.getsize(path) if os.path.isfile(path) else None,
            "ext": os.path.splitext(path)[1] if os.path.isfile(path) else None,
        })
    return structure


# -----------------------------
# Route: Analyze Project
# -----------------------------
@router.post("/projects/{project_id}/analyse")
async def analyse_project(project_id: int, payload: AnalyseRequest):
    """
    Main analysis endpoint:
    1. Extracts repo (from zip or GitHub)
    2. Analyzes structure
    3. Parses dependencies
    4. Chunks source files
    5. Generates embeddings
    6. Stores metadata
    """
    try:
        # Step 1: Extract repository
        repo_path = extract_repo(project_id, payload.source_zip_path, payload.github_url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Repository extraction failed: {str(e)}")

    # Step 2: Analyze structure
    structure = analyze_structure(repo_path)
    if structure and isinstance(structure, list) and isinstance(structure[0], str):
        structure = convert_file_paths_to_structure(structure)

    # Step 3: Parse dependencies
    dependencies = parse_dependencies(repo_path)

    # Step 4: Chunk source files
    chunks = chunk_all_files(repo_path)

    # Step 5: Generate embeddings
    texts = [c.get("source") for c in chunks if c.get("source")]
    if texts:
        embeddings = generate_embeddings(texts)
        for i, emb in enumerate(embeddings):
            chunks[i]["embedding_preview"] = emb[:8]  # store first 8 dims as preview

    # Step 6: Store metadata
    metadata = {
        "structure": structure,
        "dependencies": dependencies,
        "chunks": chunks,
    }
    store_metadata(project_id, metadata)

    # Step 7: Return summary
    return {
        "status": "success",
        "metadata_summary": {
            "repo_path": repo_path,
            "files_indexed": len(structure),
            "chunks_found": len(chunks),
            "dependencies": {k: len(v) for k, v in dependencies.items()},
        },
    }
