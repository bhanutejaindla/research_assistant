from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database.db import get_db
from models.model import Project
from services.repo_extractor import extract_repo
from services.preprocessing import preprocess_repository
from services.event_manager import EventManager
import asyncio

router = APIRouter()
event_manager = EventManager()

# ✅ Use BackgroundTasks OR create a new DB session in async task
@router.post("/projects/{project_id}/analyze")
async def start_analysis(
    project_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # use background_tasks (avoids sharing DB session across threads)
    background_tasks.add_task(run_analysis_pipeline, project_id)
    return {"message": "Analysis started", "project_id": project_id}


# ✅ Streaming endpoint for SSE
@router.get("/projects/{project_id}/events")
async def stream_events(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalar_one_or_none()
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
            # client disconnected
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
        },
    )


# ✅ Fixed background pipeline
async def run_analysis_pipeline(project_id: int):
    """
    Runs repository extraction + preprocessing asynchronously.
    Creates a new DB session to avoid threading issues.
    """
    from database.db import AsyncSessionLocal  # local import avoids circular dependency
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Project).filter(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            await event_manager.send(project_id, "❌ Project not found in background task.")
            return

        try:
            project.status = "PROCESSING"
            await db.commit()
            await event_manager.send(project_id, "🚀 Analysis started")

            # ✅ Pass project_id separately, not the whole object
            repo_path = await extract_repo(project, project_id)
            metadata = await preprocess_repository(repo_path, project_id)

            project.status = "COMPLETED"
            await db.commit()

            await event_manager.send(
                project_id,
                f"🎉 Preprocessing done! {metadata.get('total_files', 0)} files analyzed.",
            )

        except Exception as e:
            await event_manager.send(project_id, f"❌ Error during analysis: {e}")
            project.status = "FAILED"
            await db.commit()
