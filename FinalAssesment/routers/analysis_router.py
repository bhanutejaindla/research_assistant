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
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
event_manager = EventManager()


@router.post("/projects/{project_id}/analyze")
async def start_analysis(project_id: int, db: Session = Depends(get_db)):
    """Start analysis pipeline for a project"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            logger.error(f"Project {project_id} not found in database")
            raise HTTPException(status_code=404, detail=f"Project with id {project_id} not found")

        # Check if already processing
        if project.status == "PROCESSING":
            return {
                "message": "Analysis already in progress",
                "project_id": project_id,
                "status": project.status
            }

        # Run the analysis asynchronously (background task)
        asyncio.create_task(run_analysis_pipeline(project, db))

        return {
            "message": "Analysis started successfully",
            "project_id": project_id,
            "status": "PROCESSING"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start analysis: {str(e)}")


@router.get("/projects/{project_id}/events")
async def stream_events(project_id: int, db: Session = Depends(get_db)):
    """Stream real-time events for project analysis"""
    try:
        # Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            logger.error(f"Project {project_id} not found when trying to stream events")
            raise HTTPException(
                status_code=404,
                detail=f"Project with id {project_id} not found. Please create the project first."
            )
        
        logger.info(f"Starting event stream for project {project_id}")
        
        async def event_generator():
            try:
                # Send initial connection message
                yield f"data: {json.dumps({'type': 'connected', 'message': f'Connected to project {project_id}'})}\n\n"
                
                async for event in event_manager.listen(project_id):
                    if event == ":keepalive":
                        yield ": keepalive\n\n"
                    else:
                        # Ensure event is properly formatted
                        if isinstance(event, str):
                            yield f"data: {json.dumps({'type': 'message', 'message': event})}\n\n"
                        else:
                            yield f"data: {json.dumps(event)}\n\n"
                            
            except asyncio.CancelledError:
                logger.info(f"Client disconnected from project {project_id}")
                yield f"data: {json.dumps({'type': 'disconnected', 'message': 'Client disconnected'})}\n\n"
            except Exception as e:
                logger.error(f"Error in event stream for project {project_id}: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in stream_events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stream events: {str(e)}")


@router.get("/projects/{project_id}/status")
async def get_project_status(project_id: int, db: Session = Depends(get_db)):
    """Get current status of a project"""
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(
                status_code=404,
                detail=f"Project with id {project_id} not found"
            )
        
        return {
            "project_id": project.id,
            "status": project.status,
            "name": project.name,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get project status: {str(e)}")


async def run_analysis_pipeline(project: Project, db: Session):
    """Execute the full analysis pipeline"""
    project_id = project.id
    
    try:
        # Update status
        project.status = "PROCESSING"
        db.commit()
        db.refresh(project)
        
        logger.info(f"Starting analysis pipeline for project {project_id}")
        
        # Notify user
        await event_manager.send(project_id, "Analysis started - Extracting repository...")

        # Step 1: Extract repo or zip
        await event_manager.send(project_id, "Step 1/3: Extracting repository files...")
        repo_path = await extract_repo(project, event_manager)
        await event_manager.send(project_id, f"Repository extracted to: {repo_path}")

        # Step 2: Preprocess repository (detect files, stack, dependencies)
        await event_manager.send(project_id, "Step 2/3: Preprocessing repository structure...")
        metadata = await preprocess_repository(repo_path, event_manager)
        await event_manager.send(project_id, f"Preprocessing complete - Found {len(metadata.get('files', []))} files")

        # Step 3: LLM-based semantic analysis
        await event_manager.send(project_id, "Step 3/3: Running semantic analysis...")
        insights = await analyze_repo_with_llm(repo_path, metadata, event_manager)

        # Update project status
        project.status = "COMPLETED"
        db.commit()
        
        logger.info(f"Analysis pipeline completed for project {project_id}")
        await event_manager.send(project_id, f"Analysis complete: {insights}")
        
    except Exception as e:
        logger.error(f"Error in analysis pipeline for project {project_id}: {str(e)}")
        
        # Update project status to failed
        project.status = "FAILED"
        db.commit()
        
        # Notify user of failure
        await event_manager.send(project_id, f"Analysis failed: {str(e)}")
    
    finally:
        # Ensure database session is closed
        db.close()