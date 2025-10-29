from fastapi import FastAPI, UploadFile, File, Form, APIRouter
from fastapi.responses import JSONResponse
import os
import uuid

from agents.orchestration.work_flow import run_full_pipeline

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/run_pipeline")
async def run_pipeline_route(
    prompt: str = Form(...),
    file: UploadFile = File(None),
    github_url: str = Form(None),
    analysis_depth: str = Form("standard"),
    doc_verbosity: str = Form("normal"),
    enable_security: bool = Form(True),
    enable_diagram: bool = Form(True),
    web_augmented: bool = Form(True)
):
    """
    Run the main orchestration pipeline.
    Accepts either a ZIP file upload or a GitHub URL, plus configuration options.
    """

    # Handle file upload (optional)
    zip_path = None
    if file:
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        zip_path = os.path.join(UPLOAD_DIR, unique_filename)

        contents = await file.read()
        with open(zip_path, "wb") as f:
            f.write(contents)

    # Prepare pipeline configuration
    config = {
        "analysis_depth": analysis_depth,
        "doc_verbosity": doc_verbosity,
        "enable_security": enable_security,
        "enable_diagram": enable_diagram,
        "web_augmented": web_augmented,
    }

    # Initialize orchestration state
    state = {
        "prompt": prompt,
        "zip_path": zip_path,
        "github_url": github_url,
        "config": config,
        "agent_log": [],
    }

    # Run the full multi-agent pipeline
    try:
        final_state = run_full_pipeline(state)
        return JSONResponse({
            "result": final_state.get("final_output"),
            "agent_log": final_state.get("agent_log", [])
        })
    except Exception as e:
        return JSONResponse(
            {"error": str(e), "message": "Pipeline execution failed."},
            status_code=500
        )
