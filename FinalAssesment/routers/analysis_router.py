# routers/analysis_router.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database.db import get_db
from services.repo_extractor import extract_repo
from services.preprocessing import preprocess_repository
from services.llm_analyzer import analyze_repo_with_llm
from services.event_manager import EventManager
from models.model import Project
import asyncio

router = APIRouter()
event_manager = EventManager()


@router.post("/projects/{project_id}/analyze")
async def start_analysis(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Run the analysis asynchronously (background task)
    asyncio.create_task(run_analysis_pipeline(project, db))

    return {"message": "Analysis started", "project_id": project_id}


@router.get("/projects/{project_id}/events")
async def stream_events(project_id: int):
    async def event_generator():
        async for event in event_manager.listen(project_id):
            yield f"data: {event}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def run_analysis_pipeline(project: Project, db: Session):
    project.status = "PROCESSING"
    db.commit()
    project_id = project.id

    # Notify user
    await event_manager.send(project_id, "Analysis started")

    # Step 1: Extract repo or zip
    repo_path = await extract_repo(project, event_manager)

    # Step 2: Preprocess repository (detect files, stack, dependencies)
    metadata = await preprocess_repository(repo_path, event_manager)

    # Step 3: LLM-based semantic analysis
    insights = await analyze_repo_with_llm(repo_path, metadata, event_manager)

    project.status = "COMPLETED"
    db.commit()

    await event_manager.send(project_id, f"Analysis complete: {insights}")
