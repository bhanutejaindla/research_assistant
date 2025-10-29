from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
import tempfile
import zipfile
import asyncio

from api.job_state import job_status  # In-memory job tracking


router = APIRouter()


# -----------------------------
# GITHUB ANALYSIS (Simulated)
# -----------------------------
async def handle_github_analysis(job_id: str, github_url: str):
    try:
        # Step 1: Cloning
        job_status[job_id]["stage"] = "Cloning Repository"
        job_status[job_id]["feed"].append({"type": "milestone", "message": "Cloning repository..."})
        job_status[job_id]["percent"] = 10
        await asyncio.sleep(2)  # Simulate work

        # Step 2: Parsing Files
        job_status[job_id]["stage"] = "Parsing Files"
        job_status[job_id]["feed"].append({"type": "milestone", "message": "Parsing files..."})
        job_status[job_id]["percent"] = 30
        await asyncio.sleep(2)

        # Step 3: Analyzing
        job_status[job_id]["stage"] = "Analyzing"
        job_status[job_id]["feed"].append({"type": "milestone", "message": "Analyzing files for insights..."})
        job_status[job_id]["percent"] = 78
        await asyncio.sleep(3)

        # Step 4: Done
        job_status[job_id]["feed"].append({"type": "milestone", "message": "Analysis completed."})
        job_status[job_id]["stage"] = "Completed"
        job_status[job_id]["percent"] = 100

    except Exception as e:
        job_status[job_id]["stage"] = "Error"
        job_status[job_id]["error"] = str(e)
        job_status[job_id]["feed"].append({"type": "error", "message": f"GitHub analysis failed: {str(e)}"})
        job_status[job_id]["percent"] = 100


# -----------------------------
# ZIP FILE ANALYSIS (Simulated)
# -----------------------------
async def handle_zip_analysis(job_id: str, zip_path: str, project_dir: str):
    try:
        # Step 1: Extract Files
        job_status[job_id]["stage"] = "Extracting ZIP"
        job_status[job_id]["feed"].append({"type": "milestone", "message": "Extracting ZIP file..."})
        job_status[job_id]["percent"] = 10

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(project_dir)
        await asyncio.sleep(1)

        # Step 2: Simulate File Processing
        fake_files = ["file1.py", "file2.py", "file3.py"]
        for i, fname in enumerate(fake_files, start=1):
            job_status[job_id]["stage"] = f"Analyzing {fname}"
            job_status[job_id]["feed"].append({"type": "feed", "message": f"Processing {fname}..."})
            job_status[job_id]["percent"] = min(10 + i * 30, 95)
            job_status[job_id]["current_file"] = fname
            await asyncio.sleep(2)

        # Step 3: Done
        job_status[job_id]["percent"] = 100
        job_status[job_id]["current_file"] = None
        job_status[job_id]["stage"] = "Completed"
        job_status[job_id]["feed"].append({"type": "milestone", "message": "ZIP analysis completed."})

    except Exception as e:
        job_status[job_id]["stage"] = "Error"
        job_status[job_id]["error"] = str(e)
        job_status[job_id]["feed"].append({"type": "error", "message": f"Analysis failed: {str(e)}"})
        job_status[job_id]["percent"] = 100


# -----------------------------
# ROUTE: START ANALYSIS
# -----------------------------
@router.post("/real-time-analyze")
async def analyze_entrypoint(
    background_tasks: BackgroundTasks,
    github_url: str = Form(None),
    zip_file: UploadFile = File(None)
):
    """
    Starts a real-time background analysis job.
    Accepts either a GitHub URL or a ZIP file upload.
    """
    job_id = str(uuid.uuid4())
    job_status[job_id] = {
        "stage": "Queued",
        "feed": [{"type": "milestone", "message": "Analysis job created."}],
        "percent": 0,
        "current_file": None,
        "error": None
    }

    if github_url:
        background_tasks.add_task(handle_github_analysis, job_id, github_url)

    elif zip_file:
        project_dir = os.path.join(tempfile.gettempdir(), f"job_{job_id}")
        os.makedirs(project_dir, exist_ok=True)

        zip_path = os.path.join(project_dir, zip_file.filename)
        content = await zip_file.read()
        with open(zip_path, "wb") as out_file:
            out_file.write(content)

        background_tasks.add_task(handle_zip_analysis, job_id, zip_path, project_dir)

    else:
        raise HTTPException(status_code=400, detail="You must provide either a GitHub URL or a ZIP file.")

    return JSONResponse({
        "job_id": job_id,
        "message": "Analysis started. Poll /analyze/progress/{job_id} for updates."
    })
