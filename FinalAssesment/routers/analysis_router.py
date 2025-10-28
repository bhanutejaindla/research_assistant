# routers/analysis_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database.db import get_db
from models.model import Project
from services.event_manager import EventManager
from services.repo_extractor import extract_repo
from services.preprocessing import preprocess_repository
import asyncio

router = APIRouter()
event_manager = EventManager()

@router.post("/projects/{project_id}/analyze")
async def start_analysis(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    asyncio.create_task(run_analysis_pipeline(project, db))
    return {"message": "Analysis started", "project_id": project_id}

@router.get("/projects/{project_id}/events")
async def stream_events(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    async def event_generator():
        try:
            async for event in event_manager.listen(project_id):
                if event == ":keepalive":
                    yield ": keepalive\n\n"
                else:
                    yield f"data: {event}\n\n"
        except asyncio.CancelledError:
            pass
        except Exception as e:
            yield f"data: Error - {str(e)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@router.get("/projects/{project_id}/poll")
async def poll_events(
    project_id: int,
    last_index: int = Query(0),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    new_events, new_index = await event_manager.get_events(project_id, last_index)
    return {"events": new_events, "last_index": new_index}

async def run_analysis_pipeline(project: Project, db: Session):
    project.status = "PROCESSING"
    db.commit()
    project_id = project.id

    await event_manager.send(project_id, "🚀 Analysis started")

    repo_path = await extract_repo(project, event_manager)
    metadata = await preprocess_repository(repo_path, event_manager, project_id)

    project.status = "COMPLETED"
    db.commit()
    await event_manager.send(project_id, f"✅ Preprocessing done. {metadata['total_files']} files analyzed.")
