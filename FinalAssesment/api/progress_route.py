from fastapi import APIRouter, HTTPException
from api.job_state import job_status

router = APIRouter()


@router.get("/analyze/progress/{job_id}")
async def get_analysis_progress(job_id: str):
    """
    Poll the current progress of an ongoing analysis job.
    Returns stage, percent completion, feed updates, and errors if any.
    """
    status = job_status.get(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    return status
